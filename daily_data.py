#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .baidutj import BaiduTJ
from .conf import bdtjzh
from .conf import webhook_key
from .conf import bjx_headers
import time
from playwright.sync_api import sync_playwright
import arrow
import requests
import json


def daily_report():
    ystday = arrow.now().shift(days=-1)
    _7day = arrow.now().shift(days=-8)

    u, p, t = bdtjzh
    jw = BaiduTJ(819550, u, p, t)
    data = jw.getdata(
        ystday.format('YYYYMMDD'),
        ystday.format('YYYYMMDD'),
        'source/all/a',
        'visitor_count',
        start_date2=_7day.format('YYYYMMDD'),
        end_date2=_7day.format('YYYYMMDD'),
        ViewType='type'
    )['body']['data'][0]['result']

    d = {
        'date' : ystday.format('MM/DD'),
        'total' : str(data['pageSum'][0][1]),
        'total_rate' : data['pageSum'][2][1]
    }
    if d['total_rate'] > 0:
        d['total_rate']= '+%s' % d['total_rate']

    content = '{date} 流量数据\n吉屋网总 UV {total}，同比上周 {total_rate}%'.format(**d)

    for i in range(0, len(data['items'][0])):
        dd = {
            'type' : data['items'][0][i][0]['name'],
            'uv' : data['items'][1][i][1],
            'rate' : data['items'][3][i][1]
        }
        if dd['rate'] > 0:
            dd['rate']= '+%s' % dd['rate']
        content += '\n{type} UV {uv}，同比上周 {rate}%'.format(**dd)

    content += '\n---------------------------------------'
    content += '\n{date} 获客数据'.format(**d)

    def get_fkj_cookie():
        cookies = {}
        with sync_playwright() as p:
            chrome = p.chromium.launch()
            context = chrome.new_context()
            page = context.new_page()
            page.goto('http://c.jiwu.com')
            page.fill('input[placeholder="请输入用户名"]', 'wangjing_zongbu')
            time.sleep(0.5)
            page.fill('input[placeholder="请输入密码"]', '582042')
            time.sleep(0.5)
            page.click('.send-verify.ivu-btn.ivu-btn-text')
            # TODO 验证码转发
            code = input('请输入短信验证码:')
            page.fill('input[placeholder="请输入短信验证码"]', code)
            time.sleep(0.5)
            page.click('.login-btn.ivu-btn.ivu-btn-primary.ivu-btn-long')
            time.sleep(5)
            for i in context.cookies():
                cookies[i['name']] = i['value']
            context.close()
            chrome.close()
        return cookies

    cookies = get_fkj_cookie()
    k2s = {
        'totalBDxcx': '百度小程序',
        'totalPhone': '来电',
        'totalZFBxcx': '支付宝小程序',
        'totalJiwuPC': '吉屋PC',
        'totalJiwuCP': '吉屋触屏',
        'totalJWapp': '吉屋APP',
        'totalWXxcx': '微信小程序'
    }

    for t in [ystday, _7day]:
        data = requests.get(
            'http://bjx.jiwu.com/bjxadmin/alaylsis/total/terminal_source?timeDimension=&isGjjCustomer=&isEsfCustomer=&terminalType=&cityType=&cityName=&cityId=&startTime=%s&endTime=%s&statisticType=1&isPay=0&total=0&page=1&pageSize=20' % (t.format('YYYY-MM-DD'), t.format('YYYY-MM-DD')), 
            headers=bjx_headers, cookies=cookies
        ).json()
        for k, v in data['data'].items():
            if k not in d.keys():
                d[k] = v
            else:
                if ((d[k] - v) / v) * 100 > 0:
                    d['rate'] = '+' + str(round(((d[k] - v) / v) * 100, 1)) + '%'
                else:
                    d['rate'] = str(round(((d[k] - v) / v) * 100, 1)) + '%'
                if k != 'totalCustomer':
                    content += ('\n%s 获客量 {%s}，同比上周{rate}' % (k2s[k], k)).format(**d)
    print(content)
    
    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % webhook_key

    message = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    requests.post(webhook, data=json.dumps(message))