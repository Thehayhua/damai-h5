import json


def read_cookies(filepath):
    """
    读取cookies
    :param filepath:
    :return:
    """
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return None


def save_cookies(data, filepath):
    """
    保存cookies
    :param data:
    :param filepath:
    :return:
    """
    with open(filepath, 'w') as file:
        json.dump(data, file)

