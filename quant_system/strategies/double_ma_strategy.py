"""
策略模块 - 双均线交叉策略
功能：
1. 5日均线上穿20日均线买入
2. 5日均线下穿20日均线卖出
3. 支持止损止盈
4. 仓位管理
"""
import backtrader as bt
from loguru import logger
import config


class DoubleMAStrategy(bt.Strategy):
    """双均线交叉策略"""

    params = (
        ('fast_period', config.MA_FAST_PERIOD),  # 快速均线周期
        ('slow_period', config.MA_SLOW_PERIOD),  # 慢速均线周期
        ('stop_loss', config.STOP_LOSS_PCT),  # 止损比例
        ('take_profit', config.TAKE_PROFIT_PCT),  # 止盈比例
        ('position_size', config.MAX_POSITION_PCT),  # 单次开仓比例
        ('printlog', True),  # 是否打印日志
    )

    def __init__(self):
        """初始化策略"""
        # 保存收盘价
        self.dataclose = self.datas[0].close

        # 计算均线指标
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)

        # 均线交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # 记录订单和买入价格
        self.order = None
        self.buyprice = None
        self.buycomm = None

        logger.info(f"策略初始化完成 - 快线周期:{self.params.fast_period}, "
                   f"慢线周期:{self.params.slow_period}")

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/已接受 - 无需操作
            return

        # 订单完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行, 价格: {order.executed.price:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    f'卖出执行, 价格: {order.executed.price:.2f}, '
                    f'成本: {order.executed.value:.2f}, '
                    f'手续费: {order.executed.comm:.2f}'
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 重置订单
        self.order = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return

        self.log(f'交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')

    def next(self):
        """策略主逻辑 - 每个bar调用一次"""
        # 记录当前收盘价
        self.log(f'收盘价: {self.dataclose[0]:.2f}')

        # 如果有订单在处理中，不操作
        if self.order:
            return

        # 检查是否持仓
        if not self.position:
            # 没有持仓，检查买入信号
            if self.crossover > 0:  # 金叉：快线上穿慢线
                self.log(f'买入信号 - 快线:{self.fast_ma[0]:.2f}, 慢线:{self.slow_ma[0]:.2f}')

                # 计算买入数量（按资金比例）
                cash = self.broker.getcash()
                size = int((cash * self.params.position_size) / self.dataclose[0] / 100) * 100

                if size > 0:
                    self.log(f'创建买单, 数量: {size}')
                    self.order = self.buy(size=size)

        else:
            # 已持仓，检查卖出信号
            # 1. 均线死叉
            if self.crossover < 0:
                self.log(f'卖出信号(死叉) - 快线:{self.fast_ma[0]:.2f}, 慢线:{self.slow_ma[0]:.2f}')
                self.log(f'创建卖单, 数量: {self.position.size}')
                self.order = self.sell(size=self.position.size)

            # 2. 止损
            elif self.buyprice and (self.dataclose[0] < self.buyprice * (1 - self.params.stop_loss)):
                loss_pct = (self.dataclose[0] - self.buyprice) / self.buyprice * 100
                self.log(f'止损卖出 - 当前价:{self.dataclose[0]:.2f}, '
                        f'买入价:{self.buyprice:.2f}, 亏损:{loss_pct:.2f}%')
                self.order = self.sell(size=self.position.size)

            # 3. 止盈
            elif self.buyprice and (self.dataclose[0] > self.buyprice * (1 + self.params.take_profit)):
                profit_pct = (self.dataclose[0] - self.buyprice) / self.buyprice * 100
                self.log(f'止盈卖出 - 当前价:{self.dataclose[0]:.2f}, '
                        f'买入价:{self.buyprice:.2f}, 盈利:{profit_pct:.2f}%')
                self.order = self.sell(size=self.position.size)

    def log(self, txt, dt=None):
        """日志输出"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
            logger.debug(f'{dt.isoformat()} {txt}')

    def stop(self):
        """策略结束时调用"""
        self.log(f'策略结束 - 快线周期:{self.params.fast_period}, '
                f'慢线周期:{self.params.slow_period}, '
                f'最终资金: {self.broker.getvalue():.2f}', dt=None)


class MACDStrategy(bt.Strategy):
    """MACD策略示例"""

    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('printlog', True),
    )

    def __init__(self):
        """初始化MACD策略"""
        self.dataclose = self.datas[0].close

        # MACD指标
        self.macd = bt.indicators.MACD(
            self.datas[0],
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )

        # MACD交叉信号
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        self.order = None
        logger.info("MACD策略初始化完成")

    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}')
        self.order = None

    def next(self):
        """策略逻辑"""
        if self.order:
            return

        if not self.position:
            # MACD金叉买入
            if self.crossover > 0:
                self.log(f'MACD金叉买入信号')
                cash = self.broker.getcash()
                size = int((cash * 0.95) / self.dataclose[0] / 100) * 100
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            # MACD死叉卖出
            if self.crossover < 0:
                self.log(f'MACD死叉卖出信号')
                self.order = self.sell(size=self.position.size)

    def log(self, txt, dt=None):
        """日志"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')


if __name__ == '__main__':
    print("策略模块 - 使用示例请参考 backtest 模块")
