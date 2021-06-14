import threading
import time

import sys
sys.path.append("..")
import database.db_operator as db_operator
import target_pool.read_collect_target_fund as read_collect_target_fund
import data_miner.common_index_operator as index_operator
import log.custom_logger as custom_logger


class CalculateIndexHistoricalEstimations:
    # 根据最新的指数成分和股票历史估值信息，计算指数在历史上每一天的估值情况
    # 运行频率：每天收盘后

    def __init__(self):

        # 最大的计算线程数
        self.max_threading_connections = 18
        # 限制线程数量
        self.threading_pool = threading.Semaphore(self.max_threading_connections)

    def get_all_date(self):
        # 获取数据库中所有的日期
        selecting_sql = "SELECT DISTINCT date FROM stocks_main_estimation_indexes_historical_data order by date desc "
        all_date = db_operator.DBOperator().select_all("financial_data", selecting_sql)
        return all_date

    def cal_one_index_estimation_in_a_special_day(self, index_constitute_stocks, index_code, index_name, day):
        # 计算某一个指数在特定一天的估值
        # param: index_constitute_stocks, 指数的成分股代码，名称，权重， 如 [{'global_stock_code': '000568.XSHE',
        #       'stock_code': '000568', 'stock_name': '泸州老窖', 'weight': Decimal('17.0050')}, {'global_stock_code':
        #       '000596.XSHE', 'stock_code': '000596', 'stock_name': '古井贡酒', 'weight': Decimal('3.1370')}, ，，，]
        # param: index_code，指数代码，如 399997.XSHE
        # param: index_name，指数名称，如 中证白酒
        # param: day， 日期， 如 "2020-01-10"

        # 指数滚动市盈率
        index_pe_ttm = 0
        # 指数滚动市盈率有效权重
        index_pe_ttm_effective_weight = 0
        # 指数扣非滚动市盈率
        index_pe_ttm_nonrecurring = 0
        # 指数扣非滚动市盈率有效权重
        index_pe_ttm_nonrecurring_effective_weight = 0
        # 指数市净率
        index_pb = 0
        # 指数市净率有效权重
        index_pb_effective_weight = 0
        # 指数扣商誉市净率
        index_pb_wo_gw = 0
        # 指数扣商誉市净率有效权重
        index_pb_wo_gw_effective_weight = 0
        # 指数滚动市销率
        index_ps_ttm = 0
        # 指数滚动市销率有效权重
        index_ps_ttm_effective_weight = 0
        # 指数滚动市现率
        index_pcf_ttm = 0
        # 指数滚动市现率有效权重
        index_pcf_ttm_effective_weight = 0
        # 指数股息率
        index_dividend_yield = 0
        # 指数股息率
        index_dividend_yield_effective_weight = 0

        # 遍历指数成分股
        for stock_info in index_constitute_stocks:
            stock_code = stock_info['stock_code']
            stock_name = stock_info['stock_name']
            stock_weight = stock_info['weight']
            # 获取某一股票的历史某一天的估值信息
            selecting_sql = "SELECT * FROM stocks_main_estimation_indexes_historical_data WHERE stock_code = '%s' and date = '%s'" % (
                stock_code, day)
            one_stock_special_day_estimation_info = db_operator.DBOperator().select_one("financial_data", selecting_sql)
            # 如果这一股票，当天有估值数据
            if one_stock_special_day_estimation_info:
                # 当指标为正数时，累加指数指标值和有效权重
                # 当指标为复数时，不累加指数指标值和有效权重

                stock_pe_ttm = one_stock_special_day_estimation_info["pe_ttm"]
                if stock_pe_ttm >= 0:
                    index_pe_ttm += stock_pe_ttm * stock_weight
                    index_pe_ttm_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 滚动市盈率pe_ttm为负， 数值为" + \
                          str(stock_pe_ttm) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_pe_ttm_nonrecurring = one_stock_special_day_estimation_info["pe_ttm_nonrecurring"]
                if stock_pe_ttm_nonrecurring >= 0:
                    index_pe_ttm_nonrecurring += stock_pe_ttm_nonrecurring * stock_weight
                    index_pe_ttm_nonrecurring_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + \
                          " 扣非滚动市盈率pe_ttm_nonrecurring为负， 数值为" + \
                          str(stock_pe_ttm_nonrecurring) + "; 该股票在指数 " + \
                          index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_pb = one_stock_special_day_estimation_info["pb"]
                if stock_pb >= 0:
                    index_pb += stock_pb * stock_weight
                    index_pb_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 市净率pb为负， 数值为" + \
                          str(stock_pb) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_pb_wo_gw = one_stock_special_day_estimation_info["pb_wo_gw"]
                if stock_pb_wo_gw >= 0:
                    index_ps_ttm += stock_pb_wo_gw * stock_weight
                    index_pb_wo_gw_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 扣商誉市净率pb_wo_gw为负， 数值为" + \
                          str(stock_pb_wo_gw) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_ps_ttm = one_stock_special_day_estimation_info["ps_ttm"]
                if stock_ps_ttm >= 0:
                    index_ps_ttm += stock_ps_ttm * stock_weight
                    index_ps_ttm_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 滚动市销率ps_ttm为负， 数值为" + \
                          str(stock_ps_ttm) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_pcf_ttm = one_stock_special_day_estimation_info["pcf_ttm"]
                if stock_pcf_ttm >= 0:
                    index_pcf_ttm += stock_pcf_ttm * stock_weight
                    index_pcf_ttm_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 滚动市现率pcf_ttm为负， 数值为" + \
                          str(stock_pcf_ttm) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')

                stock_dividend_yield = one_stock_special_day_estimation_info["dividend_yield"]
                if stock_dividend_yield >= 0:
                    index_dividend_yield += stock_dividend_yield * stock_weight
                    index_dividend_yield_effective_weight += stock_weight
                else:
                    # 日志记录
                    msg = stock_code + " " + stock_name + " " + "在 " + day + " 股息率dividend_yield为负， 数值为" + \
                          str(stock_dividend_yield) + "; 该股票在指数 " + index_code + " " + index_name + "中的权重为 " \
                          + str(stock_weight)
                    custom_logger.CustomLogger().log_writter(msg, 'info')
            else:
                # 日志记录
                msg = stock_code + " " + stock_name + " " + "在 " + day + " 无任何估值数据，当前在 " + \
                      index_code + " " + index_name + "中的权重为 " + str(stock_weight)
                custom_logger.CustomLogger().log_writter(msg, 'info')
                continue

        # 各指标仅保留小数点后4位
        index_pe_ttm = round(float(index_pe_ttm) / 100 / float(index_pe_ttm_effective_weight / 100), 4)
        index_pe_ttm_nonrecurring = round(
            float(index_pe_ttm_nonrecurring) / 100 / float(index_pe_ttm_nonrecurring_effective_weight / 100), 4)
        index_pb = round(float(index_pb) / 100 / float(index_pb_effective_weight / 100), 4)
        index_pb_wo_gw = round(float(index_pb_wo_gw) / 100 / float(index_pb_wo_gw_effective_weight / 100), 4)
        index_ps_ttm = round(float(index_ps_ttm) / 100 / float(index_ps_ttm_effective_weight / 100), 4)
        index_pcf_ttm = round(float(index_pcf_ttm) / 100 / float(index_pcf_ttm_effective_weight / 100), 4)
        index_dividend_yield = round(
            float(index_dividend_yield) / 100 / float(index_dividend_yield_effective_weight / 100), 4)

        # 存入数据库
        inserting_sql = "INSERT INTO index_components_historical_estimations " \
                        "(index_code, index_name, historical_date, pe_ttm, pe_ttm_effective_weight, pe_ttm_nonrecurring, pe_ttm_nonrecurring_effective_weight, pb, pb_effective_weight, " \
                        "pb_wo_gw, pb_wo_gw_effective_weight, ps_ttm, ps_ttm_effective_weight, pcf_ttm, pcf_ttm_effective_weight, dividend_yield, dividend_yield_effective_weight) VALUES " \
                        "('%s', '%s', '%s', %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f) " % (
                            index_code, index_name, day,
                            index_pe_ttm, index_pe_ttm_effective_weight,
                            index_pe_ttm_nonrecurring, index_pe_ttm_nonrecurring_effective_weight, index_pb,
                            index_pb_effective_weight,
                            index_pb_wo_gw, index_pb_wo_gw_effective_weight, index_ps_ttm,
                            index_ps_ttm_effective_weight,
                            index_pcf_ttm, index_pcf_ttm_effective_weight, index_dividend_yield,
                            index_dividend_yield_effective_weight)
        db_operator.DBOperator().operate("insert", "aggregated_data", inserting_sql)
        # 释放线程
        self.threading_pool.release()

    def cal_all_index_historical_estimation_single_thread(self):
        # 单线程计算所有指数的历史上每一交易日的估值

        # todo 非常重要 如果指数有变化（成分股，权重相对于上个月有变化），就需要重新计算； 没有变化的指数，就不需要重新计算
        # 重新计算前，清空也有记录
        truncating_sql = "TRUNCATE TABLE index_components_historical_estimations"
        # 删除记录
        db_operator.DBOperator().operate("delete", "aggregated_data", truncating_sql)

        # 获取需要采集的目标指数
        # 如{ '399997.XSHE': '中证白酒', '399965.XSHE': '中证800地产', ,,,}
        target_indexes = read_collect_target_fund.ReadCollectTargetFund().get_indexes_and_their_names()
        # target_indexes = {'399997.XSHE': '中证白酒'}
        # 遍历目标指数
        for index_code in target_indexes:

            # 指数名称
            index_name = target_indexes[index_code]
            # 获取指数最新的成分股和权重
            index_constitute_stocks = index_operator.IndexOperator().get_index_constitute_stocks(index_code)
            # 获取数据库中所有的日期
            days = self.get_all_date()
            # 按天统计指数的估值
            for day in days:
                self.cal_one_index_estimation_in_a_special_day(index_constitute_stocks, index_code, index_name, str(day["date"]))

    def cal_all_index_historical_estimation_multi_threads(self):
        # 多线程计算所有指数的历史上每一交易日的估值

        # todo 非常重要 如果指数有变化（成分股，权重相对于上个月有变化），就需要重新计算； 没有变化的指数，就不需要重新计算
        # todo 多进程进程计算，提高效率

        # 重新计算前，清空也有记录
        truncating_sql = "TRUNCATE TABLE index_components_historical_estimations"
        # 删除记录
        db_operator.DBOperator().operate("delete", "aggregated_data", truncating_sql)

        # 获取需要采集的目标指数
        # 如{ '399997.XSHE': '中证白酒', '399965.XSHE': '中证800地产', ,,,}
        target_indexes = read_collect_target_fund.ReadCollectTargetFund().get_indexes_and_their_names()
        #target_indexes = {'399997.XSHE': '中证白酒'}
        # 遍历目标指数
        for index_code in target_indexes:
            # 指数名称
            index_name = target_indexes[index_code]
            # 获取指数最新的成分股和权重
            index_constitute_stocks = index_operator.IndexOperator().get_index_constitute_stocks(index_code)
            # 获取数据库中所有的日期
            days = self.get_all_date()
            # 按天统计指数的估值
            for day in days:
                # 限制线程数
                self.threading_pool.acquire()
                # 启动线程
                threading.Thread(target=self.cal_one_index_estimation_in_a_special_day,
                                                  kwargs={"index_constitute_stocks": index_constitute_stocks,
                                                          "index_code": index_code, "index_name": index_name,
                                                          "day": str(day["date"])}).start()
        # 日志记录
        msg = " 计算并已储存了所有目标指数从2010-01-02至今收盘后的估值信息"
        custom_logger.CustomLogger().log_writter(msg, 'info')

    def cal_one_index_today_estimation(self, target_indexes, index_code, today):
        # 计算单个指数今天收盘后的估值
        # param: target_indexes, 需要采集的目标指数集
        # param: index_code, 指数代码，如 399997.XSHE
        # param: today, 今天日期，如 2021-05-28

        # 指数名称
        index_name = target_indexes[index_code]
        # 获取指数最新的成分股和权重
        index_constitute_stocks = index_operator.IndexOperator().get_index_constitute_stocks(index_code)
        # 计算今天的估值
        self.cal_one_index_estimation_in_a_special_day(index_constitute_stocks, index_code, index_name, today)

    def cal_all_index_today_estimation(self):
        # 多线程计算所有指数今天收盘后的估值

        # 获取当前日期
        today = time.strftime("%Y-%m-%d", time.localtime())
        #today = "2021-05-28"

        # 获取需要采集的目标指数
        # 如{ '399997.XSHE': '中证白酒', '399965.XSHE': '中证800地产', ,,,}
        target_indexes = read_collect_target_fund.ReadCollectTargetFund().get_indexes_and_their_names()
        # target_indexes = {'399997.XSHE': '中证白酒'}
        # 遍历目标指数
        for index_code in target_indexes:
            # 限制线程数
            self.threading_pool.acquire()
            # 启动线程
            threading.Thread(target=self.cal_one_index_today_estimation,
                             args=(target_indexes,index_code,today)).start()
        # 日志记录
        msg = " 计算并已储存了今天 " + today + " 所有目标指数收盘后的估值信息"
        custom_logger.CustomLogger().log_writter(msg, 'info')


if __name__ == '__main__':
    go = CalculateIndexHistoricalEstimations()
    #go.cal_index_everyday_estimation_single_thread()
    go.cal_all_index_historical_estimation_multi_threads()
    #go.cal_all_index_today_estimation()