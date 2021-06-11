#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
采集百度、360、搜狗下拉框关键词脚本
'''

# TODO 改成 playwright 实现

import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class recommend_word_tool(object):
    def __init__(self):
        self.brs_option = webdriver.ChromeOptions()
        self.brs_option.add_argument('--headless')
        self.brs_option.add_argument('--blink-settings=imagesEnabled=false')
        self.brs_option.add_argument('user-agent="ozilla/5.0 (iPhone; CPU'
            'iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, l'
            'ike Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/86.0.'
             '4240.183"')

        self.brs_option.add_experimental_option(
            'excludeSwitches', ['enable-logging']
            )
        self.brs = webdriver.Chrome(
            executable_path="chromedriver.exe", options=self.brs_option
            )

        self.config = {
            'base': {
                'window': self.brs.current_window_handle,
            }
        }

    def __reset__(self):
        self.brs.switch_to.window(self.config['base']['window'])

        # self.brs.get('https://m.baidu.com')
        self.brs.execute_script('window.open("https://m.baidu.com")')
        self.config['bd'] = {
            'window': self.brs.window_handles[-1],
            'input_id': 'index-kw',
            'drop_class': 'suggest-content',
            'sug_class': 'c-slink-new-strong'
            }

        tmp = set(self.brs.window_handles)

        self.brs.execute_script('window.open("https://m.sogou.com")')
        self.config['sg'] = {
            'window': [x for x in self.brs.window_handles if x not in tmp][0],
            'input_id': 'keyword',
            'drop_class': 'suggestion',
            'sug_class': 'hint'
            }

        tmp = set(self.brs.window_handles)

        self.brs.execute_script('window.open("https://m.so.com")')
        self.config['so'] = {
            'window': [x for x in self.brs.window_handles if x not in tmp][0],
            'input_id': 'q',
            'drop_class': 'suggest-content',
            'sug_class': 'related-search-b'
            }
        del tmp


def get_drops(word):
    t = recommend_word_tool()
    print('--%s 下拉框采集中…' % word)
    drops = []
    t.__reset__()
    for k, v in t.config.items():
        if k != 'base':
            t.brs.switch_to.window(v['window'])
            kw_input = t.brs.find_element_by_id(v['input_id'])

            alphabet = 'abcdefghijklmnopqrstuvwxyz'
            for w in alphabet:
                kw_input.send_keys(word + w)
                time.sleep(0.5)

                n_drops = t.brs.find_element_by_class_name(v['drop_class'])
                n_drops = n_drops.text.split('\n')
                drops += n_drops[:-2] if k == 'sg' else n_drops

                kw_input.clear()
            t.brs.close()
    print('-- %s 下拉框采集完毕' % word)
    return list(set(drops))


def get_sugs(word):
    print('-- %s 相关搜索采集中' % word)
    t = recommend_word_tool()
    sugs = []
    t.__reset__()
    for k, v in t.config.items():
        if k != 'base':
            t.brs.switch_to.window(v['window'])
            kw_input = t.brs.find_element_by_id(v['input_id'])

            kw_input.send_keys(word)
            time.sleep(0.5)
            kw_input.send_keys(Keys.ENTER)
            time.sleep(2)
            if k == 'bd':
                sug_eles = t.brs.find_elements_by_class_name(v['sug_class'])
                sugs += [x.text.strip() for x in sug_eles]
            else:
                sug_eles = t.brs.find_elements_by_class_name(v['sug_class']) 
                aas = [x.find_elements_by_tag_name('a') for x in sug_eles]
                aas = sum(aas, [])
                sugs += [x.text.strip() for x in aas]
    print('-- %s 相关搜索采集完毕' % word)
    return list(set(sugs))


def get_sugs_and_drops(word):
    result_words = []
    result_words += get_drops(word)
    result_words += get_sugs(word)
    return result_words


if __name__ == '__main__':
    print('-- 开始采集')
    t = recommend_word_tool()
    f = open('SE推荐关键词.txt', 'a+', encoding='utf-8')

    try:
        seeds = [x.strip() for x in open('种子词.txt', 'r', encoding='utf-8')]
    except UnicodeDecodeError:
        seeds = [x.strip() for x in open('种子词.txt', 'r', encoding='gbk')]

    for seed in seeds:
        for i in t.get(seed):
            f.write('%s,%s\n' % (seed, i))
            f.flush()

    f.close()
    t.brs.quit()
    del t

