"""
实时股票监测脚本
功能：实时监测指定股票的行情和交易信号
"""
import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data import AStockDataFetcher
from trading import SimulatedTrader
import config


def monitor_stock(symbol, interval=60, fast_period=3, slow_period=40):
    """
    实时监测股票
    :param symbol: 股票代码
    :param interval: 监测间隔（秒）
    :param fast_period: 快线周期
    :param slow_period: 慢线周期
    """
    print("=" * 70)
    print(f"股票实时监测系统 - {symbol}".center(70))
    print("=" * 70)
    print(f"\n监测股票: {symbol}")
    print(f"监测间隔: {interval} 秒")
    print(f"策略参数: 快线={fast_period}日, 慢线={slow_period}日")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n按 Ctrl+C 停止监测")
    print("=" * 70)

    # 创建数据获取器和交易器
    fetcher = AStockDataFetcher()
    trader = SimulatedTrader(initial_cash=config.INITIAL_CASH)

    count = 0

    try:
        while True:
            count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"\n[{count}] {current_time}")
            print("-" * 70)

            # 获取最新数据
            try:
                # 先尝试获取实时行情
                realtime = fetcher.get_realtime_quote(symbol)

                # 获取最近100天的历史数据用于计算均线
                from datetime import timedelta
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')

                df = fetcher.get_stock_hist(symbol, start_date, end_date)

                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]

                    # 显示实时行情（如果获取成功）或最新收盘价
                    if realtime is not None and '最新价' in realtime:
                        current_price = float(realtime['最新价'])
                        print(f"实时价格: {current_price:.2f} 元 (实时)")
                        print(f"今日涨跌: {realtime.get('涨跌幅', 'N/A')}")
                        print(f"今日成交: {realtime.get('成交量', 'N/A')}")
                        print(f"开盘价:   {realtime.get('今开', 'N/A')}")
                        print(f"最高价:   {realtime.get('最高', 'N/A')}")
                        print(f"最低价:   {realtime.get('最低', 'N/A')}")
                    else:
                        print(f"最新价格: {latest['close']:.2f} 元 (收盘价)")
                        print(f"涨跌幅:   {((latest['close'] / df.iloc[-2]['close'] - 1) * 100):.2f}%" if len(df) > 1 else "涨跌幅:   N/A")
                        print(f"成交量:   {latest['volume']:,.0f}")
                        print("注意: 实时行情获取失败，显示最新收盘价")

                    # 计算均线
                    if len(df) >= slow_period:
                        ma_fast = df['close'].tail(fast_period).mean()
                        ma_slow = df['close'].tail(slow_period).mean()

                        print(f"MA{fast_period}:      {ma_fast:.2f} 元")
                        print(f"MA{slow_period}:      {ma_slow:.2f} 元")

                        # 判断信号
                        if ma_fast > ma_slow:
                            signal = "买入信号 (金叉)"
                            signal_color = "🟢"
                        elif ma_fast < ma_slow:
                            signal = "卖出信号 (死叉)"
                            signal_color = "🔴"
                        else:
                            signal = "持有 (均线持平)"
                            signal_color = "🟡"

                        print(f"交易信号: {signal_color} {signal}")

                        # 计算距离均线的距离
                        distance = ((latest['close'] - ma_slow) / ma_slow) * 100
                        print(f"距MA{slow_period}: {distance:+.2f}%")
                    else:
                        print("数据不足，无法计算均线")
                else:
                    print("获取数据失败")

            except Exception as e:
                print(f"监测出错: {str(e)}")

            print("-" * 70)

            # 等待下一次监测
            if count == 1:
                print(f"\n等待 {interval} 秒后进行下一次监测...")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("监测已停止".center(70))
        print("=" * 70)
        print(f"总监测次数: {count}")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='股票实时监测系统')
    parser.add_argument('--symbol', type=str, default='601016', help='股票代码')
    parser.add_argument('--interval', type=int, default=60, help='监测间隔（秒）')
    parser.add_argument('--fast', type=int, default=3, help='快线周期')
    parser.add_argument('--slow', type=int, default=40, help='慢线周期')

    args = parser.parse_args()

    monitor_stock(
        symbol=args.symbol,
        interval=args.interval,
        fast_period=args.fast,
        slow_period=args.slow
    )


if __name__ == '__main__':
    main()
