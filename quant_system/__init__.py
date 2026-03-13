"""
A股量化交易系统
基于 Python + Backtrader + AkShare

版本: 1.0.0
作者: Claude
日期: 2026-03-13

主要功能:
- 数据获取: 基于 AkShare 获取 A 股数据
- 策略回测: 基于 Backtrader 的专业回测引擎
- 参数优化: 网格搜索优化策略参数
- 模拟交易: 实时信号生成和风险控制
- 可视化: 丰富的图表展示

快速开始:
    from quant_system import BacktestEngine, DoubleMAStrategy

    engine = BacktestEngine()
    engine.add_data('000001', '20230101', '20231231')
    engine.add_strategy(DoubleMAStrategy)
    results = engine.run()
    engine.print_results(results)
"""

__version__ = '1.0.0'
__author__ = 'Claude'

# 导入核心模块
from .data import AStockDataFetcher, get_stock_data
from .strategies import DoubleMAStrategy, MACDStrategy
from .backtest import BacktestEngine, quick_backtest
from .trading import SimulatedTrader, RiskController
from .utils import ParameterOptimizer, optimize_strategy, Visualizer

# 导出的公共接口
__all__ = [
    # 数据模块
    'AStockDataFetcher',
    'get_stock_data',

    # 策略模块
    'DoubleMAStrategy',
    'MACDStrategy',

    # 回测模块
    'BacktestEngine',
    'quick_backtest',

    # 交易模块
    'SimulatedTrader',
    'RiskController',

    # 工具模块
    'ParameterOptimizer',
    'optimize_strategy',
    'Visualizer',
]


def get_version():
    """获取系统版本"""
    return __version__


def print_info():
    """打印系统信息"""
    print("=" * 70)
    print("A股量化交易系统".center(70))
    print("=" * 70)
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print("\n核心模块:")
    print("  - 数据模块: AStockDataFetcher")
    print("  - 策略模块: DoubleMAStrategy, MACDStrategy")
    print("  - 回测模块: BacktestEngine")
    print("  - 交易模块: SimulatedTrader")
    print("  - 工具模块: ParameterOptimizer, Visualizer")
    print("\n快速开始:")
    print("  python example_backtest.py")
    print("  python example_optimize.py")
    print("  python example_trading.py")
    print("=" * 70)


if __name__ == '__main__':
    print_info()
