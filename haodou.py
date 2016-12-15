#! /usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from datetime import datetime
import time
import re
import json
import copy
import random
import binascii
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

import requests
import rsa

class TempLogger(object):

    timestamp_format = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, filepath=None):
        self.filepath = filepath

    def logprint(self, msg):
        timestamp = datetime.strftime(datetime.now(), self.timestamp_format)[:-3]
        print("%s %s"%(timestamp, msg))
        if self.filepath != None:
            with open(self.filepath, 'a') as f:
                f.write("%s %s\n"%(timestamp, msg))

class Haodou(object):

    domain = 'haodou.com'
    main_url = 'http://www.' + domain + '/'
    login_url = 'http://login.' + domain + '/'
    login_post_url = login_url + 'index.php?do=check'
    login_callback_url = 'http://www.qunachi.com/user/login.php?do=ssoLoginCallBack'
    sign_url = 'http://wo.' + domain + '/user/sign.php'
    point_url = 'http://shop.' + domain + '/my.php'
    ua = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    rsa_n = b'yevTQ5C8exDUo/c0y0Lrxp+quYD9vxjkKFAgdqV0PtLefJ4FEB4VeTTGDfqaWVgQXeQeyCp0yjCd8EGVUd/77z+Z/HlBpaavHwsE77Rjf3r9AC+aSN+ZZC4uoZL0bYDiDgYcG32CPLdVPP8zbKxa/BSbUb1PhxEot/fMTo+rLrU='
    rsa_e = b'AQAB'
    timestamp_re = re.compile(r'<input id="timestamp" name="timestamp" type="hidden" value="(\d+)" />')
    sso_token_re = re.compile(r'<input type="hidden" id="sso_token" name="token" value="(.*?)" />')
    callback_re = re.compile(r'<iframe src="(.*?)">')
    point_re = re.compile(r'<span class="orange f24 fg">(\d+)</span>')
    header = {u'Accept': 'application/json, text/javascript, */*; q=0.01',
              u'Accept-Encoding': 'deflate',
              u'Accept-Language': 'zh-CN,zh;q=0.8',
              u'Connection': 'keep-alive',
              u'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
              u'User-Agent': ua,
              u'X-Requested-With': 'XMLHttpRequest'}

    def __init__(self, account, password, logger=None):
        if logger:
            self.logger = TempLogger(logger)
        else:
            self.logger = TempLogger()
        self.account = account
        self.password = password
        self.session = requests.Session()
        self.login_timestamp = str(int(time.time()*1000))
        self.logger.logprint("Account: {}".format(self.account))

    @staticmethod
    def gen_key(rsa_n, rsa_e):
        n = int(binascii.b2a_hex(base64.b64decode(rsa_n)), 16)
        e = int(binascii.b2a_hex(base64.b64decode(rsa_e)), 16)
        return rsa.PublicKey(n, e)

    @staticmethod
    def rsa_password(timestamp, password, rsa_key):
        plain = timestamp + '|' + password
        return base64.b64encode(rsa.encrypt(plain.encode('utf-8'), rsa_key))

    def login(self):
        res = self.session.get(self.login_url, headers=self.header)
        if res.status_code != 200:
            self.logger.logprint("Get Login page fail: {}".format(res.status_code))
            return False
        timestamp = self.timestamp_re.search(res.text).group(1)
        sso_token = self.sso_token_re.search(res.text).group(1)
        rsa_key = self.gen_key(self.rsa_n, self.rsa_e)
        password = self.rsa_password(timestamp, self.password, rsa_key)
        post_data = {
            'account': self.account,
            'type': '1',
            'password': password,
            'referer': self.main_url,
            'auto_login': '1',
            'valicode': '',
            'sso_token': sso_token,
            }
        res = self.session.post(self.login_post_url, data=post_data, headers=self.header)
        if res.status_code != 200:
            self.logger.logprint("Try Login fail: {}".format(res.status_code))
            return False
        login_d = json.loads(res.text)
        p_data = [
            ('referer', self.main_url),
            ('sso_ticket', login_d['sso_ticket']),
            ('auto_login', '1'),
            ('__callback', 'HDAjax'+str(int(time.time()*1000))),
            ('__domain', self.login_url.replace('http://', '').replace('/', ''))
            ]
        nheader = copy.deepcopy(self.header)
        nheader.update({
            'Host': 'www.qunachi.com',
            'Referer': self.login_url,
            'Upgrade-Insecure-Requests': '1',
            })
        res = self.session.post(self.login_callback_url, data=p_data, headers=nheader)
        if res.status_code != 200:
            self.logger.logprint("Login callback fail: {}".format(res.status_code))
            return False
        callback_url = self.callback_re.search(res.text).group(1)
        parsed = urlparse.urlparse(callback_url)
        params = urlparse.parse_qsl(parsed.query)
        params_dict = {key: value for key, value in params}
        # callback_value = params_dict['callback']
        data = json.loads(params_dict['data'])
        # t = params_dict['t']
        if not data['status']:
            self.logger.logprint("Login callback fail: {!r}".format(data))
            return False
        self.logger.logprint("Get userid: {}".format(data['user_id']))
        res = self.session.get(callback_url)
        if res.status_code != 200:
            self.logger.logprint("Show Home Page fail: {}".format(res.status_code))
            return False
        self.login_timestamp = str(int(time.time()*1000))
        return True

    def sign(self):
        nheader = copy.deepcopy(self.header)
        nheader.update({
            'Host': 'wo.' + self.domain,
            'Referer': 'http://shop.' + self.domain + '/my.php'
        })
        callback_l = []
        callback_l.append('jQuery183')
        callback_l.append('{:17.16f}'.format(random.random()).replace('.', ''))
        callback_l.append('_')
        callback_l.append(self.login_timestamp)
        callback = ''.join(callback_l)
        payload = (
            ('do', 'Sign'),
            ('callback', callback),
            ('_', str(int(time.time()*1000))),
        )
        #self.logger.logprint("Sign Payload: {}".format(payload))
        res = self.session.get(self.sign_url, params=payload, headers=nheader)
        if res.status_code != 200:
            self.logger.logprint("Sign fail: {}".format(res.status_code))
            return False
        #with open(r'R:\sign.html', 'wb') as f:
        #    f.write(res.content)
        try:
            if u'"status":true' in res.text:
                return True
        except:
            pass
        self.logger.logprint("Sign fail: {!r}".format(res.text))
        return False

    def get_point(self):
        '''nheader = copy.deepcopy(self.header)
        nheader.update({
            'Host': 'wo.' + self.domain,
            'Referer': 'http://shop.' + self.domain + '/my.php'
        })
        callback_l = []
        callback_l.append('jQuery183')
        callback_l.append('{:17.16f}'.format(random.random()).replace('.', ''))
        callback_l.append('_')
        callback_l.append(self.login_timestamp)
        payload = (
            ('do', 'GetSignInfo'),
            ('callback', ''.join(callback_l)),
            ('_', str(int(time.time()*1000))),
        )'''
        res = self.session.get(self.point_url, headers=self.header)#, params=payload)
        if res.status_code != 200:
            self.logger.logprint("Get Point Page fail: {}".format(res.status_code))
            return False
        point_r = self.point_re.search(res.text)
        if point_r:
            point = point_r.group(1)
        else:
            point = ''
        return point

    def main(self):
        if self.login():
            self.logger.logprint("Login Success")
            point = self.get_point()
            if point is not False:
                self.logger.logprint("Get Point: {}".format(point))
            if self.sign():
                self.logger.logprint("Sign Success")
                point = self.get_point()
                if point is not False:
                    self.logger.logprint("Get Point: {}".format(point))

if __name__ == "__main__":
    Haodou('username', 'password).main()
