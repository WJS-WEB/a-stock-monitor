"""
股票实时监测 - 图形界面版本
使用tkinter创建GUI界面，实时显示股票行情和交易信号
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data import AStockDataFetcher
from realtime_fetcher import RealtimeQuoteFetcher
from signal_generator import SignalGenerator
import config


class StockMonitorGUI:
    """股票监测GUI界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("A股实时监测系统")
        self.root.geometry("800x600")

        # 数据获取器
        self.fetcher = AStockDataFetcher()
        self.realtime_fetcher = RealtimeQuoteFetcher()
        self.signal_generator = SignalGenerator()

        # 监测状态
        self.is_monitoring = False
        self.monitor_thread = None

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""

        # 顶部控制面板
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        # 股票代码输入
        ttk.Label(control_frame, text="股票代码:").pack(side=tk.LEFT, padx=5)
        self.symbol_var = tk.StringVar(value="601016")
        symbol_entry = ttk.Entry(control_frame, textvariable=self.symbol_var, width=10)
        symbol_entry.pack(side=tk.LEFT, padx=5)

        # 刷新间隔
        ttk.Label(control_frame, text="刷新间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="30")
        interval_entry = ttk.Entry(control_frame, textvariable=self.interval_var, width=5)
        interval_entry.pack(side=tk.LEFT, padx=5)

        # 快线周期
        ttk.Label(control_frame, text="快线:").pack(side=tk.LEFT, padx=5)
        self.fast_var = tk.StringVar(value="3")
        fast_entry = ttk.Entry(control_frame, textvariable=self.fast_var, width=5)
        fast_entry.pack(side=tk.LEFT, padx=5)

        # 慢线周期
        ttk.Label(control_frame, text="慢线:").pack(side=tk.LEFT, padx=5)
        self.slow_var = tk.StringVar(value="40")
        slow_entry = ttk.Entry(control_frame, textvariable=self.slow_var, width=5)
        slow_entry.pack(side=tk.LEFT, padx=5)

        # 开始/停止按钮
        self.start_btn = ttk.Button(control_frame, text="开始监测", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(control_frame, text="停止监测", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 手动刷新按钮
        refresh_btn = ttk.Button(control_frame, text="立即刷新", command=self.manual_refresh)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # 分隔线
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # 主显示区域
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：实时行情
        left_frame = ttk.LabelFrame(main_frame, text="实时行情", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 行情信息标签
        self.time_label = ttk.Label(left_frame, text="更新时间: --", font=("Arial", 10))
        self.time_label.pack(anchor=tk.W, pady=2)

        self.price_label = ttk.Label(left_frame, text="最新价格: --", font=("Arial", 14, "bold"))
        self.price_label.pack(anchor=tk.W, pady=5)

        self.change_label = ttk.Label(left_frame, text="涨跌幅: --", font=("Arial", 12))
        self.change_label.pack(anchor=tk.W, pady=2)

        self.volume_label = ttk.Label(left_frame, text="成交量: --", font=("Arial", 10))
        self.volume_label.pack(anchor=tk.W, pady=2)

        self.high_label = ttk.Label(left_frame, text="最高价: --", font=("Arial", 10))
        self.high_label.pack(anchor=tk.W, pady=2)

        self.low_label = ttk.Label(left_frame, text="最低价: --", font=("Arial", 10))
        self.low_label.pack(anchor=tk.W, pady=2)

        # 右侧：技术指标和信号
        right_frame = ttk.LabelFrame(main_frame, text="技术分析", padding="10")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.ma_fast_label = ttk.Label(right_frame, text="快线(MA3): --", font=("Arial", 10))
        self.ma_fast_label.pack(anchor=tk.W, pady=2)

        self.ma_slow_label = ttk.Label(right_frame, text="慢线(MA40): --", font=("Arial", 10))
        self.ma_slow_label.pack(anchor=tk.W, pady=2)

        self.ma_diff_label = ttk.Label(right_frame, text="均线差: --", font=("Arial", 10))
        self.ma_diff_label.pack(anchor=tk.W, pady=2)

        self.distance_label = ttk.Label(right_frame, text="距慢线: --", font=("Arial", 10))
        self.distance_label.pack(anchor=tk.W, pady=2)

        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        self.signal_label = ttk.Label(right_frame, text="交易信号: --", font=("Arial", 14, "bold"))
        self.signal_label.pack(anchor=tk.W, pady=5)

        self.trend_label = ttk.Label(right_frame, text="趋势: --", font=("Arial", 12))
        self.trend_label.pack(anchor=tk.W, pady=2)

        # 底部：日志区域
        log_frame = ttk.LabelFrame(self.root, text="监测日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建滚动文本框
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def start_monitoring(self):
        """开始监测"""
        if self.is_monitoring:
            return

        try:
            symbol = self.symbol_var.get().strip()
            interval = int(self.interval_var.get())

            if not symbol:
                messagebox.showerror("错误", "请输入股票代码")
                return

            if interval < 5:
                messagebox.showerror("错误", "刷新间隔不能小于5秒")
                return

            self.is_monitoring = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            self.log(f"开始监测 {symbol}，刷新间隔 {interval} 秒")
            self.status_var.set(f"监测中: {symbol}")

            # 启动监测线程
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()

        except ValueError:
            messagebox.showerror("错误", "刷新间隔必须是数字")

    def stop_monitoring(self):
        """停止监测"""
        self.is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("监测已停止")
        self.status_var.set("就绪")

    def manual_refresh(self):
        """手动刷新"""
        self.log("手动刷新数据...")
        threading.Thread(target=self.fetch_and_update, daemon=True).start()

    def monitor_loop(self):
        """监测循环"""
        interval = int(self.interval_var.get())

        while self.is_monitoring:
            self.fetch_and_update()

            # 等待指定间隔
            for _ in range(interval):
                if not self.is_monitoring:
                    break
                time.sleep(1)

    def fetch_and_update(self):
        """获取数据并更新界面"""
        try:
            symbol = self.symbol_var.get().strip()
            fast_period = int(self.fast_var.get())
            slow_period = int(self.slow_var.get())

            # 先尝试获取实时行情
            realtime_quote = self.realtime_fetcher.get_realtime_quote(symbol)

            # 获取历史数据用于计算均线
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')

            df = self.fetcher.get_stock_hist(symbol, start_date, end_date)

            if df is None or len(df) == 0:
                self.log("数据获取失败")
                return

            # 更新界面（在主线程中执行）
            self.root.after(0, self.update_display, df, realtime_quote, fast_period, slow_period)

        except Exception as e:
            self.log(f"错误: {str(e)}")

    def update_display(self, df, realtime_quote, fast_period, slow_period):
        """更新显示"""
        try:
            # 更新时间
            self.time_label.config(text=f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 判断使用实时数据还是历史数据
            if realtime_quote:
                # 使用实时数据
                price = realtime_quote['最新价']
                self.price_label.config(text=f"最新价格: {price:.2f} 元 (实时)")

                if '涨跌幅' in realtime_quote:
                    change_pct = realtime_quote['涨跌幅']
                    color = "red" if change_pct > 0 else "green" if change_pct < 0 else "black"
                    self.change_label.config(text=f"涨跌幅: {change_pct:+.2f}%", foreground=color)

                self.volume_label.config(text=f"成交量: {realtime_quote.get('成交量', 0):,.0f}")
                self.high_label.config(text=f"最高价: {realtime_quote.get('最高', 0):.2f} 元")
                self.low_label.config(text=f"最低价: {realtime_quote.get('最低', 0):.2f} 元")

                data_type = "实时数据"
            else:
                # 使用历史收盘数据
                latest = df.iloc[-1]
                price = latest['close']
                self.price_label.config(text=f"最新价格: {price:.2f} 元 (收盘)")

                if len(df) > 1:
                    change_pct = ((latest['close'] / df.iloc[-2]['close'] - 1) * 100)
                    color = "red" if change_pct > 0 else "green" if change_pct < 0 else "black"
                    self.change_label.config(text=f"涨跌幅: {change_pct:+.2f}%", foreground=color)

                self.volume_label.config(text=f"成交量: {latest['volume']:,.0f}")
                self.high_label.config(text=f"最高价: {latest['high']:.2f} 元")
                self.low_label.config(text=f"最低价: {latest['low']:.2f} 元")

                data_type = "历史数据"

            # 计算均线
            if len(df) >= slow_period:
                # 使用改进的信号生成器
                signal_result = self.signal_generator.generate_signal(
                    current_price=price,
                    df=df,
                    fast_period=fast_period,
                    slow_period=slow_period
                )

                ma_fast = signal_result['ma_fast']
                ma_slow = signal_result['ma_slow']
                distance = signal_result['distance_to_slow']

                self.ma_fast_label.config(text=f"快线(MA{fast_period}): {ma_fast:.2f} 元")
                self.ma_slow_label.config(text=f"慢线(MA{slow_period}): {ma_slow:.2f} 元")
                self.ma_diff_label.config(text=f"均线差: {signal_result['ma_diff_pct']:+.2f}%")
                self.distance_label.config(text=f"距慢线: {distance:+.2f}%")

                # 显示信号
                signal = signal_result['signal']
                reason = signal_result['reason']
                confidence = signal_result['confidence']
                trend = signal_result['trend']

                # 设置信号颜色
                if signal == 'BUY':
                    signal_color = "red"
                    signal_text = f"买入信号 ({confidence}%)"
                elif signal == 'SELL':
                    signal_color = "green"
                    signal_text = f"卖出信号 ({confidence}%)"
                else:
                    signal_color = "black"
                    signal_text = f"观望 ({confidence}%)"

                self.signal_label.config(text=f"交易信号: {signal_text}", foreground=signal_color)
                self.trend_label.config(text=f"趋势: {trend} | {reason}")

                self.log(f"更新成功 ({data_type}) - 价格: {price:.2f}, 信号: {signal} ({reason})")
            else:
                self.log("数据不足，无法计算均线")

        except Exception as e:
            self.log(f"更新显示错误: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = StockMonitorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
