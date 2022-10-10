import csv
from multiprocessing import Queue
import sqlite3
from typing import List
import requests
import time
import traceback
from datetime import datetime, timedelta
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import logging
import os
import configparser
import re

from .third_party.base62 import encode, decode
# from error_catcher import silent

ROOT = os.path.dirname(__file__) + '/..'
DB = ROOT + '/weibo.db'
COOKIES = ROOT + '/cookies.txt'
CONFIG = ROOT + '/settings.ini'
KEYWORDS = ROOT + '/keywords.txt'

LOG = ROOT + '/log'
EXPIRED_COOKIES = LOG + '/expired_cookies.txt'
ERROR_LOG = LOG + '/error.log'
PROGRESS_LOG = LOG + '/progress.log'

BREAK = ROOT + '/break'
MERGE = ROOT + '/merge'
OUTPUT = ROOT + '/output'

CREATE_DB = os.path.dirname(__file__) + '/create_db.sql'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'
}


def connect_db():
    if os.path.isfile(DB):
        con = sqlite3.connect(DB)
        return con
    init_project()
    sys.exit("数据库不存在，已重新初始化项目")


def parse_config():
    config = configparser.ConfigParser()
    config.read(CONFIG)
    cfg = {}
    for i in config:
        for j in config[i]:
            val = config[i][j]
            if val.isdigit(): val = int(val)
            cfg[j] = val
    return cfg


def decode_mid(mid: str):
    '''4021924038830731 <- E9cllB3h9'''
    mid = mid.swapcase()
    a, b, c = mid[0], mid[1:5], mid[5:]
    return str(decode(a)) + str(decode(b)).zfill(7) + str(decode(c)).zfill(7)


def encode_mid(mid: str):
    '''4021924038830731 -> E9cllB3h9'''
    a, b, c = mid[:2], mid[2:9], mid[9:]
    return (encode(int(a)) + encode(int(b)).zfill(4) + encode(int(c)).zfill(4)).swapcase()


def query_time_to_timestamp(query_time, shift={}):
    if not isinstance(query_time, datetime):
        query_time = datetime.strptime(query_time, '%Y-%m-%d-%H')
    if shift:
        timestamp += timedelta(**shift)
    return query_time.strftime('%Y-%m-%d %H:%M:%S')


def timestamp_to_query_time(timestamp, shift={}):
    if not isinstance(timestamp, datetime):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    if shift:
        timestamp += timedelta(**shift)
    return timestamp.strftime('%Y-%m-%d-%H')


cfg = parse_config()

# @silent(key_vars=['api', 'sub', 'name'], log_file=ERROR_LOG)
def get_api(api: str, wait=cfg['wait'], check_cookie=False):
    sub = get_random_cookie()
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    r = session.get(api, headers=HEADERS, cookies={'SUB': sub}, timeout=10)

    time.sleep(wait)
    if r.status_code in [200, 304]:
        r = r.content.decode()
        if check_cookie and "$CONFIG[\'watermark\']" not in r:
            log_print(f"该 Cookie 可能过期：{sub}")
            add_expired_cookie(sub)
        return r
    # raise ValueError('API未能成功访问。')
    log_print(f'API 未能成功访问；{api}')


def log_print(s: str):
    logging.basicConfig(filename=PROGRESS_LOG, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print(s)
    logging.getLogger(sys._getframe(1).f_code.co_name).info(s)


def get_expired_cookies():
    with open(EXPIRED_COOKIES, 'r') as f:
        cookies = f.readlines()
    cookies = [x.strip() for x in cookies]
    return cookies


def add_expired_cookie(sub):
    with open(EXPIRED_COOKIES, 'a') as f:
        f.write(f'{sub}\n')


# @silent(key_vars=[], log_file=ERROR_LOG)
def get_random_cookie():
    with open(COOKIES, 'r') as f:
        cookies = f.readlines()
    cookies = [re.findall(r'(?<=SUB=).+?(?=;)', x) for x in cookies]
    cookies = [x[0] for x in cookies if x]
    cookies = [sub for sub in cookies if sub not in get_expired_cookies()]
    if not cookies:
        # send_email(task="没有可用COOKIE")
        log_print("没有可用 Cookie")
        raise Exception("没有可用 Cookie")
    return random.choice(cookies)


# @silent(key_vars=['script'], log_file=ERROR_LOG)
def write_sqlite(write_queue: Queue):
    write_con = sqlite3.connect('weibo.db')
    log_print('数据库写入连接创建成功')
    cur = write_con.cursor()
    while True:
        try:
            script, data = write_queue.get()
            cur.executemany(script, data)
            write_con.commit()
        except:
            log_print(traceback.format_exc())


def init_project():
    for p in [LOG, MERGE]:
        if not os.path.exists(p):
            os.mkdir(p)

    if os.path.isfile(DB):
        rm = input('数据库已存在，是否删除？(y/n)：')
        if rm.lower() == 'y': 
            rm = input('再次确认是否删除？(y/n)：')
            if rm.lower() == 'y': 
                new_DB = DB[:-3] + datetime.now().strftime('-%Y-%m-%d-%H-%M-%S.bak')
                os.rename(DB, new_DB)
                print(f"原数据库已备份至 {new_DB}")
        
    if not os.path.isfile(DB):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        with open(CREATE_DB, 'r') as f:
            cur.executescript(f.read())

    if os.path.isfile(ERROR_LOG) or os.path.isfile(PROGRESS_LOG):
        rm = input('是否重置所有日志？(y/n)：')
        for file in [ERROR_LOG, PROGRESS_LOG]:
            if rm.lower() == 'y' and os.path.isfile(file): os.remove(file)

    for file in [COOKIES, EXPIRED_COOKIES, KEYWORDS]:
        if not os.path.isfile(file):
            with open(file, 'w') as f:
                f.write('')

    log_print("已完成初始化，请检查 settings.ini 配置文件、keywords.txt 搜索关键词文件及 cookies.txt 登录凭证文件。")


def write_csv(table: str, cur: sqlite3.Connection.cursor, header: List[str]):
    if not os.path.exists(OUTPUT): os.mkdir(OUTPUT)
    path = f'{OUTPUT}/{table}.csv'
    with open(path, 'w+') as c:
        writer = csv.writer(c)
        writer.writerow(header)
        writer.writerows(cur)
