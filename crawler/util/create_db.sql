-- posts：记录每条微博的MID、作者的UID及数据爬取状态
CREATE TABLE IF NOT EXISTS posts (
    mid INTEGER PRIMARY KEY NOT NULL,
    uid INTEGER,
    -- status INTEGER DEFAULT 0,
    data JSON,
    update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- users：记录每个用户的UID及数据爬取状态
-- CREATE TABLE IF NOT EXISTS users (
--     uid INTEGER PRIMARY KEY NOT NULL,
--     status INTEGER DEFAULT 0,
--     update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS user_profile (
--     id INTEGER PRIMARY KEY NOT NULL,
--     uid INTEGER NOT NULL,
--     name TEXT NOT NULL,
--     update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
-- );

-- keyword_queries：记录检索关键词及完成进度
CREATE TABLE IF NOT EXISTS keyword_queries (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    start_time TIMESTAMP,
    min_time TIMESTAMP,
    end_time TIMESTAMP,
    update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- search_results：记录检索结果
CREATE TABLE IF NOT EXISTS search_results (
    keyword TEXT NOT NULL,
    mid INTEGER NOT NULL,
    update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (keyword, mid)
);