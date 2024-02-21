import random
import time

from DrissionPage import ChromiumOptions
from DrissionPage import ChromiumPage
from DrissionPage.errors import ElementNotFoundError, NoRectError, ElementLostError

from config import read_config_file, Config
from utils import read_cookies, save_cookies


def get_tracks():
    """
    滑块滑动的横坐标数组
    :return:
    """
    tracks = []
    max_times = 4
    for i in range(max_times):
        tracks.append(random.randint(100, 150))
        if i != max_times - 1 and random.choice([True, False]):
            tracks.append(random.randint(-20, -10))

    return tracks


class DaMai:
    """
    大麦H5购票
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        options = ChromiumOptions()
        options.incognito(True)
        options.set_argument('--window-size', '640,960')
        options.set_pref(arg='profile.default_content_settings.popups', value='0')
        self.page = ChromiumPage(options)

        options.ignore_certificate_errors(True)
        options.mute(True)
        options.set_user_agent(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) '
                                          'AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.62 Mobile/15E148'
                                          ' Safari/604.1')
        options.no_imgs(True)

        self.login_url = ('https://passport.damai.cn/login?ru=https://m.damai.cn/shows/mine.html?spm=a2o71.home.top'
                          '.duserinfo')

    def check_login_state(self):
        """
        :return:
        """
        cookies = read_cookies(self.cfg.cookie_filepath)
        if cookies is None:
            return False
        self.page.set.cookies(cookies)

        self.page.listen.start('mtop.damai.cn/h5/mtop.damai.wireless.user.session.transform/1.0/')
        self.page.get('https://m.damai.cn/shows/mine.html?spm=a2o71.home.top.duserinfo')

        print('检测登录状态中...')
        res = self.page.listen.wait(timeout=5)
        try:
            data = res.response.body['data']
            nickname = data['nickname']
            user_id = data['userId']
            print(f"登录成功,\n\t用户ID: {nickname}\n\t用户昵称:{user_id}\n")
            return True
        except KeyError as _:
            pass
        except TypeError as _:
            pass

        return False

    def login(self):
        """
        登录
        :return:
        """
        self.page.cookies()
        self.page.get(self.login_url)
        self.page.ele('#fm-login-id').input(self.cfg.username)
        self.page.ele('#fm-login-password').input(self.cfg.password)
        self.page.ele('.fm-btn').click(timeout=2)

        self.page.listen.start('mtop.damai.cn/h5/mtop.damai.wireless.user.session.transform/1.0/')

        try:
            self.page.wait.url_change('https://passport.damai.cn/', exclude=True, timeout=10, raise_err=True)
        except TimeoutError:
            print('登录失败, 账号/密码错误/出现滑块验证!')
            return False

        res = self.page.listen.wait()
        nickname = res.response.body['data']['nickname']
        user_id = res.response.body['data']['userId']
        print(f"登录成功,\n\t用户ID: {nickname}\n\t用户昵称:{user_id}\n")
        cookies = self.page.cookies()
        save_cookies(data=cookies, filepath=self.cfg.cookie_filepath)

    def try_move_slider(self):
        """
        判断是否有滑块, 有则拖动滑块。
        :return:
        """
        ele = self.page.ele('#nc_1_n1z', timeout=0.2)
        if not ele or not ele.states.is_displayed:
            return

        offset_x = 0
        for x in get_tracks():
            offset_x += x
            try:
                self.page.actions.hold(ele).move(offset_x=offset_x, offset_y=0, duration=0.1).release()
            except NoRectError as e:
                break
            except ElementLostError as e:
                break

        is_refresh = True
        ele = self.page.ele('.nc_1_nocaptcha', timeout=0.2)
        if ele and ele.states.is_displayed:
            is_refresh = False
            try:
                ele.click()
            except NoRectError as _:
                pass

        if is_refresh:
            ele = self.page.ele('text=刷新页面', timeout=0.2)
            if ele and ele.states.is_displayed:
                ele.click(timeout=0.2)

    def buy(self):

        self.page.get(self.cfg.ticket_url)
        ele = self.page.ele('.known', timeout=0.1)
        if ele:
            ele.click()
        self.page.ele(f'text={self.cfg.ticket_site}').click()
        self.page.ele('.buy__button__text').click()
        self.page.ele(f'text^{self.cfg.ticket_date}').click()
        start = time.time()
        while not self.page.ele('text=确定', timeout=0.2):
            self.try_move_slider()
            try:
                self.page.ele(f'text^{self.cfg.ticket_date}', timeout=0.1).click()
            except ElementNotFoundError as _:
                ele = self.page.ele('text=刷新页面', timeout=0.2)
                if ele and ele.states.is_displayed:
                    print('刷新页面...')
                    ele.click(timeout=1)
            end = time.time()
            print('等待开抢中, 点击`{}`刷新页面, 耗时:{}毫秒'.format(self.cfg.ticket_date, int((end - start) * 1000)))
            start = end

        print(f'选择票档:{self.cfg.ticket_grade}')
        self.page.ele(f'text={self.cfg.ticket_grade}').click()

        print('点击确定...')
        self.page.ele('text=确定').click()

        for item in self.cfg.real_names:
            print(f'选中实名人:{item}')
            self.page.ele(f'text^{item}').click()

        print('点击提交订单...')
        self.page.ele('text=提交订单').click()

    def start(self):
        if not self.check_login_state():
            self.login()
        self.buy()


if __name__ == '__main__':
    conf = read_config_file('config.yml')
    app = DaMai(conf)
    app.start()
