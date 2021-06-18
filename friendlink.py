import requests
from bs4 import BeautifulSoup
import csv
import time
import tldextract

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75'
}

# @pysnooper.snoop()
def check_friendlink(my_link):
    """
    友情链接检测工具，提取页面上非本域名链接并检测对方是否有反链
    返回域名及检测结果列表
    """
    ext = tldextract.extract(my_link)
    tld = ext.domain + '.' + ext.suffix

    def is_same(linka, linkb):
    # 解决友情链接尾部有时带 / 有时不带 / 导致的匹配失败问题
        if linka == linkb:
            return True
        else:
            if len(linka) > len(linkb):
                return (linka[:-1] == linkb)
            else:
                return (linka == linkb[:-1])

    def double_check(my_link, link):
        statu = {
            0 : '有反链',
            1 : '有主域反链',
            2 : '无反链'
        }
        statu_code = 3
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            chrome = p.chromium.launch(headless=True)
            page = chrome.new_page()
            if '.fang.com' in link:
                page.goto('https://www.fang.com')
                time.sleep(3)
            page.goto(link, timeout=5000)
            page.goto('view-source:%s' % page.url )
            soup = BeautifulSoup(page.inner_html('html'),'html.parser')
            all_link = [
                x.get('href').strip() 
                for x in soup.findAll('a') if x.get('href') is not None
            ]
            for link in all_link:
                if is_same(my_link, link):
                    statu_code = 0
                    break
                elif tld in link:
                    statu_code = 1
                    break
                else:
                    statu_code = 2
            chrome.close()
        return statu[statu_code]


    def is_link_regular(my_link, link):
        print('-- 检查 %s' % link)
        try:
            res = requests.get(link, headers=headers, timeout=10)
        except Exception:
            return double_check(link)
        else:
            soup = BeautifulSoup(
                res.content.decode(res.apparent_encoding, errors='ignore'),
                'html.parser'
            )
            all_link = [
                x.get('href').strip() 
                for x in soup.findAll('a') if x.get('href') is not None
            ]
            for link in all_link:
                if is_same(my_link, link):
                    return '有反链'
                elif tld in link:
                    return '有主域反链'
                else:
                    continue
            return double_check(link)

    def is_exclude(link):
        exclude_link = [
            'https://beian.miit.gov.cn',
            'http://szcert.ebs.org.cn',
            'http://si.trustutn.org',
            'http://www.beian.gov.cn'
        ]
        return (link in exclude_link)

    # 获取外部链接
    res = requests.get(my_link, headers=headers, timeout=5)
    soup = BeautifulSoup(res.content.decode(res.apparent_encoding, errors='ignore'), 'html.parser')
    external_link = []
    # external_link = [
    #     x['href'] for x in
    #     soup.find('span', string='友情链接').find_parent('div').findAll('a')
    # ]
    all_link = list(
        set([x.get('href') for x in soup.findAll('a') if x.get('href') is not None])
    )
    for link in all_link:
        if ('http' in link) and (tld not in link):
            if not is_exclude(link):
                external_link.append(link)
    print('--在 %s 检测到 %s 条友链' % (my_link, len(external_link)))
    
    # 逐个检测
    result = []
    for link in external_link:
        if tld in link:
            result.append([my_link, link, '站内链接'])
        else:
            result.append([my_link, link, is_link_regular(my_link, link)])
    return result

if __name__ == "__main__":
        try:
            links = [x.strip() for x in open('待检测网址.txt', 'r', encoding='utf-8')]
        except UnicodeDecodeError:
            links = [x.strip() for x in open('待检测网址.txt', 'r', encoding='gbk')]

        with open('友链检测结果.csv', 'a+', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['网址', '友链', '检查结果'])
            for l in links:
                try:
                    writer.writerows(check_friendlink(l))
                except:
                    continue
                time.sleep(3)

