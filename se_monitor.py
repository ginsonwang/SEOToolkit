import time
from playwright.sync_api import sync_playwright

def se_monitor():
    print('# SE 搜索结果页产品动态监控')
    se = {
        'baidu_pc': 'https://www.baidu.com/s?wd=',
        'baidu_m': 'https://m.baidu.com/s?wd=',
        'sogou_pc': 'https://www.sogou.com/web?query=',
        'sogou_m': 'https://wap.sogou.com/web/searchList.jsp?keyword=',
        '360_pc': 'https://www.so.com/s?q=',
        '360_m': 'https://m.so.com/s?q=',
        'sm': 'https://m.sm.cn/s?q='
    }

    keywords = [
        '深圳买房', '深圳房价', '卓弘星辰', '卓弘星辰房价', '卓弘星辰怎么样', '卓弘星辰实景'
    ]
    for k in keywords:
        for sn, su in se.items():
            fn = '%s_%s_%s.jpg' % (sn, k, time.strftime('%Y%m%d'))
            with sync_playwright() as p:
                if 'sogou' in sn:
                    chrome = p.chromium.launch(headless=False)
                else:
                    chrome = p.chromium.launch()
                page = chrome.new_page()
                if '_m' in sn:
                    page.set_viewport_size({'width': 750, 'height': 1920})
                page.goto(su + k)
                page.screenshot(full_page=True, path=fn, type='jpeg', quality=50)
                chrome.close()
            print('截图成功 ' + fn)
            time.sleep(int(time.strftime('%S'))%3 + 3)
