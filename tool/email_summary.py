from py_reminder import monitor
from summary import summary


@monitor('微博爬虫运行摘要')
def email(*args, **kwargs):
    return None


if __name__ == '__main__':
    email(summary())