#!/usr/bin/env python
# -*- coding:utf-8 -*-
#from assistant import Assistant
from util import Plat
from vip_assistant import Assistant
import ssl
ssl._create_default_https_context = ssl._create_unverified_context()

if __name__ == '__main__':
    """
    重要提示：此处为示例代码之一，请移步下面的链接查看使用教程👇
    https://github.com/tychxn/jd-assistant/wiki/1.-%E4%BA%AC%E4%B8%9C%E6%8A%A2%E8%B4%AD%E5%8A%A9%E6%89%8B%E7%94%A8%E6%B3%95
    """
    #ssl._create_default_https_context = ssl._create_unverified_context()
    asst = Assistant(Plat.SN, '13760735626')  # 初始化
    asst.login_by_QRcode()  # 扫码登陆
    #asst.clear_cart()
    #asst.get_order_list()
    #asst.clear_cart()
    #asst.exec_reserve_seckill_by_time(sku_id="100009083498", buy_time="2019-11-10 22:42:30.000")
    # 执行预约抢购
    # 5个参数
    # sku_id: 商品id
    # buy_time: 下单时间，例如：'2019-11-10 22:41:30.000'
    # retry: 抢购重复执行次数，可选参数，默认4次
    # interval: 抢购执行间隔，可选参数，默认4秒
    # num: 购买数量，可选参数，默认1个
