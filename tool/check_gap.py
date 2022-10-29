import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from multiprocessing import Process, Queue

from util.util import log_print, write_sqlite, parse_config, connect_db
from util.search import search_periods, get_keywords, get_gap_periods
from util.summary import email_summary


def main():
    cfg = parse_config()
    keywords = get_keywords() if cfg['keywords'] else []

    con = connect_db()
    print('数据库读取连接创建成功')

    write_queue = Queue()
    print("数据库写入队列初始化成功")

    email = Process(target=email_summary, args=(cfg['monitor'], cfg['interval'],))
    email.start()
    write = Process(target=write_sqlite, args=(write_queue,))
    write.start()

    try:
        task_queue = Queue()
        print("搜索任务队列初始化成功")
        get_gap_periods(task_queue, con)

        search_periods(task_queue, write_queue, con, cfg['start_time'], cfg['end_time'], keywords, check_gap=True)

    except KeyboardInterrupt:
        email.terminate()
        write.terminate()
        log_print("任务被中止，退出程序")
    else:
        email.terminate()
        write.terminate()
        log_print("任务结束，退出程序")

if __name__ == '__main__':
    main()