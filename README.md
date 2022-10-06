# Weibo Search Crawler

本爬虫用于从微博搜索中爬取尽可能完整的结果。

输入文件：
- `add_keywords.txt`：需要输入给数据库的待查关键词。一行一组。
- `cookies.txt`：微博登陆后，取出COOKIES中SUB字段的值放入其中。一行一个COOKIE，需要以`SUB NAME`的形式存。NAME用于标识区分各个COOKIE。
- `expired_cookies.txt`：请先手动创建空的该文件，用于存放被程序识别为过期的COOKIE。

代码：
- `add_keywords.py`：将`add_keywords.txt`增加至数据库。
- `get_all_keywords.py`: 以多进程爬取所有未完成查询的关键词。
- `get_by_keyword.py`：用于指定关键词查询。
- `get_no_data_mid.py`：抓取尚未下载数据的微博。
- `refresh_search_progress.py`：以实际数据更新已查询的范围。应当在运行`get_no_data_mid.py`后才运行该脚本。
- `utils.py`：所有函数。

数据库结构：
- weibo.db
    - posts：博文及数据
    - keywords：关键词及搜索已覆盖范围
    - search_results：关键词及对应的博文结果