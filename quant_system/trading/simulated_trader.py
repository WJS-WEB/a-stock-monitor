"""
交易模块 - 模拟交易和风险控制
功能：
1. 实时信号生成
2. 模拟下单
3. 仓位管理
4. 风险控制
"""
import pandas as pd
from datetime import datetime
from loguru import logger
import os
import config
from data.data_fetcher import AStockDataFetcher


class RiskController:
    """风险控制器"""

    def __init__(self, total_cash, max_position_pct=config.MAX_POSITION_PCT,
                 max_total_position_pct=config.MAX_TOTAL_POSITION_PCT):
        """
        初始化风险控制器
        :param total_cash: 总资金
        :param max_position_pct: 单只股票最大仓位比例
        :param max_total_position_pct: 总仓位上限比例
        """
        self.total_cash = total_cash
        self.max_position_pct = max_position_pct
        self.max_total_position_pct = max_total_position_pct
        self.positions = {}  # 持仓信息 {symbol: {'size': 数量, 'price': 成本价}}
        self.available_cash = total_cash

        logger.info(f"风险控制器初始化 - 总资金:{total_cash}, "
                   f"单票上限:{max_position_pct*100}%, 总仓位上限:{max_total_position_pct*100}%")

    def check_buy_order(self, symbol, price, size):
        """
        检查买入订单是否符合风险控制
        :param symbol: 股票代码
        :param price: 买入价格
        :param size: 买入数量
        :return: (是否允许, 调整后的数量, 原因)
        """
        order_value = price * size

        # 检查可用资金
        if order_value > self.available_cash:
            max_size = int(self.available_cash / price / 100) * 100
            return False, max_size, f"可用资金不足，最多可买{max_size}股"

        # 检查单票仓位限制
        max_single_value = self.total_cash * self.max_position_pct
        if order_value > max_single_value:
            max_size = int(max_single_value / price / 100) * 100
            return False, max_size, f"超过单票仓位限制，最多可买{max_size}股"

        # 检查总仓位限制
        current_position_value = sum(
            pos['size'] * pos['price'] for pos in self.positions.values()
        )
        max_total_value = self.total_cash * self.max_total_position_pct

        if current_position_value + order_value > max_total_value:
            remaining_value = max_total_value - current_position_value
            max_size = int(remaining_value / price / 100) * 100
            return False, max_size, f"超过总仓位限制，最多可买{max_size}股"

        return True, size, "通过风险检查"

    def update_position(self, symbol, action, price, size):
        """
        更新持仓信息
        :param symbol: 股票代码
        :param action: 'buy' 或 'sell'
        :param price: 价格
        :param size: 数量
        """
        if action == 'buy':
            if symbol in self.positions:
                # 加仓
                old_size = self.positions[symbol]['size']
                old_price = self.positions[symbol]['price']
                new_size = old_size + size
                new_price = (old_size * old_price + size * price) / new_size
                self.positions[symbol] = {'size': new_size, 'price': new_price}
            else:
                # 新建仓位
                self.positions[symbol] = {'size': size, 'price': price}

            self.available_cash -= price * size
            logger.info(f"买入更新 - {symbol}, 数量:{size}, 价格:{price:.2f}, "
                       f"剩余资金:{self.available_cash:.2f}")

        elif action == 'sell':
            if symbol in self.positions:
                self.positions[symbol]['size'] -= size
                if self.positions[symbol]['size'] <= 0:
                    del self.positions[symbol]

                self.available_cash += price * size
                logger.info(f"卖出更新 - {symbol}, 数量:{size}, 价格:{price:.2f}, "
                           f"剩余资金:{self.available_cash:.2f}")

    def check_stop_loss(self, symbol, current_price, stop_loss_pct=config.STOP_LOSS_PCT):
        """
        检查是否触发止损
        :param symbol: 股票代码
        :param current_price: 当前价格
        :param stop_loss_pct: 止损比例
        :return: (是否止损, 亏损比例)
        """
        if symbol not in self.positions:
            return False, 0

        cost_price = self.positions[symbol]['price']
        loss_pct = (current_price - cost_price) / cost_price

        if loss_pct <= -stop_loss_pct:
            return True, loss_pct

        return False, loss_pct

    def get_position_info(self):
        """获取持仓信息"""
        return self.positions.copy()

    def get_total_value(self, current_prices):
        """
        计算总资产
        :param current_prices: 当前价格字典 {symbol: price}
        :return: 总资产
        """
        position_value = sum(
            pos['size'] * current_prices.get(symbol, pos['price'])
            for symbol, pos in self.positions.items()
        )
        return self.available_cash + position_value


