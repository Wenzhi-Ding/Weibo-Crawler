import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from multiprocessing import Queue

from util.util import parse_config, connect_db
from util.search import get_query_periods, get_keywords


if __name__ == "__main__":
    cfg = parse_config()
    keywords = get_keywords() if cfg['keywords'] else []

    con = connect_db()
    print('数据库读取连接创建成功')

    task_queue = Queue()
    get_query_periods(cfg['start_time'], cfg['end_time'], con, task_queue, keywords)