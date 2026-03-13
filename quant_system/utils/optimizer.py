"""
工具模块 - 参数优化器
功能：
1. 网格搜索优化策略参数
2. 遗传算法优化（可选）
"""
import backtrader as bt
from itertools import product
from loguru import logger
import pandas as pd
import config


class ParameterOptimizer:
    """参数优化器"""

    def __init__(self, data, strategy_class, initial_cash=config.INITIAL_CASH):
        """
        初始化参数优化器
        :param data: Backtrader数据对象
        :param strategy_class: 策略类
        :param initial_cash: 初始资金
        """
        self.data = data
        self.strategy_class = strategy_class
        self.initial_cash = initial_cash
        self.results = []

        logger.info(f"参数优化器初始化 - 策略:{strategy_class.__name__}")

    def grid_search(self, param_grid):
        """
        网格搜索优化
        :param param_grid: 参数网格，如 {'fast_period': [5, 10], 'slow_period': [20, 30]}
        :return: 优化结果DataFrame
        """
        logger.info(f"开始网格搜索优化，参数空间: {param_grid}")

        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        total_combinations = len(param_combinations)
        logger.info(f"总共需要测试 {total_combinations} 组参数")

        # 遍历所有参数组合
        for idx, params in enumerate(param_combinations, 1):
            param_dict = dict(zip(param_names, params))

            logger.info(f"测试 [{idx}/{total_combinations}]: {param_dict}")

            # 运行回测
            result = self._run_single_backtest(param_dict)
            self.results.append(result)

        # 转换为DataFrame并排序
        results_df = pd.DataFrame(self.results)
        results_df = results_df.sort_values('total_return', ascending=False)

        logger.info("网格搜索完成")
        return results_df

    def _run_single_backtest(self, params):
        """
        运行单次回测
        :param params: 参数字典
        :return: 结果字典
        """
        cerebro = bt.Cerebro()
        cerebro.adddata(self.data)
        cerebro.broker.setcash(self.initial_cash)

        # 设置手续费和滑点
        cerebro.broker.setcommission(commission=config.COMMISSION_RATE)
        cerebro.broker.set_slippage_perc(config.SLIPPAGE_PERC)

        # 添加策略（关闭日志输出）
        cerebro.addstrategy(self.strategy_class, printlog=False, **params)

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 运行回测
        results = cerebro.run()
        strat = results[0]

        # 提取结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - self.initial_cash) / self.initial_cash * 100

        result_dict = params.copy()
        result_dict['final_value'] = final_value
        result_dict['total_return'] = total_return

        try:
            result_dict['sharpe_ratio'] = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
            result_dict['max_drawdown'] = strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0)

            trades = strat.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            result_dict['total_trades'] = total_trades
            result_dict['win_rate'] = (won_trades / total_trades * 100) if total_trades > 0 else 0

        except Exception as e:
            logger.warning(f"提取分析结果失败: {str(e)}")

        return result_dict

    def get_best_params(self, metric='total_return'):
        """
        获取最佳参数
        :param metric: 评价指标
        :return: 最佳参数字典
        """
        if not self.results:
            return None

        results_df = pd.DataFrame(self.results)
        best_row = results_df.loc[results_df[metric].idxmax()]

        return best_row.to_dict()


def optimize_strategy(symbol, strategy_class, param_grid, start_date=None, end_date=None):
    """
    快速优化函数
    :param symbol: 股票代码
    :param strategy_class: 策略类
    :param param_grid: 参数网格
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 优化结果DataFrame
    """
    from data.data_fetcher import AStockDataFetcher

    # 获取数据
    fetcher = AStockDataFetcher()
    df = fetcher.get_stock_hist(symbol, start_date, end_date)

    # 转换为Backtrader数据格式
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )

    # 优化
    optimizer = ParameterOptimizer(data, strategy_class)
    results = optimizer.grid_search(param_grid)

    return results


if __name__ == '__main__':
    print("参数优化模块 - 使用示例请参考主程序")
