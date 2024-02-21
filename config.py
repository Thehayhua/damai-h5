import yaml


class Config:
    def __init__(self, data):
        self.username = data.get('username', None)
        self.password = data.get('password', None)
        self.ticket_url = data.get('ticket_url', None)
        self.ticket_site = data.get('ticket_site', None)
        self.ticket_date = data.get('ticket_date', None)
        self.ticket_grade = data.get('ticket_grade', None)
        self.ticket_num = data.get('ticket_num', 1)
        self.real_names = data.get('real_names', [])
        self.cookie_filepath = data.get('cookie_filepath', 'cookies.json')

        if not self.username or not self.password \
                or not self.ticket_url or not self.ticket_site \
                or not self.ticket_date or not self.ticket_grade:
            raise ValueError('账号/密码/门票URL/门票站点/门票日期/票档存在空值, 请检测配置文件!')

        if self.ticket_num != len(self.real_names):
            raise ValueError('购票数量与实名人数量不一致!')


def read_config_file(file_path):
    try:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return Config(config_data)
    except FileNotFoundError as e:
        raise ValueError("未找到配置文件: config.yml")
