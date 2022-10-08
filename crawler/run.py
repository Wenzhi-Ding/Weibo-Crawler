import sqlite3
from multiprocessing import Process, Queue

from util.util import write_sqlite, DB, parse_config
from util.search import get_query_periods, search_periods, get_keywords
from util.content import get_post_contents

cfg = parse_config()
keywords = get_keywords() if cfg['keywords'] else []

con = sqlite3.connect(DB)
print('数据库读取连接创建成功')

if __name__ == "__main__":

    task_queue = Queue()
    write_queue = Queue()
    print("队列初始化成功")

    write = Process(target=write_sqlite, args=(write_queue,))
    write.start()

    if cfg['get_search']:
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
    
    write.terminate()
