import utils
import sqlite3

keyword = "华海药业"
start = "2010-01-01-0"
end = "2020-01-01-0"
cont = 1

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

while cont:  # 一次循环中只要有一个period查到了新数据，就继续查询一轮
    cont = 0
    periods = utils.get_query_periods(keyword, start, end, con)
    for kw, st, et in periods:
        print(f"正在获取 {kw} 从 {st} 到 {et} 的数据")
        cont += utils.search_period(kw, st, et, con)
        
