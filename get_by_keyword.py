import utils
import sqlite3

keyword = "华海药业"
start = "2010-01-01-0"
end = "2020-01-01-0"
cont = True

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

while True:
    periods = utils.get_query_periods(keyword, start, end, con)
    for st, et in periods:
        print(f"正在获取 {keyword} 从 {st} 到 {et} 的数据")
        utils.search_period(keyword, st, et, con)
