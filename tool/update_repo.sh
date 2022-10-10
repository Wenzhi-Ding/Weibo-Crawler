cd ..
mv Weibo-Crawler Weibo-Crawler_bak
git clone https://github.com/Wenzhi-Ding/Weibo-Crawler.git
cp Weibo-Crawler_bak/*.txt Weibo-Crawler
cp Weibo-Crawler_bak/*.ini Weibo-Crawler
cp Weibo-Crawler_bak/*.db Weibo-Crawler
cp -r Weibo-Crawler_bak/log Weibo-Crawler
cd Weibo-Crawler
