from multiprocessing import Process, Queue

from util.util import log_print, write_sqlite, parse_config, connect_db
from util.search import get_query_periods, search_periods, get_keywords
from util.content import get_post_contents
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
        if cfg['get_search']:
            task_queue = Queue()
            print("搜索任务队列初始化成功")
            get_query_periods(cfg['start_time'], cfg['end_time'], con, task_queue, keywords)

            if cfg['multi_process']:
                search = Process(target=search_periods, args=(task_queue, write_queue, con, cfg['start_time'], cfg['end_time'], keywords))
                search.start()
                search.join()
            else:
                search_periods(task_queue, write_queue, con, cfg['start_time'], cfg['end_time'], keywords)

        if cfg['get_content']:
            if cfg['multi_process']:
                content = Process(target=get_post_contents, args=(con, write_queue, keywords))
                content.start()
                content.join()
            else:
                get_post_contents(con, write_queue, keywords)
    except KeyboardInterrupt:
        email.terminate()
        write.terminate()
        log_print("任务被中止，退出程序")
    else:
        email.terminate()
        write.terminate()
        log_print("任务结束，退出程序")
