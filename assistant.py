# -*- coding: utf-8 -*-
import pickle
import random
import datetime
from dateutil.relativedelta import relativedelta
from util import *
from lxml import etree
import html

class Assistant(object):

    def __init__(self):
        self.username = ''
        self.nick_name = ''
        self.custno = ''
        self.is_login = False
        self.headers = {
            'User-Agent': USER_AGENT,
        }
        self.sess = requests.session()

        self.item_cat = dict()

        try:
            self._load_cookies()
        except Exception as e:
            pass

    def _load_cookies(self):
        cookies_file = ''
        for name in os.listdir('./cookies'):
            if name.endswith('.cookies'):
                cookies_file = './cookies/{0}'.format(name)
                break
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.sess.cookies.update(local_cookies)

        self.is_login = self._validate_cookies()

    def _validate_cookies(self):  # True -- cookies is valid, False -- cookies is invalid
        # user can't access to order list page (would redirect to login page) if his cookies is expired

        try:
            if self.get_order_list():
                return True
        except Exception as e:
            print(get_current_time(), e)
        #self.sess = requests.session()
        return False

    def _save_cookies(self):
        cookies_file = './cookies/{0}.cookies'.format(self.custno)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def login_by_QRcode(self):
        """二维码登陆
        :return:
        """
        if self.is_login:
            print(get_current_time(), '登录成功[%s,%s]' % (self.sess.cookies.get('nick'), self.sess.cookies.get('custno')))
            return True

        self._get_login_page()

        # download QR code
        if not self._get_QRcode():
            print(get_current_time(), '登录失败')
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

        r16 = get_r16()
        ms = int(time.time() * 1000)
        if self._login_auth(r16, ms):
            #if self._login_auth(r16, ms + 1):
            self.nick_name = self.sess.cookies.get('nick')
            self.custno = self.sess.cookies.get('custno')
            self._save_cookies()
            self.is_login = True
            print(get_current_time(), '认证成功')
            return True
        print(get_current_time(), '认证失败')
        return False

    def _get_login_page(self):
        url = "https://passport.suning.com/ids/login"
        page = self.sess.get(url, headers=self.headers, verify=CER_VERIFY)
        return page

    def _get_QRcode(self):
        url = 'https://passport.suning.com/ids/qrLoginUuidGenerate.htm'
        params = {
            'image': 'true',
            'yys': str(int(time.time() * 1000)),
        }
        headers = dict(self.headers)
        headers['Referer'] = 'https://passport.suning.com/ids/login'
        resp = self.sess.get(url=url, headers=headers, params=params, verify=CER_VERIFY)

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

        resp = self.sess.post(url=url, headers=self.headers, params=params, data=data, verify=CER_VERIFY)

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

    def _login_auth(self, r16, ms):
        url = 'https://loginst.suning.com/authStatus'
        params = {
            'callback': 'jQuery1720{}_{}'.format(r16, ms),
            '_': ms + 100
        }
        params = get_callback_time(r16)
        headers = dict(self.headers)
        headers['Referer'] = 'https://www.suning.com'

        resp = self.sess.get(url=url, headers=headers, params=params, verify=CER_VERIFY)

        if not response_status(resp):
            return False

        js = parse_json(resp.text)
        if js['authStatusResponse']:
            return True
        else:
            print(get_current_time(), js)
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

        resp = self.sess.get(url=url, headers=headers, params=params, allow_redirects=False, verify=CER_VERIFY)
        if not response_status(resp):
            print(get_current_time(), '获取订单失败')
            return False
        print(get_current_time(), '获取订单成功')
        return True

    def clear_cart(self):
        """清空购物车

        包括两个请求：
        1.选中购物车中所有的商品
        2.批量删除

        :return: 清空购物车结果 True/False
        """
        # 1.select all items  2.batch remove items
        r16 = get_r16()
        headers = dict(self.headers)

        #clear invalidate items
        print(get_current_time(), '删除失效商品')
        clear_url = 'https://shopping.suning.com/emptyCartOne.do'
        params = get_callback_time(r16)
        params['emptyFlag'] = 2
        headers['Referer'] = 'https://shopping.suning.com/cart.do'

        resp = self.sess.get(url=clear_url, headers=headers, params=params, verify=CER_VERIFY)
        if not response_status(resp):
            print('删除失效商品失败')
            return False

        cart_items_url = 'https://shopping.suning.com/showCartOneItems.do'
        params = get_callback_time(r16)
        headers['Referer'] = 'https://shopping.suning.com/cart.do?safp=d488778a.homepage1.lQl9p.1'

        resp = self.sess.get(url=cart_items_url, headers=headers, params=params, verify=CER_VERIFY)
        if not response_status(resp):
            print('获取购物车失败')
            return False

        js = parse_json(resp.text)
        html_str = html.unescape(etree.tostring(etree.HTML(js['html'])).decode("utf-8"))
        #print(html_str)
        result = etree.fromstring(html_str)
        es = result.xpath('//input[@name="icart1_goods_sel" and @type="checkbox"]')
        items = []
        for e in es:
            item = {}
            item['id'] = e.xpath('@id')[0]
            item['salesprice'] = e.xpath('@salesprice')[0]
            item['shopcode'] = e.xpath('@shopcode')[0]
            item['cmmdtyname'] = e.xpath('@cmmdtyname')[0]
            item['cmmdtycode'] = e.xpath('@cmmdtycode')[0]
            items.append(item)
        #print(items)
        if len(items) == 0:
            return True
        operateCheckCmmdty = ''
        for i, item in enumerate(items):
            if i > 0:
                operateCheckCmmdty = operateCheckCmmdty.join('%2C')
            operateCheckCmmdty = operateCheckCmmdty.join('%s-1' % item['id'])
        print(operateCheckCmmdty)
        oper_check_url = 'https://shopping.suning.com/operateCartOneCheck.do'
        params = get_callback_time(r16)
        params['loginSign'] = 'true'
        params['operateCheckCmmdty'] = operateCheckCmmdty
        headers['Referer'] = 'https://shopping.suning.com/cart.do?safp=d488778a.ddlb.lQl9p.1'
        resp = self.sess.get(url=oper_check_url, headers=headers, params=params, verify=CER_VERIFY)
        if not response_status(resp):
            print(get_current_time(), '全选失败')
            return False

        # auth_url = 'https://shopping.suning.com/authStatus'
        # r16 = get_r16()
        # params = get_callback_time(r16)
        # headers['Referer'] = 'https://shopping.suning.com/cart.do'
        # resp = self.sess.get(url=auth_url, headers=headers, params=params, verify=False)
        # if not response_status(resp):
        #     print(get_current_time(), 'shopping auth fail')
        #     return False

        del_url = 'https://shopping.suning.com/deleteCartOnePro.do'
        cummtyItemNos = ''
        for i, item in enumerate(items):
            if i > 0:
                cummtyItemNos = cummtyItemNos.join('%2C')
            cummtyItemNos = cummtyItemNos.join(item['id'])
        params = get_callback_time(r16)
        params['loginSign'] = 'true'
        params['cummtyItemNos'] = cummtyItemNos
        print(cummtyItemNos)
        resp = self.sess.get(url=del_url, headers=headers, params=params, verify=CER_VERIFY)
        print(resp.text)
        if not response_status(resp):
            print(get_current_time(), '删除选中失败')
            return False
        print('清空成功')
        return True

