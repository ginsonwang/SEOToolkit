from playwright.sync_api import sync_playwright
from playwright._impl._api_types import TimeoutError
import time
import csv
from random import randint

SE_CONF = {
    'baidu_pc': {
        'index': 'https://www.baidu.com',
        'device': 'pc',
        'need_scroll': False,
        'selectors': {
            'input_kw': '#kw',
            'search': '#su',
            'turn_page': 'text=下一页 >',
            'rank_list': '#content_left',
            'rank_item': '.new-pmd.c-container',
            'title': 'h3'
        }
    },
    'baidu_h5': {
        'index': 'https://m.baidu.com',
        'device': 'mobile',
        'need_scroll': False,
        'selectors': {
            'input_kw': 'input[name="word"]',
            'search': '.se-bn',
            'turn_page': '',
            'rank_list': 'div#results.results',
            'rank_item': '.c-result.result',
            'title': '.c-title'
        }
    }
}


# TODO 增加切换代理 IP 功能，提升查询效率

# TODO 排名查询函数进一步抽象化，一个函数支持不同浏览器
class Ranker(object):
    def __init__(self, se='baidu_pc', headless=False) -> None:
        super().__init__()
        self.set_se(se)
        self.headless = headless

    def set_se(self, se):
        if se not in SE_CONF.keys():
            raise ValueError('Unsupported search engine')
        self.se = se
        self.conf = SE_CONF[se]
        self.selectors = self.conf['selectors']

    def scroll(self, page):
        # 将页面向下滚动数次
        for _ in range(1, randint(4, 5)):
            page.press('body', 'PageDown')
            time.sleep(0.3)
        # 将页面向上滚动数次
        for _ in range(1, randint(3, 4)):
            page.press('body', 'PageUp')
            time.sleep(0.3)

    def is_nature(self, element):
        if 'baidu' in self.se:
            # 没有 tpl 属性，是付费排名
            if element.get_attribute('tpl') is None:
                return False
            # tpl 属性值为 recommend_list, 是相关搜索
            elif element.get_attribute('tpl') == 'recommend_list':
                return False
        return True

    def parser_rank(self, page, order):
        ranks = []
        # 获取排名列表
        rank_list = page.query_selector(self.selectors['rank_list'])
        # 逐个解析排名项
        for i in rank_list.query_selector_all(self.selectors['rank_item']):
            # 判断是否正常排名，不是则跳过
            if not self.is_nature(i):
                continue
            # 基于结果数定义排名位置
            order += 1
            # 获取排名标题
            title = i.query_selector(
                self.selectors['title']).inner_text().strip()
            # 获取排名网站
            site = i.get_attribute('mu')
            if site is None:
                if self.se == 'baidu_pc':
                    site = i.query_selector('a.c-showurl.c-color-gray')
                    if site is not None:
                        site = site.inner_text().strip()
                elif self.se == 'baidu_h5':
                    site = i.query_selector('.c-line-clamp1')
                    if site is not None:
                        site = site.inner_text().strip()
                else:
                    site = 'unknown'
            ranks.append([order, title, site])
        return ranks, order

    def get_rank(self, keywords, size=10):
        # 参数检查
        if size % 10 != 0 and size < 0:
            raise ValueError(
                'Size num can only be multiples of 10, like 20 30 …')
        if not isinstance(keywords, list):
            raise TypeError('The keywords must be list.')

        # 准备存储文件
        rank_file = open(
            '排名查询_%s_%s.csv' % (self.se, time.strftime('%Y%m%d')),
            'a+', encoding='utf-8-sig', newline='')
        writer = csv.writer(rank_file)

        # 构建浏览器环境
        with sync_playwright() as p:
            chrome = p.chromium.launch(headless=self.headless)
            if self.conf['device'] != 'pc':
                device = p.devices['Pixel 2']
                context = chrome.new_context(**device)
            else:
                context = chrome.new_context()
            page = context.new_page()

            # 访问搜索引擎
            page.goto(self.conf['index'])
            page.wait_for_load_state()

            # 采集排名数据
            for k in keywords:
                # 在搜索框输入搜索词
                page.fill(self.selectors['input_kw'], k)
                time.sleep(1)
                # 点击搜索按钮发起搜索请求并等待页面加载完成
                page.click(self.selectors['search'])
                time.sleep(randint(3, 5))
                page.wait_for_selector(self.selectors['rank_list'])
                # 从页面解析排名并实时写入文件
                start_order = 0
                ranks, start_order = self.parser_rank(page, 0)
                for line in ranks:
                    writer.writerow([k] + line)
                # 如果 size > 10，则需要解析翻页排名
                for _ in range(1, size//10):
                    # 点击翻页
                    page.click(self.selectors['turn_page'])
                    time.sleep(randint(2, 3))
                    page.wait_for_selector(self.selectors['rank_list'])
                    # 定位页面到页尾
                    page.press('body', 'End')
                    time.sleep(1)
                    # 解析翻页排名并实时写入文件
                    ranks, order = self.parser_rank(page, start_order)
                    for line in ranks:
                        writer.writerow([k] + line)
                # 清空搜索框
                page.fill(self.selectors['input_kw'], '')
                # 打印采集提示
                print('关键词【%s】排名采集完成。' % k)
            # 清理现场
            page.close()
            context.close()
            chrome.close()
        rank_file.close()


keywords = '''金地中心风华
中汇嘉园
华景新城鸿景楼
紫金花园
成山公寓
荀山花苑
潜龙曼海宁花园北区
蓝山CBD
嘉英大厦
水禾园'''.split('\n')

ranker = Ranker(se='baidu_pc', headless=False)
ranker.get_rank(keywords, 20)
