"""
改进的交易信号生成器
综合考虑多个因素生成更准确的交易信号
"""
from datetime import datetime


class SignalGenerator:
    """交易信号生成器"""

    def __init__(self):
        pass

    def generate_signal(self, current_price, df, fast_period=3, slow_period=40):
        """
        生成交易信号
        :param current_price: 当前价格
        :param df: 历史数据DataFrame
        :param fast_period: 快线周期
        :param slow_period: 慢线周期
        :return: 信号字典
        """
        if df is None or len(df) < slow_period:
            return {
                'signal': 'HOLD',
                'reason': '数据不足',
                'confidence': 0
            }

        # 计算均线
        ma_fast = df['close'].tail(fast_period).mean()
        ma_slow = df['close'].tail(slow_period).mean()

        # 计算前一周期的均线（用于判断交叉）
        ma_fast_prev = df['close'].tail(fast_period + 1).head(fast_period).mean()
        ma_slow_prev = df['close'].tail(slow_period + 1).head(slow_period).mean()

        # 计算价格与均线的关系
        price_above_fast = current_price > ma_fast
        price_above_slow = current_price > ma_slow
        fast_above_slow = ma_fast > ma_slow

        # 计算距离百分比
        distance_to_fast = ((current_price - ma_fast) / ma_fast) * 100
        distance_to_slow = ((current_price - ma_slow) / ma_slow) * 100

        # 判断均线交叉
        golden_cross = (ma_fast > ma_slow) and (ma_fast_prev <= ma_slow_prev)  # 金叉
        death_cross = (ma_fast < ma_slow) and (ma_fast_prev >= ma_slow_prev)   # 死叉

        # 计算趋势强度
        ma_diff_pct = ((ma_fast - ma_slow) / ma_slow) * 100

        # 信号判断逻辑
        signal = 'HOLD'
        reason = ''
        confidence = 0

        # 1. 金叉买入信号
        if golden_cross:
            if price_above_fast and price_above_slow:
                signal = 'BUY'
                reason = '金叉买入（价格在均线上方）'
                confidence = 80
            else:
                signal = 'HOLD'
                reason = '金叉但价格偏离（观望）'
                confidence = 40

        # 2. 死叉卖出信号
        elif death_cross:
            signal = 'SELL'
            reason = '死叉卖出'
            confidence = 80

        # 3. 多头趋势
        elif fast_above_slow:
            # 价格在快线上方 - 强势
            if price_above_fast and distance_to_fast > -2:
                signal = 'BUY'
                reason = f'多头趋势（价格高于MA{fast_period}）'
                confidence = 60
            # 价格跌破快线 - 警告
            elif not price_above_fast and distance_to_fast < -3:
                signal = 'SELL'
                reason = f'价格跌破MA{fast_period}（趋势转弱）'
                confidence = 70
            # 价格在快慢线之间
            elif price_above_slow and not price_above_fast:
                signal = 'HOLD'
                reason = f'价格在MA{fast_period}和MA{slow_period}之间（观望）'
                confidence = 50
            else:
                signal = 'HOLD'
                reason = '多头趋势但信号不明确'
                confidence = 40

        # 4. 空头趋势
        else:
            # 价格在慢线下方 - 弱势
            if not price_above_slow:
                signal = 'SELL'
                reason = f'空头趋势（价格低于MA{slow_period}）'
                confidence = 60
            # 价格反弹到快线上方 - 可能反转
            elif price_above_fast:
                signal = 'HOLD'
                reason = '空头趋势但价格反弹（观望）'
                confidence = 50
            else:
                signal = 'HOLD'
                reason = '空头趋势（观望）'
                confidence = 40

        # 5. 极端情况调整
        # 价格远高于慢线（超买）
        if distance_to_slow > 30:
            if signal == 'BUY':
                signal = 'HOLD'
                reason = f'价格偏离MA{slow_period}过大（超买，观望）'
                confidence = 30

        # 价格远低于慢线（超卖）
        if distance_to_slow < -10:
            if signal == 'SELL':
                signal = 'HOLD'
                reason = f'价格偏离MA{slow_period}过大（超卖，观望）'
                confidence = 30

        return {
            'signal': signal,
            'reason': reason,
            'confidence': confidence,
            'current_price': current_price,
            'ma_fast': ma_fast,
            'ma_slow': ma_slow,
            'distance_to_fast': distance_to_fast,
            'distance_to_slow': distance_to_slow,
            'trend': '多头' if fast_above_slow else '空头',
            'ma_diff_pct': ma_diff_pct
        }


# 测试代码
if __name__ == '__main__':
    import pandas as pd
    from data import AStockDataFetcher
    from datetime import timedelta

    print("=" * 70)
    print("改进的信号生成器测试")
    print("=" * 70)

    # 获取数据
    fetcher = AStockDataFetcher()
    symbol = '601016'
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')

    df = fetcher.get_stock_hist(symbol, start_date, end_date)

    if df is not None and len(df) > 0:
        # 测试不同价格的信号
        test_prices = [4.41, 4.45, 4.50, 3.50, 3.20]

        generator = SignalGenerator()

        for price in test_prices:
            print(f"\n测试价格: {price:.2f} 元")
            print("-" * 70)

            result = generator.generate_signal(price, df, fast_period=3, slow_period=40)

            print(f"信号: {result['signal']}")
            print(f"原因: {result['reason']}")
            print(f"信心度: {result['confidence']}%")
            print(f"MA3: {result['ma_fast']:.2f} 元")
            print(f"MA40: {result['ma_slow']:.2f} 元")
            print(f"距MA3: {result['distance_to_fast']:+.2f}%")
            print(f"距MA40: {result['distance_to_slow']:+.2f}%")
            print(f"趋势: {result['trend']}")

    print("\n" + "=" * 70)
