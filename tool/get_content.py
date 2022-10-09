import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from multiprocessing import Process, Queue

from util.util import write_sqlite, log_print, parse_config, connect_db
from util.content import get_post_contents

cfg = parse_config()

con = connect_db()
print('数据库读取连接创建成功')

if __name__ == "__main__":

    task_queue = Queue()
    write_queue = Queue()
    print("队列初始化成功")

    write = Process(target=write_sqlite, args=(write_queue,))
    write.start()

    if cfg['multi_process']:
        content = Process(target=get_post_contents, args=(con, write_queue, []))
        content.start()
        content.join()
    else:
        get_post_contents(con, write_queue, [])
    
    write.terminate()
    log_print("任务执行完毕，退出程序")