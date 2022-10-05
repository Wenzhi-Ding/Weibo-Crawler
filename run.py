import utils
import sqlite3

keyword = "华海药业"
start = "2010-01-01-0"
end = "2020-01-01-0"

con = sqlite3.connect('/home/wenzhi/Weibo-Search-Crawler/weibo.db')

for page in range(1, 51):
    print(f'keyword={keyword} start={start} end={end} page={page}')

    # 获取搜索页
    data = utils.get_search_page(keyword=keyword, start=start, end=end, page=page)
    utils.dump_posts(data, con)

    # 获取搜索结果的详细数据
    mids = [mid for mid, uid in data]
    for mid in mids:
        print(mid)
        json = utils.get_post_json(mid)
        utils.dump_post_content((mid, json), con)

    # 记录搜索结果
    sr_data = [(keyword, mid) for mid, uid in data]
    utils.dump_search_results(sr_data, con)

    # 更新搜索进度
    utils.update_keyword_progress(keyword, mids, con)