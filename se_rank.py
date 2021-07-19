from playwright.sync_api import sync_playwright
import time
import csv
import requests

def get_proxy():
    targetUrl = "http://piping.mogumiao.com/proxy/api/get_ip_bs?appKey=dac19f0332de458387ba0bc1f1df6295&count=10&expiryDate=0&format=1&newLine=2"
    rsp = requests.get(targetUrl).json()
    proxy = rsp['msg'][0]['ip'] + ':' + rsp['msg'][0]['port']
    return proxy


def tt_se_rank(keywords):
    with sync_playwright() as p:
        chrome = p.chromium.launch(
            headless=False,
            # proxy={"server": "per-context"}
        )

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
                    rank.append([k, rank_num, title, detail])
            return rank

        rank_file = open(
            '头条关键词查询结果_%s.csv' % time.strftime('%Y%m%d%H%M%S'),
            'a+', encoding='utf-8-sig', newline='')
        writer = csv.writer(rank_file)

        for k in keywords:
            context = chrome.new_context(
                # proxy={"server": get_proxy()}
            )
            page = context.new_page()
            for i in range(0, 1):
                try:
                    page.goto(
                        'https://so.toutiao.com/search?dvpf=pc&source=sug&keyword=%s&page_num=%s&pd=synthesis&source=pagination'
                        % (k, i)
                    )
                    time.sleep(int(time.strftime('%S'))%2 + 7)
                    for line in get_rank(page):
                        writer.writerow(line)
                except Exception:
                    continue
            page.close()
            context.close()

        chrome.close()
        rank_file.close()

if __name__ == "__main__":
    keywords = [
        x.strip() for x in open(
            'C:\\Users\\admin\\Desktop\\头条排名查询关键词.txt',
            'r', encoding='utf-8')
        ]
    tt_se_rank(keywords)
