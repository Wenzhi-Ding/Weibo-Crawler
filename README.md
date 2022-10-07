# Weibo Crawler

微博爬虫。以SQLite形式存储数据，支持多进程、随机Cookie、随机代理等功能。爬虫包含以下模块：
- User：用户页面的完整爬取（已完成）
- Search：基于关键词及时间区间的爬取（施工中）
- Content：爬取某条微薄的具体数据（施工中）
- Repost：爬取某条微博的所有转发
- Comment：爬取某条微博的所有评论
- Topic：爬取话题或超话内的微博
- Trending：记录热搜榜