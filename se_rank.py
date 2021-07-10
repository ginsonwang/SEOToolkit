from playwright.sync_api import sync_playwright
import time
import csv


def tt_se_rank(keywords):
    with sync_playwright() as p:
        chrome = p.chromium.launch(headless=False)
        page = chrome.new_page()
        page.goto(
            'https://so.toutiao.com/search?dvpf=pc&source=input&keyword=买房&page_num=0&pd=synthesis'
            )
        time.sleep(int(time.strftime('%S'))%2 + 3)

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
            for i in range(0, 5):
                page.goto(
                    'https://so.toutiao.com/search?dvpf=pc&source=sug&keyword=%s&page_num=%s&pd=synthesis&source=pagination'
                    % (k, i))
                time.sleep(int(time.strftime('%S'))%2 + 3)
                for line in get_rank(page):
                    writer.writerows(line)

        page.close()
        chrome.close()
        rank_file.close()

if __name__ == "__main__":
    keywords = [
        x.strip() for x in open(
            'C:\\Users\\admin\\Desktop\\头条排名查询关键词.txt',
            'r', encoding='utf-8')
        ]
    tt_se_rank(keywords)
