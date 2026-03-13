"""
数据模块 - 基于 AkShare 获取 A 股数据
功能：
1. 获取股票历史行情数据
2. 获取实时行情数据
3. 获取财务数据
4. 数据清洗和缓存
"""
import akshare as ak
import pandas as pd
import os
from datetime import datetime, timedelta
from loguru import logger
import config


class AStockDataFetcher:
    """A股数据获取器"""

    def __init__(self, enable_cache=config.ENABLE_CACHE):
        """
        初始化数据获取器
        :param enable_cache: 是否启用缓存
        """
        self.enable_cache = enable_cache
        self.cache_dir = config.CACHE_DIR

        # 配置日志
        log_file = os.path.join(config.LOG_DIR, 'data_fetcher.log')
        logger.add(log_file, rotation=config.LOG_ROTATION,
                   retention=config.LOG_RETENTION, level=config.LOG_LEVEL)
        logger.info("数据获取器初始化完成")

    def get_stock_hist(self, symbol, start_date=None, end_date=None,
                       period='daily', adjust='qfq'):
        """
        获取股票历史行情数据
        :param symbol: 股票代码，如 '000001'
        :param start_date: 开始日期，格式 'YYYYMMDD'
        :param end_date: 结束日期，格式 'YYYYMMDD'
        :param period: 周期 daily/weekly/monthly
        :param adjust: 复权类型 qfq前复权/hfq后复权/None不复权
        :return: DataFrame
        """
        symbol = config.format_stock_code(symbol)

        # 设置默认日期
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = config.DEFAULT_START_DATE

        # 检查缓存
        cache_file = self._get_cache_filename(symbol, start_date, end_date, period, adjust)
        if self.enable_cache and self._is_cache_valid(cache_file):
            logger.info(f"从缓存加载数据: {symbol}")
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)

        try:
            logger.info(f"从AkShare获取数据: {symbol}, {start_date} - {end_date}")
            df = ak.stock_zh_a_hist(symbol=symbol, period=period,
                                    start_date=start_date, end_date=end_date,
                                    adjust=adjust)

            # 数据清洗
            df = self._clean_data(df)

            # 保存缓存
            if self.enable_cache:
                df.to_csv(cache_file)
                logger.info(f"数据已缓存: {cache_file}")

            return df

        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {str(e)}")
            raise

    def get_realtime_quote(self, symbol):
        """
        获取股票实时行情
        :param symbol: 股票代码
        :return: Series 包含现价、涨跌幅、成交量等
        """
        try:
            symbol = config.format_stock_code(symbol)
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == symbol]

            if stock_data.empty:
                logger.warning(f"未找到股票 {symbol} 的实时数据")
                return None

            result = stock_data.iloc[0]
            logger.info(f"获取实时行情: {symbol}, 现价: {result['最新价']}")
            return result

        except Exception as e:
            logger.error(f"获取实时行情失败 {symbol}: {str(e)}")
            return None

    def get_stock_financial(self, symbol):
        """
        获取股票财务数据
        :param symbol: 股票代码
        :return: DataFrame 包含PE、PB、净利润等
        """
        try:
            symbol = config.format_stock_code(symbol)

            # 获取个股信息（包含PE、PB等）
            df = ak.stock_individual_info_em(symbol=symbol)

            logger.info(f"获取财务数据: {symbol}")
            return df

        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {str(e)}")
            return None

    def get_stock_list(self):
        """
        获取A股股票列表
        :return: DataFrame 包含股票代码、名称等
        """
        try:
            df = ak.stock_zh_a_spot_em()
            logger.info(f"获取股票列表，共 {len(df)} 只股票")
            return df[['代码', '名称', '最新价', '涨跌幅', '换手率', '市盈率-动态']]

        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return None

    def _clean_data(self, df):
        """
        数据清洗
        :param df: 原始数据
        :return: 清洗后的数据
        """
        if df is None or df.empty:
            return df

        # 重命名列为英文（适配Backtrader）
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }

        df = df.rename(columns=column_mapping)

        # 设置日期为索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # 处理缺失值
        df = df.fillna(method='ffill')  # 前向填充

        # 删除异常值（如成交量为0的数据）
        if 'volume' in df.columns:
            df = df[df['volume'] > 0]

        # 确保数据类型正确
        numeric_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        logger.debug(f"数据清洗完成，共 {len(df)} 条记录")
        return df

    def _get_cache_filename(self, symbol, start_date, end_date, period, adjust):
        """生成缓存文件名"""
        filename = f"{symbol}_{start_date}_{end_date}_{period}_{adjust}.csv"
        return os.path.join(self.cache_dir, filename)

    def _is_cache_valid(self, cache_file):
        """检查缓存是否有效"""
        if not os.path.exists(cache_file):
            return False

        # 检查缓存是否过期
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        expire_time = datetime.now() - timedelta(days=config.CACHE_EXPIRE_DAYS)

        return file_time > expire_time


# 便捷函数
def get_stock_data(symbol, start_date=None, end_date=None):
    """
    快速获取股票数据的便捷函数
    :param symbol: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: DataFrame
    """
    fetcher = AStockDataFetcher()
    return fetcher.get_stock_hist(symbol, start_date, end_date)


if __name__ == '__main__':
    # 测试代码
    fetcher = AStockDataFetcher()

    # 测试获取历史数据
    df = fetcher.get_stock_hist('000001', start_date='20230101', end_date='20231231')
    print("历史数据:")
    print(df.head())
    print(f"\n数据形状: {df.shape}")

    # 测试获取实时行情
    quote = fetcher.get_realtime_quote('000001')
    print("\n实时行情:")
    print(quote)
