#!/usr/bin/env python3

import json
import requests
import datetime
import sys
from .conf import bdtjzh

siteids = {
        '深圳': 834043,
        '惠州': 7394767,
        '二手房': 10295378,
        '全站': 819550
    }

class BaiduTJ(object):
    def __init__(self, site_id, username, password, token):
        self.siteId = site_id
        self.username = username
        self.password = password
        self.token = token

    def getdata(self, start, end, method, metrics, **kw):
        """
        百度统计 API 请求参数见 ：https://tongji.baidu.com/api/manual/
        :param start: 开始日期, 20190101
        :param end: 截止日期, 20190101
        :param method: 请求报告
        :param metrics: 数据指标
        :param kw: 其他参数
        :return: json 格式的结果
        """
        base_url = "https://api.baidu.com/json/tongji/v1/ReportService/getData"
        body = {"header": {"account_type": 1, "password": self.password,
                           "token": self.token, "username": self.username},
                "body": {"siteId": self.siteId, "method": method,
                         "start_date": start, "end_date": end,
                         "metrics": metrics}}
        for key in kw:
            body['body'][key] = kw[key]
        data = json.dumps(body)
        res = requests.post(base_url, data)
        res = json.loads(res.text)
        return res

    def get_date_list(self, start, end):
            date_list = [start, end]
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
            for i in range(1, (end - start).days):
                date = (start + datetime.timedelta(days=i)).strftime('%Y%m%d')
                date_list.insert(-1, date)
            return date_list

    def get_keywords(self, start, end):
        date_list = self.get_date_list(start, end)
        kw_uv = {}

        for d in date_list:
            res = self.getdata(
                d, d, 'source/searchword/a', 'ip_count'
            )
            if res['header']['desc'] != 'success':
                print(res)
                if date_list.count(d) < 3:
                    date_list.append(d)
                continue
            keywords = res['body']['data'][0]['result']['items'][0]
            uvs = res['body']['data'][0]['result']['items'][1]
            for i, x in enumerate(keywords):
                if uvs[i][0] != '×':    # 排除付费流量，不是 X 小写，是叉号
                    continue
                else:
                    kw = x[0]['name']
                    if kw not in kw_uv.keys():
                        kw_uv[kw] = uvs[i][1]
                    else:
                        kw_uv[kw] += uvs[i][1]
            print(d)

        for k, v in kw_uv.items():
            with open('%s搜索词-%s_%s.txt' % (self.siteId, start, end), 'a+', encoding='utf-8') as f:
                    f.write('%s,%s\n' % (k, v))
        
        print('%s - %s 搜索词数据下载完成' % (start, end))

    def get_landingpage(self, start, end):
        date_list = self.get_date_list(start, end)
        url_uv = {}

        for d in date_list:
            res = self.getdata(
                d, d, 'visit/landingpage/a', 'ip_count'
            )
            if res['header']['desc'] != 'success':
                print(res)
                continue
            urls = res['body']['data'][0]['result']['items'][0]
            uvs = res['body']['data'][0]['result']['items'][1]
            for i, x in enumerate(urls):
                url = x[0]['name']
                if 'hmsr=' in url:  # 排除付费流量
                    continue
                else: 
                    if url not in url_uv.keys():
                        url_uv[url] = uvs[i][0]
                    else:
                        url_uv[url] += uvs[i][0]
            print(d)
        
        for k, v in url_uv.items():
            with open('入口页-%s_%s.txt' % (start, end), 'a+', encoding='utf-8') as f:
                    f.write('%s,%s\n' % (k, v))
        
        print('%s - %s 入口页数据下载完成' % (start, end))

# bdtj = BaiduTJ(
#         siteids[site], bdtjzh[0], bdtjzh[1], bdtjzh[2]
#         )

# # if __name__ == '__main__':
# #     site, method, start, end = sys.argv[1:]
# #     func = {
# #         'landingpage': jw.get_landingpage,
# #         'keywords': jw.get_keywords
# #     }
# #     func[method](start, end)
    