class SimulatedTrader:
    """模拟交易器"""

    def __init__(self, initial_cash=config.INITIAL_CASH):
        """
        初始化模拟交易器
        :param initial_cash: 初始资金
        """
        self.risk_controller = RiskController(initial_cash)
        self.data_fetcher = AStockDataFetcher()
        self.trade_history = []  # 交易历史

        # 配置日志
        log_file = os.path.join(config.LOG_DIR, 'trading.log')
        logger.add(log_file, rotation=config.LOG_ROTATION,
                   retention=config.LOG_RETENTION, level=config.LOG_LEVEL)

        logger.info(f"模拟交易器初始化完成 - 初始资金:{initial_cash}")

    def generate_signal(self, symbol, strategy_type='double_ma'):
        """
        生成交易信号
        :param symbol: 股票代码
        :param strategy_type: 策略类型
        :return: 信号字典 {'action': 'buy'/'sell'/'hold', 'reason': 原因}
        """
        try:
            # 获取最近数据
            df = self.data_fetcher.get_stock_hist(
                symbol,
                start_date=(datetime.now() - pd.Timedelta(days=100)).strftime('%Y%m%d')
            )

            if df is None or len(df) < 20:
                return {'action': 'hold', 'reason': '数据不足'}

            # 双均线策略信号
            if strategy_type == 'double_ma':
                df['ma5'] = df['close'].rolling(window=5).mean()
                df['ma20'] = df['close'].rolling(window=20).mean()

                latest = df.iloc[-1]
                prev = df.iloc[-2]

                # 金叉
                if prev['ma5'] <= prev['ma20'] and latest['ma5'] > latest['ma20']:
                    return {
                        'action': 'buy',
                        'reason': f"金叉信号 - MA5:{latest['ma5']:.2f} > MA20:{latest['ma20']:.2f}",
                        'price': latest['close']
                    }

                # 死叉
                if prev['ma5'] >= prev['ma20'] and latest['ma5'] < latest['ma20']:
                    return {
                        'action': 'sell',
                        'reason': f"死叉信号 - MA5:{latest['ma5']:.2f} < MA20:{latest['ma20']:.2f}",
                        'price': latest['close']
                    }

            return {'action': 'hold', 'reason': '无明确信号'}

        except Exception as e:
            logger.error(f"生成信号失败 {symbol}: {str(e)}")
            return {'action': 'hold', 'reason': f'错误: {str(e)}'}

    def execute_order(self, symbol, action, price, size):
        """
        执行订单
        :param symbol: 股票代码
        :param action: 'buy' 或 'sell'
        :param price: 价格
        :param size: 数量
        :return: 执行结果
        """
        if action == 'buy':
            # 风险检查
            passed, adjusted_size, reason = self.risk_controller.check_buy_order(
                symbol, price, size
            )

            if not passed:
                logger.warning(f"买入订单被拒绝 - {symbol}: {reason}")
                return {'success': False, 'reason': reason, 'adjusted_size': adjusted_size}

            # 执行买入
            self.risk_controller.update_position(symbol, 'buy', price, size)

            # 记录交易
            trade_record = {
                'time': datetime.now(),
                'symbol': symbol,
                'action': 'buy',
                'price': price,
                'size': size,
                'value': price * size
            }
            self.trade_history.append(trade_record)

            logger.info(f"买入成功 - {symbol}, 价格:{price:.2f}, 数量:{size}")
            return {'success': True, 'trade': trade_record}

        elif action == 'sell':
            positions = self.risk_controller.get_position_info()

            if symbol not in positions:
                return {'success': False, 'reason': '无持仓'}

            available_size = positions[symbol]['size']
            if size > available_size:
                size = available_size

            # 执行卖出
            self.risk_controller.update_position(symbol, 'sell', price, size)

            # 记录交易
            trade_record = {
                'time': datetime.now(),
                'symbol': symbol,
                'action': 'sell',
                'price': price,
                'size': size,
                'value': price * size,
                'profit': (price - positions[symbol]['price']) * size
            }
            self.trade_history.append(trade_record)

            logger.info(f"卖出成功 - {symbol}, 价格:{price:.2f}, 数量:{size}, "
                       f"盈亏:{trade_record['profit']:.2f}")
            return {'success': True, 'trade': trade_record}

    def get_trade_history(self):
        """获取交易历史"""
        return pd.DataFrame(self.trade_history)

    def get_account_info(self):
        """获取账户信息"""
        positions = self.risk_controller.get_position_info()

        # 获取当前价格
        current_prices = {}
        for symbol in positions.keys():
            quote = self.data_fetcher.get_realtime_quote(symbol)
            if quote is not None:
                current_prices[symbol] = quote['最新价']

        total_value = self.risk_controller.get_total_value(current_prices)

        return {
            'total_value': total_value,
            'available_cash': self.risk_controller.available_cash,
            'positions': positions,
            'current_prices': current_prices,
            'total_return': (total_value - self.risk_controller.total_cash) /
                           self.risk_controller.total_cash * 100
        }


if __name__ == '__main__':
    print("交易模块 - 使用示例请参考主程序")
