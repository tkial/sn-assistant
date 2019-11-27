# -*- coding: utf-8 -*-
import datetime

from dateutil.relativedelta import relativedelta

from util import *

class Assistant(object):
    def __init__(self, plat, id):
        self.plat = plat.value
        self.id = id
        self.is_login = False
        self.headers = {
            'User-Agent': USER_AGENT,
        }
        self.sess = requests.session()

        try:
            load_cookies(self.plat, self.id, self.sess.cookies)
        except Exception as e:
            print(e)
            pass
        print('after pass')
        self.is_login = self._validate_cookies()

    def _validate_cookies(self):  # True -- cookies is valid, False -- cookies is invalid
        # user can't access to order list page (would redirect to login page) if his cookies is expired
        print('_validate_cookies')
        try:
            if self.get_order_list():
                print(self.id, self.sess.cookies)
                return True
        except Exception as e:
            print(get_current_time(), e)
        return False

    def get_order_list(self):
        url = 'https://order.suning.com/order/queryOrderList.do'

        headers = dict(self.headers)
        headers['Referer'] = 'https://order.suning.com/order/orderList.do?safp=d488778a.homepage1.Ygnh.1'

        dt_now = datetime.datetime.now()
        dt_3month_ago = dt_now - relativedelta(months=3)

        params = {
            'transStatus': '',
            'pageNumber': '1',
            'condition': '',
            'startDate': dt_3month_ago.strftime('%Y-%m-%d'),
            'endDate': dt_now.strftime('%Y-%m-%d'),
            'orderType': ''
        }

        resp = self.sess.get(url=url, headers=headers, params=params, allow_redirects=False, verify=False)
        if not response_status(resp):
            print(get_current_time(), '获取订单失败')
            return False
        print(get_current_time(), '获取订单成功')
        return True

    def login_by_QRcode(self):
        """二维码登陆
        :return:
        """
        if self.is_login:
            print(get_current_time(), '登录成功[%s,%s]' % (self.plat, self.id))
            return True

        self._get_login_page()

        # download QR code
        if not self._get_QRcode():
            return False

        # get QR code ticket
        ticket = None
        retry_times = 90
        r16 = get_r16()
        ms = int(time.time() * 1000)
        for _ in range(retry_times):
            ticket = self._get_QRcode_ticket(r16, ms)
            ms = ms + 1
            if ticket:
                break
            time.sleep(2)
        else:
            print(get_current_time(), '二维码扫描出错')
            return False

        print(get_current_time(), '已登陆，开始认证')

        if self._login_auth():
            save_cookies(self.plat, self.id, self.sess.cookies)
            self.is_login = True
            print(get_current_time(), '认证成功')
            print(self.id, self.sess.cookies)
            return True
        print(get_current_time(), '认证失败')
        return False

    def _get_login_page(self):
        url = "https://passport.suning.com/ids/login"
        page = self.sess.get(url, headers=self.headers, verify=False)
        return page

    def _get_QRcode(self):
        url = 'https://passport.suning.com/ids/qrLoginUuidGenerate.htm'
        params = {
            'image': 'true',
            'yys': str(int(time.time() * 1000)),
        }
        headers = dict(self.headers)
        headers['Referer'] = 'https://passport.suning.com/ids/login'
        resp = self.sess.get(url=url, headers=headers, params=params, verify=False)

        if not response_status(resp):
            print(get_current_time(), '获取二维码失败')
            return False

        QRCode_file = 'QRcode.png'
        save_image(resp, QRCode_file)
        print(get_current_time(), '二维码获取成功，请打开苏宁易购APP扫描')
        open_image(QRCode_file)
        return True

    def _get_QRcode_ticket(self, r16, ms):
        url = 'https://passport.suning.com/ids/qrLoginStateProbe'

        params = {
            'callback': 'jQuery1720{}_{}'.format(r16, ms),
        }

        data = {
            'uuid': self.sess.cookies.get('ids_qr_uuid'),
            'terminal': 'PC'
        }

        resp = self.sess.post(url=url, headers=self.headers, params=params, data=data, verify=False)

        if not response_status(resp):
            print(get_current_time(), '获取二维码扫描结果出错')
            return False

        js = parse_json(resp.text)
        if js['state'] == '0':
            print(get_current_time(), '请扫描二维码')
            return False
        if js['state'] == '1':
            print(get_current_time(), '已扫描，请登录')
            return False
        if js['state'] == '2':
            print(get_current_time(), '登录成功')
            return True
        if js['state'] == '3':
            print(get_current_time(), '二维码已过期')
            return False

    def _login_auth(self):
        r16 = get_r16()
        ms = int(time.time() * 1000)
        url = 'https://loginst.suning.com/authStatus'
        params = get_callback_time(r16)
        headers = dict(self.headers)
        headers['Referer'] = 'https://www.suning.com'

        resp = self.sess.get(url=url, headers=headers, params=params, verify=False)

        if not response_status(resp):
            return False

        js = parse_json(resp.text)
        if js['authStatusResponse']:
            return True
        else:
            print(get_current_time(), js)
            return False
