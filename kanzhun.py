import re
from datetime import datetime

import requests

class temp_logger(object):

    timestamp_format = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, filepath=None):
        self.filepath = filepath

    def logprint(self, str):
        try:
            timestamp = datetime.strftime(datetime.now(), self.timestamp_format)[:-3]
            print(u"%s %s"%(timestamp, str))
            if self.filepath != None:
                with open(self.filepath, 'a') as f:
                    f.write(u"%s %s\n"%(timestamp, str))
        except:
            pass


class kanzhun(object):

    def __init__(self, account, password, logger=None):
        self.account = account
        self.password = password
        if logger == None:
            self.logger = temp_logger()
        else:
            self.logger = temp_logger(logger)
        self.kanzhun = requests.Session()
        self.common_headers = {
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                                'Accept-Encoding': 'deflate',
                                'Accept-Language': 'en-US,en;q=0.5',
                                'Host': 'www.kanzhun.com',
                                'Referer': 'http://www.kanzhun.com/',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:43.0) Gecko/20100101 Firefox/43.0',
                              }

    def login(self):
        url_checkaccountbind = 'http://www.kanzhun.com/account/checkAccountBind.json?'
        url_needcaptcha = 'http://www.kanzhun.com/account/checkAccountBind.json?'
        url_login = 'http://www.kanzhun.com/login.json'

        # Pre1 Login, check Account Bind
        res1 = self.kanzhun.get(url_checkaccountbind, params={'account': self.account}, headers=self.common_headers)
        try:
            if res1.json()['rescode'] != 1:
                self.logger.logprint(u"Pre1 Login Fail: {0}".format(res1.json()))
                return False
        except ValueError:
            self.logger.logprint(u"Pre1 Login Fail: Fail to get JSON response")
            return False
        self.logger.logprint(u"Pre1 Login Check Success")

        # Pre2 Login, check need captcha
        res2 = self.kanzhun.get(url_needcaptcha, params={'account': self.account}, headers=self.common_headers)
        try:
            if res2.json()['rescode'] != 1:
                self.logger.logprint(u"Pre2 Login Fail: {0}".format(res2.json()))
                self.logger.logprint(u"Maybe need captcha")
                return False
        except ValueError:
            self.logger.logprint(u"Pre2 Login Fail: Fail to get JSON response")
            return False
        self.logger.logprint(u"Pre2 Login Check Success")

        # Login
        logindata = {
                        'account': self.account,
                        'password': self.password,
                        'redirect': 'http://www.kanzhun.com/',
                        'remember': 'false',
                    }
        res3 = self.kanzhun.post(url_login, data=logindata, headers=self.common_headers)
        try:
            if res3.json()['rescode'] != 1:
                self.logger.logprint(u"Login Fail: {0}".format(res3.json()))
                return False
        except ValueError:
            self.logger.logprint(u"Login Fail: Fail to get JSON response")
            return False

        self.logger.logprint(u"Login Success")
        return True

    def sign(self):
        url_sign = 'http://www.kanzhun.com/integral/userSign.json'
        res = self.kanzhun.get(url_sign, headers=self.common_headers)
        try:
            if res.json()['rescode'] == 1:
                self.logger.logprint(u"Sign Success, Get: {0}".format(res.json()['integral']))
                return True
            else:
                self.logger.logprint(u"Sign Fail: {0}".format(res.json()))
                return False
        except ValueError:
            self.logger.logprint(u"Sign Fail: Fail to get JSON response")
            return False

    def getsignpoint(self):
        url_my = 'http://www.kanzhun.com/usercenter/account/'
        res = self.kanzhun.get(url_my, headers=self.common_headers)
        if res.status_code != 200:
            self.logger.logprint(u"Get Sign Point Fail: Fail to get proper response. {0}".format(res.status_code))
            return False
        re_point = re.compile(r'integral-number">(\d{1,5})')
        try:
            self.logger.logprint(u"Get Sign Point Success: {}".format(re_point.search(res.content).group(1)))
            return True
        except AttributeError:
            self.logger.logprint(u"Get Sign Point Fail: Fail to find Point RE")
            return False


if __name__ == "__main__":
    account = 'XXXXX'
    password = 'XXXXXX'
    log = 'R:\\kanzhun.log'
    k = kanzhun(account, password, log)
    if k.login():
        k.getsignpoint()
        if k.sign():
            k.getsignpoint()
