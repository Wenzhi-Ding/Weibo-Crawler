import argparse
import requests
import json
from pathlib import Path
import os
from datetime import datetime
import time

import pandas as pd
# from py_reminder import monitor
import numpy as np
from lxml import etree


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'
}

COOKIES = {'SUB': '_2A25Pk2TfDeRhGeFI41MY9ivFyz6IHXVs6dEXrDV8PUNbmtAfLW3CkW9NfMwjopB5-A1wUaHGaw3Cz6N3uJOZZQuN'}

PATH = 'posts'


def parse_args():
    now = datetime.now()
    parser = argparse.ArgumentParser(description='批量抓取微博数据。')
    parser.add_argument('-n', '--nickname', type=str, 
                        help='如果指定该项，则首先根据用户昵称查询用户。')
    parser.add_argument('-u', '--uid', type=str, nargs='*',
                        help='如果指定该项，则根据用户的UID抓取微博。')
    parser.add_argument('-e', '--end', type=str, default=now.year * 100 + now.month,
                        help='结束抓取的月份。格式为yyyymm。如未指定，默认为当前月份。')
    parser.add_argument('-s', '--start', type=str, default=200910,
                        help='开始抓取的月份。格式为yyyymm。如未指定，默认为2009年10月。')

    args = parser.parse_args()
    
    return args


def get_api(api, wait=3):
    r = requests.get(api, headers=HEADERS, cookies=COOKIES)
    time.sleep(np.random.randint(wait, wait + 5))
    if r.status_code in [200, 304]:
        return r
    else:
        raise ValueError('API未能成功访问。')


def query_month(uid, year, month):
    page = 1
    data_path = f'{PATH}/{uid}/{year}/{month}'
    while True:
        print(f'正在获取{uid}用户{year}年{month}月第{page}页……')
        
        api = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0&displayYear={year}&curMonth={month}&stat_date={year * 100 + month}'
        r = get_api(api)
        res = json.loads(r.content.decode())['data']
        if len(res['list']) == 0:
            print(f'完成获取{uid}用户{year}年{month}月数据。')
            break
        
        Path(data_path).mkdir(parents=True, exist_ok=True)
        for post in res['list']:
            with open(f"{data_path}/{post['mid']}.json", 'w+') as f:
                json.dump(post, f)
        
        page += 1
        
        
def query_nickname(name):
    api = f'https://s.weibo.com/user/&nickname={name}'
    r = get_api(api)
    
    selector = etree.HTML(r.content)
    cards = selector.xpath('//*[@id="pl_user_feedList"]/div')
    uids = []
    for x in cards:
        nickname = x.xpath('div[2]/div/a')[0].text
        uid = x.xpath('div[3]/button')[0].get('uid')
        l = len(x.xpath('div[2]/p'))
        intro = x.xpath('div[2]/p')[0].text if l == 2 else ''
        follower = x.xpath('div[2]/p/span')[0].text
        
        uids.append((nickname, uid, intro, follower))
    
    df = pd.DataFrame(uids, columns=['昵称', 'UID', '简介', '粉丝量'])
    df['update_time'] = int(datetime.now().timestamp())
    if os.path.isfile('uids.csv'):
        df.to_csv('uids.csv', mode='a', index=False, header=False)
    else:
        df.to_csv('uids.csv', mode='a', index=False)
        
    return uids


def query_history(uid):
    url = f'https://weibo.com/ajax/profile/mbloghistory?uid={uid}'
    r = get_api(url)
    
    yms = []

    res = json.loads(r.content.decode())['data']
    for y in res:
        for m in res[y]:
            yms.append(int(y) * 100 + int(m))
            
    return yms


def init_session(args):
    todo = args.uid
    if args.nickname:
        uids = query_nickname(args.nickname)
        print(pd.DataFrame(uids, columns=['昵称', 'UID', '简介', '粉丝量']))
        select = input("如果查询以上所有用户，请输入A。否则，请输入用户对应的序号（多个用户序号以空格分割）：")
        if select == 'A':
            todo = [int(x[1]) for x in uids]
        else:
            todo = [int(uids[int(x)][1]) for x in select.split()]
        
    if len(todo) == 0:
        print('结束程序，再见！')
        return

    for uid in todo:
        yms = [x for x in query_history(uid) if int(args.start) <= x <= int(args.end)]
        yms.sort(reverse=True)
        
        if len(yms) == 0:
            print(f'{uid}用户没有位于{args.start}和{args.end}之间的微博。')
        else:
            print(f'开始获取{uid}用户在{min(yms)}和{max(yms)}之间的微博……')
        
        for ym in yms:
            cur_year, cur_month = divmod(ym, 100)
            query_month(uid, cur_year, cur_month)


if __name__ == '__main__':
    args = parse_args()
    init_session(args)