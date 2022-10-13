import time
from datetime import datetime, timedelta

from util.util import connect_db, monitor, log_print

def utc_to_bj(utc_time):
    return (datetime.strptime(utc_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

def summary():
    con = connect_db()
    cur = con.cursor()
    abstract_time = cur.execute("SELECT MAX(abstract_at) FROM posts").fetchone()[0]
    abstract_time = utc_to_bj(abstract_time) if abstract_time else 'N/A'

    data_time = cur.execute("SELECT MAX(data_at) FROM posts").fetchone()[0]
    data_time = utc_to_bj(data_time) if data_time else 'N/A'

    dct = {
        '微博条数': cur.execute("SELECT COUNT(*) FROM posts").fetchone()[0],
        '有摘要微博': cur.execute("SELECT COUNT(*) FROM posts WHERE content IS NOT NULL").fetchone()[0],
        '最近一次抓取摘要': abstract_time,
        '有JSON微博': cur.execute("SELECT COUNT(*) FROM posts WHERE data IS NOT NULL").fetchone()[0],
        '最近一次抓取JSON': data_time,
    }
    return dct


def format_summary():
    dct = summary()
    return '\n'.join([f'{k}: {v}' for k, v in dct.items()])


def email_summary(monitor=0, interval=240):
    if monitor: 
        log_print(f"摘要邮件进程启动，报告间隔为 {interval} 分钟（{interval / 60:.1f} 小时）")
        while True:
            time.sleep(interval * 60)
            email(summary())


@monitor('微博爬虫运行摘要', mute_success=False)
def email(*args, **kwargs):
    log_print("邮件摘要已发送")
    return None
