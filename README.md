# A股量化交易系统

基于Python的A股量化交易系统，支持实时监测、信号生成和多股票管理。

## 功能特性

### 1. 数据获取
- 使用AkShare获取A股实时和历史数据
- 支持数据缓存，提高访问速度
- 多源实时数据获取，提高可靠性

### 2. 交易信号生成
- 双均线策略（MA3/MA40）
- 智能信号分析，考虑超买超卖
- 信号信心度评分
- 自动检测金叉/死叉

### 3. 多股票实时监测
- 同时监测多个股票
- 侧边栏点击切换查看
- 实时价格更新
- 交易信号提示
- 可添加/删除股票

## 系统架构

```
quant_system/
├── data/
│   ├── __init__.py
│   └── data_fetcher.py          # 数据获取模块
├── backtest/
│   ├── __init__.py
│   └── backtest_engine.py       # 回测引擎
├── strategies/
│   ├── __init__.py
│   └── double_ma_strategy.py    # 双均线策略
├── trading/
│   ├── __init__.py
│   └── simulated_trader.py      # 模拟交易器
├── utils/
│   ├── __init__.py
│   ├── optimizer.py             # 参数优化器
│   └── visualizer.py            # 可视化工具
├── config.py                    # 全局配置
├── realtime_fetcher.py          # 实时行情获取
├── signal_generator.py          # 交易信号生成器
├── monitor_gui.py               # 单股票监测GUI
├── monitor_gui_multi.py         # 多股票监测GUI
├── monitor_stock.py             # 股票监测核心
├── main.py                      # 主程序入口
├── verify_system.py             # 系统验证脚本
├── requirements.txt             # 依赖列表
└── cache/                       # 数据缓存目录
```

## 安装依赖

```bash
pip install -r quant_system/requirements.txt
```

或手动安装：

```bash
pip install akshare pandas loguru matplotlib backtrader
```

## 使用方法

### 1. 系统验证

首次使用前，验证系统环境：

```bash
python quant_system/verify_system.py
```

### 2. 多股票实时监测

```bash
python quant_system/monitor_gui_multi.py
```

功能说明：
- 左侧边栏显示股票列表
- 点击股票代码切换查看
- 点击"开始监测"启动自动刷新
- 使用"添加股票"/"删除股票"管理列表
- 查看实时价格、均线、交易信号和信心度

### 3. 单股票监测

```bash
python quant_system/monitor_gui.py
```

### 4. 策略回测

```bash
python quant_system/main.py
```

### 5. 参数优化

在 `main.py` 中启用优化功能，系统会自动寻找最优参数组合

## 配置说明

### 交易参数

在 `config.py` 中可以配置：
- `INITIAL_CASH`: 初始资金（默认100,000元）
- `MA_FAST_PERIOD`: 快线周期（默认5）
- `MA_SLOW_PERIOD`: 慢线周期（默认20）

### 信号生成器

在 `signal_generator.py` 中实现了智能信号生成：
- 金叉/死叉检测
- 价格与均线关系分析
- 超买超卖判断（偏离MA40超过30%）
- 信号信心度评分（0-100）

## 信号说明

- **BUY**: 买入信号（多头趋势，价格在均线上方）
- **SELL**: 卖出信号（空头趋势或死叉）
- **HOLD**: 观望信号（信号不明确或超买超卖）

信心度：
- 80%: 金叉/死叉
- 60-70%: 趋势明确
- 40-50%: 信号不明确
- 30%: 超买超卖，建议观望

## 注意事项

1. 本系统仅供学习和研究使用
2. 不构成任何投资建议
3. 实盘交易需谨慎，风险自负
4. 数据来源于AkShare，请遵守相关使用协议

## 技术栈

- Python 3.11+
- AkShare: A股数据获取
- Pandas: 数据处理
- Tkinter: GUI界面
- Loguru: 日志管理
- Matplotlib: 数据可视化
- Backtrader: 回测框架

## 核心功能

### 数据获取
- 历史数据缓存机制
- 多源实时数据获取（spot_em、hist_min_em、daily fallback）
- 自动重试和错误处理

### 信号生成
- 双均线策略（MA3/MA40）
- 金叉/死叉自动检测
- 超买超卖判断（偏离度>30%）
- 信号信心度评分系统（0-100%）

### 回测系统
- 基于Backtrader的专业回测引擎
- 支持多种策略
- 网格搜索参数优化
- 详细的性能指标统计

### 可视化
- 实时价格曲线
- 均线指标显示
- 交易信号标注
- 回测结果图表

## 开发计划

- [x] 双均线策略实现
- [x] 实时数据获取（多源fallback）
- [x] 智能信号生成（超买超卖检测）
- [x] 多股票监测GUI
- [x] 回测引擎
- [x] 参数优化器
- [x] 数据可视化
- [ ] 添加更多技术指标（MACD、RSI、KDJ等）
- [ ] 支持自定义策略
- [ ] 支持更多数据源
- [ ] 优化GUI界面
- [ ] 添加实盘交易接口

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请提交Issue。
