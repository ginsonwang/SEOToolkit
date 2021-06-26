#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
采集百度、360、搜狗下拉框关键词脚本
"""

# TODO 改为异步访问各浏览器，提升关键词采集效率
from playwright.sync_api import sync_playwright
import time


def get_sugs(word):
    se_config = [
        ['https://m.baidu.com', 'input[id="index-kw"]', '.suggest-content', '#index-bn', '.c-slink-new-strong'],
        ['https://m.sogou.com', 'input[id="keyword"]', '.suggestion', 'input[class="qbtn"]', 'a'],
        ['https://m.so.com', 'input[id="q"]', '.suggest-content', 'button[class="search-btn"]', 'a']
    ]
    sugs = []
    with sync_playwright() as p:
        chrome = p.chromium.launch()
        page = chrome.new_page()
        for i in se_config:
            page.goto(i[0])
            # 获取下拉框关键词
            for a in 'abcdefghijklmnopqrstuvwxyz':
                page.fill(i[1], word + a)
                time.sleep(1)
                sugs += page.inner_text(i[2]).split('\n')
            # 获取相关搜索
            page.fill(i[1], word)
            time.sleep(1)
            page.click(i[3])
            time.sleep(3)
            if 'baidu' in i[0]:
                for a in page.query_selector_all(i[4]):
                    sugs.append(a.inner_text())
            else:
                for a in page.query_selector_all(i[4]):
                    href = a.get_attribute('href')
                    if ('/s?q=%' in href) or ('?keyword=' in href):
                        sugs.append(a.inner_text())
        chrome.close()
    return list(set(sugs))


if __name__ == '__main__':
    print('-- 开始采集')
    f = open('SE推荐关键词.txt', 'a+', encoding='utf-8')

    try:
        seeds = [x.strip() for x in open('种子词.txt', 'r', encoding='utf-8')]
    except UnicodeDecodeError:
        seeds = [x.strip() for x in open('种子词.txt', 'r', encoding='gbk')]

    for seed in seeds:
        for i in get_sugs(seed):
            f.write('%s,%s\n' % (seed, i))
            f.flush()
