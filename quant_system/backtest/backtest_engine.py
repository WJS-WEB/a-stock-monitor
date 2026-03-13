"""
回测模块 - 基于 Backtrader 的回测引擎
功能：
1. 集成数据和策略
2. 执行回测
3. 计算绩效指标
4. 可视化结果
"""
import backtrader as bt
import pandas as pd
from datetime import datetime
from loguru import logger
import matplotlib.pyplot as plt
import os
import config
from data.data_fetcher import AStockDataFetcher


class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_cash=config.INITIAL_CASH):
        """
        初始化回测引擎
        :param initial_cash: 初始资金
        """
        self.cerebro = bt.Cerebro()
        self.initial_cash = initial_cash
        self.cerebro.broker.setcash(initial_cash)

        # 设置手续费
        self.cerebro.broker.setcommission(
            commission=config.COMMISSION_RATE,
            stocklike=True,
            percabs=False  # 按比例收取
        )

        # 设置滑点
        self.cerebro.broker.set_slippage_perc(config.SLIPPAGE_PERC)

        # 添加分析器
        self._add_analyzers()

        # 配置日志
        log_file = os.path.join(config.LOG_DIR, 'backtest.log')
        logger.add(log_file, rotation=config.LOG_ROTATION,
                   retention=config.LOG_RETENTION, level=config.LOG_LEVEL)

        logger.info(f"回测引擎初始化完成 - 初始资金: {initial_cash}")

    def add_data(self, symbol, start_date=None, end_date=None):
        """
        添加股票数据
        :param symbol: 股票代码
        :param start_date: 开始日期
        :param end_date: 结束日期
        """
        try:
            # 获取数据
            fetcher = AStockDataFetcher()
            df = fetcher.get_stock_hist(symbol, start_date, end_date)

            if df is None or df.empty:
                logger.error(f"无法获取股票数据: {symbol}")
                return False

            # 转换为Backtrader数据格式
            data = bt.feeds.PandasData(
                dataname=df,
                datetime=None,  # 使用索引作为日期
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1
            )

            self.cerebro.adddata(data, name=symbol)
            logger.info(f"添加数据成功: {symbol}, 数据量: {len(df)}")
            return True

        except Exception as e:
            logger.error(f"添加数据失败 {symbol}: {str(e)}")
            return False

    def add_strategy(self, strategy_class, **kwargs):
        """
        添加策略
        :param strategy_class: 策略类
        :param kwargs: 策略参数
        """
        self.cerebro.addstrategy(strategy_class, **kwargs)
        logger.info(f"添加策略: {strategy_class.__name__}")

    def run(self):
        """
        运行回测
        :return: 回测结果字典
        """
        logger.info("=" * 50)
        logger.info("开始回测")
        logger.info(f"初始资金: {self.initial_cash:.2f}")

        # 运行回测
        results = self.cerebro.run()
        strat = results[0]

        # 获取最终资金
        final_value = self.cerebro.broker.getvalue()
        total_return = (final_value - self.initial_cash) / self.initial_cash * 100

        logger.info("=" * 50)
        logger.info("回测完成")
        logger.info(f"最终资金: {final_value:.2f}")
        logger.info(f"总收益率: {total_return:.2f}%")

        # 提取分析结果
        results_dict = self._extract_results(strat, final_value, total_return)

        return results_dict

    def plot(self, save_path=None):
        """
        绘制回测结果
        :param save_path: 保存路径，如果为None则显示
        """
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            fig = self.cerebro.plot(style='candlestick', barup='red', bardown='green')[0][0]

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"回测图表已保存: {save_path}")
            else:
                plt.show()

        except Exception as e:
            logger.error(f"绘图失败: {str(e)}")

    def _add_analyzers(self):
        """添加分析器"""
        # 收益分析
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        # 夏普比率
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        # 回撤分析
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        # 交易分析
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        # 年化收益
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')

    def _extract_results(self, strat, final_value, total_return):
        """
        提取回测结果
        :param strat: 策略实例
        :param final_value: 最终资金
        :param total_return: 总收益率
        :return: 结果字典
        """
        results = {
            'initial_cash': self.initial_cash,
            'final_value': final_value,
            'total_return': total_return,
        }

        # 提取各分析器结果
        try:
            # 夏普比率
            sharpe = strat.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe.get('sharperatio', None)
            results['sharpe_ratio'] = sharpe_ratio if sharpe_ratio is not None else 0

            # 回撤
            drawdown = strat.analyzers.drawdown.get_analysis()
            results['max_drawdown'] = drawdown.get('max', {}).get('drawdown', 0)
            results['max_drawdown_period'] = drawdown.get('max', {}).get('len', 0)

            # 交易分析
            trades = strat.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)

            results['total_trades'] = total_trades
            results['won_trades'] = won_trades
            results['lost_trades'] = lost_trades
            results['win_rate'] = (won_trades / total_trades * 100) if total_trades > 0 else 0

            # 盈亏比
            avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
            avg_loss = abs(trades.get('lost', {}).get('pnl', {}).get('average', 0))
            results['profit_loss_ratio'] = (avg_win / avg_loss) if avg_loss > 0 else 0

            # 年化收益
            annual_returns = strat.analyzers.annual_return.get_analysis()
            if annual_returns:
                avg_annual_return = sum(annual_returns.values()) / len(annual_returns)
                results['annual_return'] = avg_annual_return
            else:
                results['annual_return'] = 0

        except Exception as e:
            logger.error(f"提取分析结果失败: {str(e)}")

        return results

    def print_results(self, results):
        """
        打印回测结果
        :param results: 结果字典
        """
        print("\n" + "=" * 60)
        print("回测结果汇总".center(60))
        print("=" * 60)
        print(f"初始资金:        {results['initial_cash']:>15,.2f} 元")
        print(f"最终资金:        {results['final_value']:>15,.2f} 元")
        print(f"总收益率:        {results['total_return']:>15.2f} %")
        print(f"年化收益率:      {results.get('annual_return', 0):>15.2f} %")
        print(f"最大回撤:        {results.get('max_drawdown', 0):>15.2f} %")
        print(f"夏普比率:        {results.get('sharpe_ratio', 0):>15.2f}")
        print("-" * 60)
        print(f"总交易次数:      {results.get('total_trades', 0):>15}")
        print(f"盈利次数:        {results.get('won_trades', 0):>15}")
        print(f"亏损次数:        {results.get('lost_trades', 0):>15}")
        print(f"胜率:            {results.get('win_rate', 0):>15.2f} %")
        print(f"盈亏比:          {results.get('profit_loss_ratio', 0):>15.2f}")
        print("=" * 60 + "\n")


def quick_backtest(symbol, strategy_class, start_date=None, end_date=None, **strategy_params):
    """
    快速回测函数
    :param symbol: 股票代码
    :param strategy_class: 策略类
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param strategy_params: 策略参数
    :return: 回测结果
    """
    engine = BacktestEngine()
    engine.add_data(symbol, start_date, end_date)
    engine.add_strategy(strategy_class, **strategy_params)
    results = engine.run()
    engine.print_results(results)
    return results


if __name__ == '__main__':
    print("回测模块 - 使用示例请参考主程序")
