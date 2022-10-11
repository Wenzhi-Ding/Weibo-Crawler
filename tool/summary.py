import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from datetime import datetime, timedelta

from util.util import connect_db


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


if __name__ == '__main__':
    print(format_summary())