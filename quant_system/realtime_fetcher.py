"""
改进的实时行情获取模块
使用多个数据源提高可靠性
"""
import akshare as ak
import pandas as pd
from datetime import datetime
from loguru import logger


class RealtimeQuoteFetcher:
    """实时行情获取器 - 多数据源"""

    def __init__(self):
        logger.info("实时行情获取器初始化")

    def get_realtime_quote(self, symbol):
        """
        获取实时行情 - 尝试多个数据源
        :param symbol: 股票代码
        :return: 实时行情字典
        """
        # 方法1: 尝试个股实时行情
        try:
            logger.info(f"尝试获取 {symbol} 实时行情 - 方法1")
            df = ak.stock_zh_a_spot_em()

            # 查找对应股票
            stock_data = df[df['代码'] == symbol]

            if not stock_data.empty:
                row = stock_data.iloc[0]
                result = {
                    '股票代码': symbol,
                    '股票名称': row['名称'],
                    '最新价': float(row['最新价']),
                    '涨跌幅': float(row['涨跌幅']),
                    '涨跌额': float(row['涨跌额']),
                    '成交量': float(row['成交量']),
                    '成交额': float(row['成交额']),
                    '今开': float(row['今开']),
                    '最高': float(row['最高']),
                    '最低': float(row['最低']),
                    '昨收': float(row['昨收']),
                    '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                logger.info(f"方法1成功: {symbol} 最新价 {result['最新价']}")
                return result
        except Exception as e:
            logger.warning(f"方法1失败: {str(e)}")

        # 方法2: 尝试分时行情
        try:
            logger.info(f"尝试获取 {symbol} 实时行情 - 方法2")
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1', adjust='')

            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                result = {
                    '股票代码': symbol,
                    '最新价': float(latest['收盘']),
                    '今开': float(latest['开盘']),
                    '最高': float(latest['最高']),
                    '最低': float(latest['最低']),
                    '成交量': float(latest['成交量']),
                    '成交额': float(latest['成交额']),
                    '更新时间': str(latest['时间'])
                }
                logger.info(f"方法2成功: {symbol} 最新价 {result['最新价']}")
                return result
        except Exception as e:
            logger.warning(f"方法2失败: {str(e)}")

        # 方法3: 使用最新日线数据
        try:
            logger.info(f"尝试获取 {symbol} 最新日线 - 方法3")
            df = ak.stock_zh_a_hist(symbol=symbol, period='daily', adjust='qfq')

            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest

                change = latest['收盘'] - prev['收盘']
                change_pct = (change / prev['收盘']) * 100

                result = {
                    '股票代码': symbol,
                    '最新价': float(latest['收盘']),
                    '涨跌幅': float(change_pct),
                    '涨跌额': float(change),
                    '今开': float(latest['开盘']),
                    '最高': float(latest['最高']),
                    '最低': float(latest['最低']),
                    '昨收': float(prev['收盘']),
                    '成交量': float(latest['成交量']),
                    '成交额': float(latest['成交额']),
                    '日期': str(latest['日期']),
                    '数据类型': '日线数据',
                    '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                logger.info(f"方法3成功: {symbol} 收盘价 {result['最新价']} (日线)")
                return result
        except Exception as e:
            logger.error(f"方法3失败: {str(e)}")

        logger.error(f"所有方法均失败，无法获取 {symbol} 行情")
        return None

    def is_trading_time(self):
        """
        判断当前是否为交易时间
        :return: True/False
        """
        now = datetime.now()

        # 周末不交易
        if now.weekday() >= 5:
            return False

        # 交易时间: 9:30-11:30, 13:00-15:00
        current_time = now.time()
        morning_start = datetime.strptime('09:30', '%H:%M').time()
        morning_end = datetime.strptime('11:30', '%H:%M').time()
        afternoon_start = datetime.strptime('13:00', '%H:%M').time()
        afternoon_end = datetime.strptime('15:00', '%H:%M').time()

        if morning_start <= current_time <= morning_end:
            return True
        if afternoon_start <= current_time <= afternoon_end:
            return True

        return False


# 测试代码
if __name__ == '__main__':
    fetcher = RealtimeQuoteFetcher()

    print("=" * 70)
    print("实时行情获取测试")
    print("=" * 70)

    # 测试是否为交易时间
    is_trading = fetcher.is_trading_time()
    print(f"\n当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"是否交易时间: {'是' if is_trading else '否'}")

    # 测试获取行情
    symbol = '601016'
    print(f"\n正在获取 {symbol} 行情...")
    print("-" * 70)

    quote = fetcher.get_realtime_quote(symbol)

    if quote:
        print("\n行情数据:")
        for key, value in quote.items():
            print(f"  {key}: {value}")
    else:
        print("\n获取失败")

    print("\n" + "=" * 70)
