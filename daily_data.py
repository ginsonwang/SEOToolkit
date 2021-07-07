#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .baidutj import BaiduTJ
from .conf import bdtjzh
from .conf import webhook_key
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
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64',
        'accessToken': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ3YW5namluZ196b25nYnUiLCJleHAiOjE2MjU0NzQ1NzN9.WoAEnnBd0Vl72QG3sDRcZQX7WmcIJE707bTfL6Hqo1w',
        'Referer': 'http://bjx.jiwu.com/data-analysis/customer-report',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
    }

    for t in [ystday, _7day]:
        data = requests.get(
            'http://bjx.jiwu.com/bjxadmin/alaylsis/detail/terminal_source?timeDimension=&isGjjCustomer=&isEsfCustomer=&terminalType=&cityType=&cityName=&cityId=&startTime=%s&endTime=%s&statisticType=1&isPay=0&total=0&page=1&pageSize=20' % (t.format('YYYY-MM-DD'), t.format('YYYY-MM-DD')), 
            headers=headers, cookies=cookies
        ).json()
        for l in data['data']['list']:
            if l['platform'] not in d.keys():
                d[l['platform']] = l['totalcustomer']
            else:
                d[l['platform'] + '_vs'] = l['totalcustomer']
        
    for k in ['吉屋PC', '吉屋触屏', '百度小程序', '微信小程序', '吉屋APP', '来电']:
        rate = ((d[k] - d[k + '_vs'])/d[k + '_vs'])*100
        if rate > 0:
            rate = '+' + str(round(rate, 1)) + '%'
        else:
            rate = str(round(rate, 1)) + '%'
        d[k + '_rate'] = rate
        content += ('\n%s 获客量 {%s}，同比上周{%s_rate}' % (k, k, k)).format(**d)
    
    print(content)
    

    webhook = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % webhook_key

    message = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    requests.post(webhook, data=json.dumps(message))