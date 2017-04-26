#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

# requests.adapters.DEFAULT_RETRIES = 5

# 将用户名和密码传入auth参数，通过get方法向服务器发出请求，requests会将用户名和密码编成request.headers的Authorization参数来进行请求
# r = requests.get('http://127.0.0.1:5000/login',auth=('yifeng','123456'))
# print(r.text)

# token = 'eWlmZW5nOjAuMTIyOTQ4ODkwMjM2OjE0OTA5Mzc3NTQuMjI='
# r = requests.get('http://127.0.0.1:5000/test',params={'token' : token})
# print(r.text)

r = requests.get('http://127.0.0.1:5000/client/login')  # 该路由会将访问重定向至授权服务器oauth路径
print(r.text)   # 返回oauth的'please login'信息
print('=========')
print(r.history)   # history attribute can show the redirect info
print('=========')
print(r.url)
print('=========')
uri_login = r.url.split('?')[0] + '?user=yifeng&pw=123456'
r2 = requests.get(uri_login)
print(r2.text)
print(r2.history)
print('=========')
r = requests.get('http://127.0.0.1:5000/test1', params={'token':r2.text})
print(r.text)

