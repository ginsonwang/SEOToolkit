from playwright.sync_api import sync_playwright
import time
import csv
import requests
from random import randint

def get_proxy():
    targetUrl = "http://piping.mogumiao.com/proxy/api/get_ip_bs?appKey=dac19f0332de458387ba0bc1f1df6295&count=10&expiryDate=0&format=1&newLine=2"
    rsp = requests.get(targetUrl).json()
    proxy = rsp['msg'][0]['ip'] + ':' + rsp['msg'][0]['port']
    return proxy


def tt_rank(keywords):
    with sync_playwright() as p:
        chrome = p.chromium.launch(
            headless=False,
            # proxy={"server": "per-context"}
        )
        context = chrome.new_context()
        page = context.new_page()

        def get_rank(page):
            rank = []
            result_list = page.query_selector('.s-result-list')
            for div in result_list.query_selector_all('.result-content'):
                rank_num = div.get_attribute('data-i')
                if rank_num is None:
                    continue
                else:
                    title = div.query_selector(
                        '.text-ellipsis.text-underline-hover'
                        )
                    if title is None:
                        continue
                    else:
                        title = title.inner_text()
                    detail = div.query_selector(
                        '.cs-view.cs-view-flex.align-items-center.flex-row.cs-source-content'
                        )
                    if detail is None:
                        continue
                    else:
                        detail = detail.inner_text().replace('\n', ',')
                    rank.append([rank_num, title, detail])
            return rank
        
        def scroll(page):
            # 将页面向下滚动数次
            for _ in range(1, randint(4, 5)):
                page.press('body', 'PageDown')
                time.sleep(0.3)
            # 将页面向上滚动数次
            for _ in range(1, randint(3, 4)):
                page.press('body', 'PageUp')
                time.sleep(0.3)

        rank_file = open(
            '头条关键词查询结果_%s.csv' % time.strftime('%Y%m%d'),
            'a+', encoding='utf-8-sig', newline='')
        writer = csv.writer(rank_file)

        
        page.goto('https://so.toutiao.com')
        time.sleep(randint(3, 5))
        for k in keywords:
            page.fill('div[role="search"] [aria-label="搜索"]', k)
            time.sleep(randint(1, 2))
            with page.expect_popup() as popup_info:
                page.click('div[role="search"] button')
                time.sleep(randint(2, 4))
            page2 = popup_info.value
            scroll(page2)
            for line in get_rank(page2):
                writer.writerow([k] + line)
            page2.close()

        chrome.close()
        rank_file.close()


def bd_rank(keywords, size=10):
    # 构建浏览器环境
    with sync_playwright() as p:
        chrome = p.chromium.launch()
        context = chrome.new_context()
        page = context.new_page()

        # 定义排名解析函数
        def get_rank(page):
            rank = []
            # rank_type = {
            #     'news-realtime': '相关新闻',
            #     'se_com_default': '自然排名',
            #     'short_video_pc': '相关视频'
            # }

            for div in page.query_selector_all('.new-pmd.c-container'):
                if div.get_attribute('tpl') is not None:
                    if div.get_attribute('tpl') == 'se_com_default':
                        title = div.query_selector('.t').inner_text().strip()
                        rank_num = div.get_attribute('id')
                        _from = div.query_selector('.c-showurl').inner_text().strip()
                    elif div.get_attribute('tpl') == 'short_video_pc':
                        title = div.query_selector('.c-title').inner_text().strip()
                        _from = ''
                        rank_num = div.get_attribute('id')
                    print(','.join([title, rank_num, _from]))
                    rank.append([title, rank_num, _from])
            return rank

        # 准备存储
        rank_file = open(
            '百度关键词查询结果_%s.csv' % time.strftime('%Y%m%d'),
            'a+', encoding='utf-8-sig', newline='')
        writer = csv.writer(rank_file)

        # 访问百度
        page.goto('https:www.baidu.com')
        time.sleep(2)

        # 开始采集关键词排名
        for k in keywords:
            page.fill('#kw', k)
            time.sleep(1)
            page.click('#su')
            time.sleep(randint(3, 5))
            writer.writerows(get_rank(page))
            for _ in range(1, size//10 + 1):
                page.click('#page .n')
                time.sleep(randint(2, 3))
                writer.writerows(get_rank(page))
        rank_file.close()
        page.close()
        context.close()
        chrome.close()




if __name__ == "__main__":
    keywords = ['深圳新房']
    # keywords = [
    #     x.strip() for x in open(
    #         'C:\\Users\\admin\\Desktop\\头条排名查询关键词.txt',
    #         'r', encoding='utf-8')
    #     ]
    # tt_rank(keywords)
    bd_rank(keywords)
