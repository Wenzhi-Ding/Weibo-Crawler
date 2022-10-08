# Weibo Crawler

微博爬虫。以SQLite形式存储数据，支持多进程、随机Cookie、随机代理等功能。爬虫包含以下模块：
- User：用户页面的完整爬取（已完成，未整合）
- Search：基于关键词及时间区间的爬取（已完成）
- Content：爬取某条微博的具体数据（已完成）
- Repost：爬取某条微博的所有转发
- Comment：爬取某条微博的所有评论
- Topic：爬取话题或超话内的微博
- Trending：记录热搜榜

## 使用

若首次运行该爬虫或希望重置项目（清空数据库、日志、过期 Cookies 等），请先运行
```bash
python crawler/init.py
```

此后每次使用，用户只需编辑 `crawler.ini` 后，再运行
```bash
python crawler/run.py
```

由于微博内容爬取绝大多数不需要使用Cookie，因此建议单独运行用户和搜索等爬虫，得到微博ID后，批量将微博ID分配至多台设备并行爬取。以此实现最少Cookie、最高效率。

## 依赖

本爬虫完全以 Python 原生库完成，额外依赖仅 SQLite 3 一项。一般而言，Python 已经自带了对 SQLite 3 的支持。若提示找不到 SQLite 3，可以参考[该网页](https://www.runoob.com/sqlite/sqlite-installation.html)安装。