#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import requests.exceptions
import json
import time
import datetime as dt
from ..conf import baidu_accounts

# TO DO LIST
# 1. 帐号出现问题时自动切换
# 2. 批量挖词结果合并去重


class KRService(object):
    def __init__(self, username=baidu_accounts[2][0],password=baidu_accounts[2][1],
                 token=baidu_accounts[2][2]):
        self.username = username
        self.password = password
        self.token = token

        self.api = 'https://api.baidu.com/json/sms/service/KRService/'
        self.methods = {
            'getKRByQuery': self.api + 'getKRByQuery',
            'getKRFileIdByWords': self.api + 'getKRFileIdByWords',
            'getFileStatus': self.api + 'getFileStatus',
            'getFilePath': self.api + 'getFilePath'
        }
        self.common_headers = {
            'content-type': 'application/json',
            'username': self.username.encode('utf-8'),
            'password': self.password,
            'token': self.token
        }
        self.common_req_body = {
            'header': {
                'username': self.username,
                'password': self.password,
                'token': self.token
            }
        }

    def req_aqi(self, method, body):
        req_body = self.common_req_body
        req_body['body'] = body
        payload = json.dumps(req_body)
        req = requests.post(
                self.methods[method],data=payload,
                headers=self.common_headers
        )
        res = req.json()
        req.close()
        return res

    def get_keywords_by_query(self, query):
        query = str(query)
        body = {'queryType': 1, 'query': query}
        res = self.req_aqi('getKRByQuery', body)
        return res['body']['data']

    def get_query_info(self, query):
        res = self.get_keywords_by_query(query)
        for i in res:
            if i['word'] == query:
                return i

    def get_file_id(self, seed_words):
        body = {'seedWords': seed_words,
                'seedFilter': {'device': 0, 'competeLow': 0}}
        res = self.req_aqi('getKRFileIdByWords', body)
        return res['body']['data'][0]['fileId']

    def get_file_statu(self, file_id):
        body = {'fileId': file_id}
        res = self.req_aqi('getFileStatus', body)
        statu_code = res['body']['data'][0]['isGenerated']
        status_info = {
            1: '等待中', 2: '处理中', 3: '处理成功'
        }
        return status_info[statu_code]

    def get_file_path(self, file_id):
        body = {'fileId': file_id}
        res = self.req_aqi('getFilePath', body)
        return res['body']['data'][0]['filePath']

    def get_keywords_by_seeds(self, seeds_file_path):
        try:
            all_seeds = [x.strip() for x in
                        open(seeds_file_path, 'r', encoding='utf-8')]
        except UnicodeDecodeError:
            all_seeds = [x.strip() for x in
                        open(seeds_file_path, 'r', encoding='utf-8')]
        # encoding = 'utf-8'
        print('### 关键词已提取')
        while all_seeds:
            req_seeds = all_seeds[:100]
            all_seeds = all_seeds[100:]

            print('### 获取关键词文件 id')
            file_id = self.get_file_id(req_seeds)
            time.sleep(5)
            print('### 获取关键词文件状态')
            file_status = self.get_file_statu(file_id)

            count = 1
            while file_status != '处理成功':
                if count < 4:
                    print('\t服务器生成文件中，10s 后重新获取状态')
                    time.sleep(10)
                    file_status = self.get_file_statu(file_id)
                    count += 1
                else:
                    break

            if file_status != '处理成功':
                print('\t服务器生成文件失败，跳过当前循环，失败关键词>failseeds.txt')
                with open('failseeds.txt', 'a+') as failfile:
                    failfile.write('\n'.join(req_seeds))
                all_seeds += req_seeds
                continue
            else:
                print('\t服务器生成文件完毕')
                time.sleep(2)
                print('### 获取关键词文件路径')
                file_path = self.get_file_path(file_id)
                file_req = requests.get(file_path)
                # if len(file_req.content) == 0:
                file_name = dt.datetime.now().strftime("%m%d%H%M%S") + '.csv'
                with open(file_name, 'wb') as f:
                    f.write(file_req.content)
                print('### 关键词文件已保存至 %s' % file_name)
                time.sleep(1)

krs = KRService()

if __name__ == "__main__":
    krs = KRService()
    while True:
        print('请选择想要进行的操作编号：\n'
              '1. 单个挖词\n2. 批量挖词\n3. 查询单个词搜索量\n4. 批量查询搜索量')
        mode = input()
        if mode == '1':
            seed_word = input('请输入种子词：')
            result = krs.get_keywords_by_query(seed_word)
            file = '挖词结果_' + dt.datetime.now().strftime("%m%d%H%M") + '.txt'
            with open(file, 'w', encoding='utf-8') as f:
                f.write('关键词\t搜索量\t移动搜索量\n')
                for x in result:
                    f.write(
                        '%s\t%s\t%s\n' % (x['word'], x['pv'], x['mobilePV']))
            print('结果已写入 %s' % file)

        elif mode == '2':
            print('请将种子词放入 seeds.txt 文件，每行一个，然后将 seeds.txt 文件放到此脚本所在目录')
            flag = input('是否已放好 seeds.txt 文件？ y/n ')
            if flag == 'y':
                krs.get_keywords_by_seeds('seeds.txt')
            else:
                print('请放好 seeds.txt 文件再来\n')

        elif mode == '3':
            seed_word = input('请输入要查询的关键词：')
            result = krs.get_query_info(seed_word)
            print(result)
        
        elif mode == '4':
            print('请将种子词放入 seeds.txt 文件，每行一个，然后将 seeds.txt 文件放到此脚本所在目录')
            flag = input('是否已放好 seeds.txt 文件？ y/n ')
            if flag == 'y':
                print('关键词\tPC\t移动\t总计')
                for i in [x.strip() for x in open('seeds.txt', 'r', encoding='utf-8')]:
                    try:
                        result = krs.get_query_info(i)
                    except Exception:
                        continue
                    with open('搜索量查询结果.txt', 'a+', encoding='utf-8') as f:
                        if result is not None:
                            print('%s\t%s\t%s\t%s' % (i, result['pcPV'], result['mobilePV'], result['pv']))
                            f.write('%s\t%s\t%s\t%s\n' % (i, result['pcPV'], result['mobilePV'], result['pv']))
                        else:
                            print('%s\t0\t0\t0' % i)
                            f.write('%s\t0\t0\t0\n' % i)
                    time.sleep(0.5)
            else:
                print('请放好 seeds.txt 文件再来\n')
        else:
            break
