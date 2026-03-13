"""
系统主入口 - 命令行界面
提供统一的命令行入口，方便使用
"""
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtest import BacktestEngine
from strategies import DoubleMAStrategy, MACDStrategy
from trading import SimulatedTrader
from utils import optimize_strategy, Visualizer
from data import AStockDataFetcher
import config


def run_backtest(args):
    """运行回测"""
    print(f"\n开始回测 {args.symbol}...")

    engine = BacktestEngine(initial_cash=args.cash)
    engine.add_data(args.symbol, args.start, args.end)

    # 选择策略
    strategy_map = {
        'double_ma': DoubleMAStrategy,
        'macd': MACDStrategy
    }
    strategy_class = strategy_map.get(args.strategy, DoubleMAStrategy)

    engine.add_strategy(strategy_class)
    results = engine.run()
    engine.print_results(results)

    if args.plot:
        engine.plot()


def run_optimize(args):
    """运行参数优化"""
    print(f"\n开始优化 {args.symbol}...")

    param_grid = {
        'fast_period': [3, 5, 10, 15],
        'slow_period': [20, 30, 60]
    }

    results = optimize_strategy(
        symbol=args.symbol,
        strategy_class=DoubleMAStrategy,
        param_grid=param_grid,
        start_date=args.start,
        end_date=args.end
    )

    print("\n优化结果（前10组）:")
    print(results.head(10).to_string(index=False))


def run_trading(args):
    """运行模拟交易"""
    print(f"\n模拟交易 {args.symbol}...")

    trader = SimulatedTrader(initial_cash=args.cash)
    signal = trader.generate_signal(args.symbol)

    print(f"信号: {signal['action']}")
    print(f"原因: {signal['reason']}")

    if signal['action'] == 'buy' and args.execute:
        price = signal.get('price', 0)
        size = int((trader.risk_controller.available_cash * 0.3) / price / 100) * 100
        if size > 0:
            result = trader.execute_order(args.symbol, 'buy', price, size)
            print(f"执行结果: {'成功' if result['success'] else '失败'}")


def show_data(args):
    """显示股票数据"""
    print(f"\n获取 {args.symbol} 数据...")

    fetcher = AStockDataFetcher()

    if args.type == 'hist':
        df = fetcher.get_stock_hist(args.symbol, args.start, args.end)
        print(df.tail(10))
    elif args.type == 'realtime':
        quote = fetcher.get_realtime_quote(args.symbol)
        print(quote)
    elif args.type == 'financial':
        financial = fetcher.get_stock_financial(args.symbol)
        print(financial)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='A股量化交易系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 回测
  python main.py backtest --symbol 000001 --start 20230101 --end 20231231

  # 参数优化
  python main.py optimize --symbol 000001 --start 20230101 --end 20231231

  # 模拟交易
  python main.py trade --symbol 000001

  # 查看数据
  python main.py data --symbol 000001 --type hist
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 回测命令
    backtest_parser = subparsers.add_parser('backtest', help='运行回测')
    backtest_parser.add_argument('--symbol', required=True, help='股票代码')
    backtest_parser.add_argument('--start', default='20230101', help='开始日期')
    backtest_parser.add_argument('--end', default='20231231', help='结束日期')
    backtest_parser.add_argument('--strategy', default='double_ma',
                                 choices=['double_ma', 'macd'], help='策略类型')
    backtest_parser.add_argument('--cash', type=float, default=config.INITIAL_CASH,
                                 help='初始资金')
    backtest_parser.add_argument('--plot', action='store_true', help='显示图表')

    # 优化命令
    optimize_parser = subparsers.add_parser('optimize', help='参数优化')
    optimize_parser.add_argument('--symbol', required=True, help='股票代码')
    optimize_parser.add_argument('--start', default='20230101', help='开始日期')
    optimize_parser.add_argument('--end', default='20231231', help='结束日期')

    # 交易命令
    trade_parser = subparsers.add_parser('trade', help='模拟交易')
    trade_parser.add_argument('--symbol', required=True, help='股票代码')
    trade_parser.add_argument('--cash', type=float, default=config.INITIAL_CASH,
                              help='初始资金')
    trade_parser.add_argument('--execute', action='store_true', help='执行交易')

    # 数据命令
    data_parser = subparsers.add_parser('data', help='查看数据')
    data_parser.add_argument('--symbol', required=True, help='股票代码')
    data_parser.add_argument('--type', default='hist',
                            choices=['hist', 'realtime', 'financial'],
                            help='数据类型')
    data_parser.add_argument('--start', default='20230101', help='开始日期')
    data_parser.add_argument('--end', default='20231231', help='结束日期')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'backtest':
        run_backtest(args)
    elif args.command == 'optimize':
        run_optimize(args)
    elif args.command == 'trade':
        run_trading(args)
    elif args.command == 'data':
        show_data(args)


if __name__ == '__main__':
    print("=" * 70)
    print("A股量化交易系统".center(70))
    print("=" * 70)
    main()
