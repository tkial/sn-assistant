# -*- coding: utf-8 -*-
import datetime

from dateutil.relativedelta import relativedelta

from util import *


class Assistant(object):
    def __init__(self, plat, account):
        self.plat = plat.value
        self.account = account
        self.is_login = False
        self.headers = {
            'User-Agent': USER_AGENT,
        }
        self.sess = requests.session()

        try:
            load_cookies(self.plat, self.account, self.sess.cookies)
            print(self.sess.cookies)
        except Exception as e:
            print(e)
            pass
        self.is_login = self._validate_cookies()

    def _validate_cookies(self):  # True -- cookies is valid, False -- cookies is invalid
        # user can't access to order list page (would redirect to login page) if his cookies is expired
        if not self.sess.cookies.get('VipRUID'):
            return False
        url = 'http://order.vip.com/order/orderlist'
        self.headers['Referer'] = 'https://www.vip.com/'
        resp = self.sess.get(url=url, headers=self.headers, allow_redirects=False, verify=CER_VERIFY)
        if response_status(resp):
            return True

        return False

    def get_order_list(self):
        url = 'http://order.vip.com/order/orderlist'
        params = {
            'orderStatus': 'all',
            'type': 'all',
            'pageNum': 1
        }
        resp = self.sess.get(url=url, headers=self.headers, params=params, allow_redirects=False, verify=CER_VERIFY)
        if response_status(resp):
            url = 'http://mapi.vip.com/vips-mobile/rest/order/get_integrate_count/pc/v1'
            params = {
                'callback': 'getIntergrateCountCb',
                'app_name': 'shop_pc',
                'app_version': '1',
                'warehouse': self.sess.cookies.get('vip_wh'),
                'fdc_area_id': self.sess.cookies.get('vip_city_code'),
                'client': 'pc',
                'mobile_platform': '1',
                'province_id': self.sess.cookies.get('vip_province'),
                'api_key': '70f71280d5d547b2a7bb370a529aeea1',
                'user_id': self.sess.cookies.get('VipRUID'),
                'mars_cid': self.sess.cookies.get('mars_cid'),
                'wap_consumer': 'a',
                'fields': 'allCount%2CunpaidCount%2CpendingReceiveCount%2CcompletedCount%2CcancelledCount%2CpresellCount%2CcouponCount',
                '_': int(time.time() * 1000)
            }
            resp = self.sess.get(url=url, headers=self.headers, params=params, allow_redirects=False, verify=CER_VERIFY)
            print(resp.url)
            if response_status(resp):
                url = 'http://mapi.vip.com/vips-mobile/rest/order/pc/get_union_order_list/v1'
                del params['fields']
                params.update({
                    'callback': 'getUnionOrderListCb',
                    'page_num': '1',
                    'page_size': '10',
                    'query_status': 'all',
                    'order_types': 'all',
                    '_': int(time.time() * 1000)})

                resp = self.sess.get(url=url, headers=self.headers, params=params, allow_redirects=False, verify=CER_VERIFY)
                if response_status(resp):
                    print(get_current_time(), '获取订单成功')
                    print(resp.text)
                    return True

        print(get_current_time(), '获取订单失败')
        return False

    def login_by_QRcode(self):
        """二维码登陆
        :return:
        """
        if self.is_login:
            print(get_current_time(), '登录成功[%s,%s]' % (self.plat, self.account))
            return True

        self._get_login_page()
        print(self.sess.cookies)
        # download QR code
        qr_token = self._get_QRcode()
        if not qr_token:
            return False

        # get QR code ticket
        ticket = None
        retry_times = 90
        for _ in range(retry_times):
            ticket = self._get_QRcode_ticket(qr_token)
            if ticket:
                break
            time.sleep(2)
        else:
            print(get_current_time(), '二维码扫描出错')
            return False

        save_cookies(self.plat, self.account, self.sess.cookies)
        self.is_login = True
        print(self.account, self.sess.cookies)
        return True

    def _get_login_page(self):
        url = "https://www.vip.com"
        page = self.sess.get(url, headers=self.headers, verify=CER_VERIFY)
        self.sess.cookies.set('mars_cid', mar_rand2(), domain='.vip.com', expires=gmtime_d(732))
        self.sess.cookies.set('mars_pid', '0', domain='.vip.com', expires=gmtime_d(732))
        self.sess.cookies.set('mars_sid', mar_rand(), domain='.vip.com', expires=gmtime_d(0))
        self.sess.cookies.set('visit_id', mar_guid(), domain='.vip.com', expires=gmtime_d(0.5 / 24))
        return page

    def _get_QRcode(self):
        url = 'https://passport.vip.com/qrLogin/initQrLogin'
        self.headers['Referer'] = 'https://www.vip.com'
        resp = self.sess.post(url, headers=self.headers, verify=CER_VERIFY)
        if not response_status(resp):
            print('init qr login fail')
            return False
        print(resp.text)
        js = json.loads(resp.text)
        if js['code'] != 200:
            print('init qr login fail')
            return False
        qr_token = js['qrToken']
        url = 'https://passport.vip.com/qrLogin/getQrImage'
        params = {'qrToken': qr_token}
        resp = self.sess.get(url=url, headers=self.headers, params=params, verify=CER_VERIFY)

        if not response_status(resp):
            print(get_current_time(), '获取二维码失败')
            return False

        QRCode_file = 'QRcode.png'
        save_image(resp, QRCode_file)
        print(get_current_time(), '二维码获取成功，请打开唯品会APP扫描')
        open_image(QRCode_file)
        return qr_token

    def _get_QRcode_ticket(self, qr_token):
        url = 'https://passport.vip.com/qrLogin/checkStatus'
        data = {'qrToken': qr_token}
        resp = self.sess.post(url=url, headers=self.headers, data=data, verify=CER_VERIFY)

        if not response_status(resp):
            print(get_current_time(), '获取二维码扫描结果出错')
            return False

        js = json.loads(resp.text)
        if js['status'] == 'NOT_SCANNED':
            print(get_current_time(), '请扫描二维码')
            return False
        if js['status'] == 'SCANNED':
            print(get_current_time(), '已扫描，请登录')
            return False
        if js['status'] == 'CONFIRMED':
            print(get_current_time(), '登录成功')
            return True
        if js['status'] == '3':
            print(get_current_time(), '二维码已过期')
            return False
        return False
