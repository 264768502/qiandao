#! /usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import time
import re
try:
    from HTMLParser import HTMLParser as html
except ImportError:
    import html

import requests


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

class UShare(object):

    domain = 'u-share.cn'
    main_url = 'http://' + domain + '/'
    login_url = 'http://' + domain + '/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
    login_post_url = 'http://' + domain + '/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1'

    sign_url = 'http://' + domain + '/plugin.php?id=gsignin:index'
    point_url = 'http://' + domain + '/home.php?mod=spacecp&ac=credit&showcredit=1'

    formhash_re = re.compile(r'<input type="hidden" name="formhash" value="(.*?)" />')
    referer_re = re.compile(r'<input type="hidden" name="referer" value="(.*?)" />')
    point_re = re.compile(r'<li class="xi1 cl"><em>.*?</em>\D*(\d+).*?</li>')
    sign_re = re.compile(r'<a href="(.*?)" target="formsubmit" class="right">')

    def __init__(self, account, password, logger=None):
        if logger:
            self.logger = TempLogger(logger)
        else:
            self.logger = TempLogger()
        self.account = account
        self.password = password
        self.session = requests.Session()
        self.logger.logprint("Account: {}".format(self.account))

    def login(self):
        res = self.session.get(self.login_url)
        if res.status_code != 200:
            self.logger.logprint("Get Login page fail: {}".format(res.status_code))
            return False
        formhash = self.formhash_re.search(res.text).group(1)
        referer = self.referer_re.search(res.text).group(1)
        post_data = {
                'formhash': formhash,
                'referer': referer,
                'loginfield':'username',
                'username': self.account,
                'password': self.password,
                'questionid': '0',
                'answer': '',
                'loginsubmit': 'true',
            }
        res = self.session.post(self.login_post_url, data=post_data)
        if res.status_code != 200:
            self.logger.logprint("Try Login fail: {}".format(res.status_code))
            return False
        return True

    def sign(self):
        res = self.session.get(self.sign_url)
        if res.status_code != 200:
            self.logger.logprint("Pre Sign fail: {}".format(res.status_code))
            return False
        try:
            back_str = self.sign_re.search(res.text).group(1)
            try:
                back_link = html().unescape(back_str)
            except:
                back_link = html.unescape(back_str)
            sign_url = 'http://' + self.domain + '/' + back_link
            print("sign_url: {}".format(sign_url))
            res = self.session.get(sign_url)
            if res.status_code != 200:
                self.logger.logprint("Sign fail: {}".format(res.status_code))
                return False
            if u'\u7b7e\u5230\u6210\u529f' in res.text:
                return True
            self.logger.logprint("Sign fail: {!r}".format(res.text))
        except Exception as err:
            self.logger.logprint("Sign fail: {!r}".format(res.text))
            self.logger.logprint("Sign fail: {!r}".format(err))
        return False

    def get_point(self):
        res = self.session.get(self.point_url)
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
    UShare('username', 'password').main()
