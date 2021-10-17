

from bs4 import BeautifulSoup
import urllib.request
from urllib import error
import requests
import json
import ast
import sys
sys.path.append("..")
import log.custom_logger as custom_logger
import database.db_operator as db_operator
import parsers.disguise as disguise

class CollectStocksEstimationIndexes:
    # 从乌龟量化收集股票的估值指标，滚动市盈率，扣非滚动市盈率，市净率，股息率

    def __init__(self, stock_code, stock_name, stock_exchange_location):
        # param： stock_code  股票代码  600519
        # param: stock_name 股票名称  中国茅台
        # param： stock_exchange_location  股票上市地 sz或者sh

        self.stock_code = stock_code
        self.stock_name = stock_name
        self.stock_exchange_location = stock_exchange_location

    # https://androidinvest.com/stock/history/sh600519/

    def generate_web_address(self,stock_code, stock_exchange_location):
        # 根据数据库中股票代码信息，拼接 获取乌龟量化数据的地址
        # 参数： stock_code  股票代码  600519
        # 参数： stock_exchange_location  股票上市地 sz或者sh
        # 返回： 乌龟量化数据的地址
        address = "https://androidinvest.com/stock/history/"+stock_exchange_location+stock_code
        return address


    def get_raw_web_content(self, stock_code, address):
        # 从乌龟量化获取数据


        # 从数据库中获取一个代理IP和假的文件头
        proxy_ip_address, fake_ua = disguise.Disguise().get_one_IP_UA()

        # 伪装，隐藏IP和文件头
        # 使用ProxyHandler处理器，Proxy代理
        # 注意此处必须使用'http'，不可使用'https',与parse_csindex_detail_json.py 有区别
        proxy_support = urllib.request.ProxyHandler({'http': 'http://' + proxy_ip_address["ip_address"]})
        # 通过urllib2.build_opener()方法使用这些代理Handler对象，创建自定义opener
        opener = urllib.request.build_opener(proxy_support)
        # 给用户代理添加User-Agent属性
        opener.addheaders = [('User-Agent', fake_ua["ua"])]
        response_content = ''
        try:
            # opener.open()方法发送请才使用自定义的代理
            response = opener.open(address)
            # 解析返回内容
            response_content = response.read()
            # 将返回内容解析成json结构
            #json_content = json.loads(response_content)
            #return (json_content)
            return response_content.decode()
        except urllib.error.HTTPError as e:
            # 日志记录
            msg = "HTTP Error "+ str(e.code) + " " + e.reason + " When get data from " + address
            custom_logger.CustomLogger().log_writter(msg, 'info')
            # 如果出现403错误，说明代理ip或者文件头有误，重新再运行一次
            if e.code == 403:
                return self.get_raw_web_content(stock_code,address)
            msg = "Run again to get " + address + " data "
            custom_logger.CustomLogger().log_writter(msg, 'info')
        except Exception as e:
            msg = e
            custom_logger.CustomLogger().log_writter(msg, 'info')


    def analyze_web_content(self, response_content):
        # 解析从乌龟量化获取到的内容
        # 参数： response_content 获取到的网站内容
        # 输出：解析之后，将有用的内容存入数据库

        soup = BeautifulSoup(response_content, 'lxml')
        raw_data_str = soup.find('script', type="text/javascript").get_text()
        raw_data_list = raw_data_str.split(";")
        # 提取数据结构并转为字典
        raw_data_dict = eval(raw_data_list[2][15:])
        # 1，3，5，10年，all全部年份 的每周 PE-TTM， 扣非PE-TTM， 前复权收盘价，日期， 数据
        # '1'，'3'，'5'，'10'，'all' 代表近X年
        # list_val1 ：PE-TTM,滚动市盈率；
        # list_val2 ：扣非PE-TTM，扣非滚动市盈率
        # list_price ： 收盘价前复权
        # list_date ： 日期, 按周
        # list_val1_30：PE-TTM 30% 机会值
        # list_val1_70：PE-TTM 70% 危险值
        # list_val2_30：扣非PE-TTM 30% 机会值
        # list_val2_70：扣非PE-TTM 70% 危险值
        # list_val1_p：PE-TTM 历史百分位
        # list_val2_p：扣非PE-TTM 历史百分位
        # 数据结构：  ：{'1': {
        #                       'list_val1': [37.76, 37.79,,],
        #                       'list_val2': [37.51, 37.55,,,,],
        #                       'list_price': [1215.78, 1217.06,,,],
        #                       'list_date': ['2019-11-14', '2019-11-21', '2019-11-28',,,],
        #                       'list_val1_30': [37.76, 37.77,,,,],
        #                       'list_val1_70': [37.76, 37.78,,,,],
        #                       'list_val2_30': [37.51, 37.52,,,,],
        #                       'list_val2_70': [37.51, 37.54,,,,],
        #                       'list_val1_p': [0.0, 50.0,,,,],
        #                       'list_val2_p': [0.0, 50.0,,,,],}
        #                '3':{}}
        return raw_data_dict


    def save_stocks_pe_into_db(self,raw_data_dict, recent_year=10):
        # 存储股票的 滚动市盈率PE-TTM，扣非市盈率non-recurring PE-TTM
        # param：raw_data_dict，从乌龟量化获取的生数据
        # param: recent_year 收集最近年份，默认最近10年
        # 输出：将数据存入数据库

        # 默认最近10年的数据
        recent_year_data = raw_data_dict[str(recent_year)]
        # PE-TTM
        PE_TTM_list = recent_year_data['list_val1']
        # 扣非PE-TTM
        PE_TTM_non_recurring_list = recent_year_data['list_val2']
        # 日期
        date_list = recent_year_data['list_date']

        # 从最近日期向前遍历, 先把最新日期的数据存入数据库
        # TODO 插入前，需要在观察乌龟量化的返回，检查是否在数据库中已存在，否再插入
        for i in range(len(date_list)-1, -1, -1):
            sql = "Insert INTO stocks_main_estimation_indexes_historical_data (stock_code, stock_name, date, pe_ttm, nonrecurring_pe_ttm) values ('%s', '%s', '%s', '%s', '%s') " % (self.stock_code, self.stock_name, date_list[i], PE_TTM_list[i], PE_TTM_non_recurring_list[i] )
            db_operator.DBOperator().operate("insert", "financial_data", sql)


if __name__ == '__main__':
    go = CollectStocksEstimationIndexes("600519", "中国茅台", "sh")
    #result = go.generate_web_address("600519", "sh")
    #print(result)
    response_content = go.get_raw_web_content('600519','https://androidinvest.com/stock/history/sh600519/')
    # print(result)
    # go.get_raw_web_content('600519', 'https://androidinvest.com/stock/history/sh600519/')
    raw_data_dict = go.analyze_web_content(response_content)
    print(raw_data_dict["10"])
    #go.save_stocks_pe_into_db(raw_data_dict)