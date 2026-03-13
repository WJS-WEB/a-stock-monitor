"""
配置文件 - 系统全局配置
"""
import os

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 确保目录存在
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== 数据配置 ====================
# 数据缓存设置
ENABLE_CACHE = True  # 是否启用本地缓存
CACHE_EXPIRE_DAYS = 1  # 缓存过期天数

# 复权方式：'qfq'前复权, 'hfq'后复权, None不复权
ADJUST_TYPE = 'qfq'

# 数据获取默认参数
DEFAULT_START_DATE = '20190101'  # 默认起始日期（5年前）
DEFAULT_PERIOD = 'daily'  # 数据周期：daily, weekly, monthly

# ==================== 回测配置 ====================
# 初始资金
INITIAL_CASH = 100000.0

# 手续费设置
COMMISSION_RATE = 0.0003  # 佣金费率 0.03%
STAMP_DUTY_RATE = 0.001  # 印花税 0.1%（仅卖出收取）

# 滑点设置
SLIPPAGE_PERC = 0.0001  # 滑点 0.01%

# ==================== 风险控制配置 ====================
# 仓位控制
MAX_POSITION_PCT = 0.2  # 单只股票最大仓位 20%
MAX_TOTAL_POSITION_PCT = 0.8  # 总仓位上限 80%

# 止损止盈
STOP_LOSS_PCT = 0.1  # 止损比例 10%
TAKE_PROFIT_PCT = 0.2  # 止盈比例 20%

# ==================== 策略配置 ====================
# 双均线策略默认参数
MA_FAST_PERIOD = 5  # 快速均线周期
MA_SLOW_PERIOD = 20  # 慢速均线周期

# ==================== 日志配置 ====================
LOG_LEVEL = 'INFO'  # 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
LOG_ROTATION = '10 MB'  # 日志文件大小限制
LOG_RETENTION = '30 days'  # 日志保留时间

# ==================== 其他配置 ====================
# 股票代码格式化
def format_stock_code(code):
    """
    格式化股票代码
    :param code: 股票代码，如 '000001' 或 'sz000001'
    :return: 标准格式代码
    """
    code = str(code).strip()
    if len(code) == 6:
        return code
    elif code.startswith(('sz', 'sh')):
        return code[2:]
    return code
