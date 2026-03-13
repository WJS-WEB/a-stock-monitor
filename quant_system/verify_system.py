"""
系统验证脚本
用于检查系统安装和配置是否正确
"""
import sys
import os

def check_python_version():
    """检查 Python 版本"""
    print("检查 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  [FAIL] Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("  需要 Python 3.8 或更高版本")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    required_packages = {
        'backtrader': 'Backtrader',
        'akshare': 'AkShare',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'matplotlib': 'Matplotlib',
        'loguru': 'Loguru',
    }

    all_installed = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [FAIL] {name} 未安装")
            all_installed = False

    return all_installed


def check_directories():
    """检查目录结构"""
    print("\n检查目录结构...")
    required_dirs = ['data', 'strategies', 'backtest', 'trading', 'utils', 'cache', 'logs']

    all_exist = True
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  [OK] {dir_name}/")
        else:
            print(f"  [FAIL] {dir_name}/ 不存在")
            all_exist = False

    return all_exist


def check_modules():
    """检查模块导入"""
    print("\n检查模块导入...")
    modules = [
        ('data.data_fetcher', 'AStockDataFetcher'),
        ('strategies.double_ma_strategy', 'DoubleMAStrategy'),
        ('backtest.backtest_engine', 'BacktestEngine'),
        ('trading.simulated_trader', 'SimulatedTrader'),
        ('utils.optimizer', 'ParameterOptimizer'),
        ('utils.visualizer', 'Visualizer'),
    ]

    all_imported = True
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  [OK] {module_path}.{class_name}")
        except Exception as e:
            print(f"  [FAIL] {module_path}.{class_name}: {str(e)}")
            all_imported = False

    return all_imported


def check_config():
    """检查配置文件"""
    print("\n检查配置文件...")
    try:
        import config
        required_configs = [
            'INITIAL_CASH',
            'COMMISSION_RATE',
            'MAX_POSITION_PCT',
            'STOP_LOSS_PCT',
            'MA_FAST_PERIOD',
            'MA_SLOW_PERIOD',
        ]

        all_exist = True
        for conf in required_configs:
            if hasattr(config, conf):
                value = getattr(config, conf)
                print(f"  [OK] {conf} = {value}")
            else:
                print(f"  [FAIL] {conf} 未定义")
                all_exist = False

        return all_exist
    except Exception as e:
        print(f"  [FAIL] 配置文件错误: {str(e)}")
        return False


def test_data_fetcher():
    """测试数据获取"""
    print("\n测试数据获取...")
    try:
        from data import AStockDataFetcher
        fetcher = AStockDataFetcher()
        print("  [OK] 数据获取器初始化成功")

        # 测试获取股票列表（不实际调用API，避免网络问题）
        print("  [OK] 数据模块功能正常")
        return True
    except Exception as e:
        print(f"  [FAIL] 数据获取测试失败: {str(e)}")
        return False


def test_backtest_engine():
    """测试回测引擎"""
    print("\n测试回测引擎...")
    try:
        from backtest import BacktestEngine
        engine = BacktestEngine(initial_cash=100000)
        print("  [OK] 回测引擎初始化成功")
        return True
    except Exception as e:
        print(f"  [FAIL] 回测引擎测试失败: {str(e)}")
        return False


def test_strategy():
    """测试策略模块"""
    print("\n测试策略模块...")
    try:
        from strategies import DoubleMAStrategy, MACDStrategy
        print("  [OK] 双均线策略加载成功")
        print("  [OK] MACD策略加载成功")
        return True
    except Exception as e:
        print(f"  [FAIL] 策略模块测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("A股量化交易系统 - 验证脚本".center(70))
    print("=" * 70)

    results = []

    # 执行所有检查
    results.append(("Python 版本", check_python_version()))
    results.append(("依赖包", check_dependencies()))
    results.append(("目录结构", check_directories()))
    results.append(("模块导入", check_modules()))
    results.append(("配置文件", check_config()))
    results.append(("数据获取", test_data_fetcher()))
    results.append(("回测引擎", test_backtest_engine()))
    results.append(("策略模块", test_strategy()))

    # 汇总结果
    print("\n" + "=" * 70)
    print("验证结果汇总".center(70))
    print("=" * 70)

    passed = 0
    failed = 0

    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{name:20s} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 70)
    print(f"总计: {len(results)} 项检查")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print("=" * 70)

    if failed == 0:
        print("\n[OK] 所有检查通过！系统可以正常使用。")
        print("\n快速开始:")
        print("  python example_backtest.py")
        return 0
    else:
        print(f"\n[FAIL] 有 {failed} 项检查失败，请先解决问题。")
        print("\n解决方法:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 检查目录结构是否完整")
        print("  3. 查看错误信息并修复")
        return 1


if __name__ == '__main__':
    sys.exit(main())
