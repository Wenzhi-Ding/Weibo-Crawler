import utils
import sqlite3
from multiprocessing import Process, Queue
import os

START = "2010-01-01-0"
END = "2020-01-01-0"

con = sqlite3.connect(os.path.dirname(__file__) + '/../weibo.db')
print('数据库读取连接创建成功')

if __name__ == "__main__":

    task_queue = Queue()
    write_queue = Queue()
    print("队列初始化成功")

    utils.get_query_periods(START, END, con, task_queue)
    writer = Process(target=utils.write_sqlite, args=(write_queue,))
    worker1 = Process(target=utils.search_period, args=(task_queue, write_queue, con, START, END,))


    writer.start()
    worker1.start()

    worker1.join()

    writer.terminate()
