"""
多股票实时监测 - 图形界面版本
支持多个股票同时监测，侧边栏切换显示
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


class MultiStockMonitorGUI:
    """多股票监测GUI界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("A股多股票实时监测系统")
        self.root.geometry("1000x700")

        # 数据获取器
        self.fetcher = AStockDataFetcher()
        self.realtime_fetcher = RealtimeQuoteFetcher()
        self.signal_generator = SignalGenerator()

        # 监测的股票列表
        self.stock_list = ["601016", "600519", "000001", "600036"]  # 默认股票列表
        self.current_stock = self.stock_list[0]  # 当前显示的股票
        self.stock_data = {}  # 存储每个股票的数据

        # 监测状态
        self.is_monitoring = False
        self.monitor_thread = None

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""

        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左侧边栏 - 股票列表
        sidebar_frame = ttk.Frame(main_container, width=200)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        sidebar_frame.pack_propagate(False)

        # 侧边栏标题
        ttk.Label(sidebar_frame, text="监测股票列表", font=("Arial", 12, "bold")).pack(pady=10)

        # 股票列表框
        list_frame = ttk.Frame(sidebar_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.stock_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.stock_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.stock_listbox.yview)

        # 绑定选择事件
        self.stock_listbox.bind('<<ListboxSelect>>', self.on_stock_select)

        # 填充股票列表
        for stock in self.stock_list:
            self.stock_listbox.insert(tk.END, stock)
        self.stock_listbox.selection_set(0)

        # 添加/删除股票按钮
        btn_frame = ttk.Frame(sidebar_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="添加股票", command=self.add_stock).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="删除股票", command=self.remove_stock).pack(fill=tk.X, pady=2)

        # 右侧主显示区域
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 顶部控制面板
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=5)

        # 当前股票显示
        self.current_stock_label = ttk.Label(control_frame, text=f"当前: {self.current_stock}",
                                             font=("Arial", 14, "bold"))
        self.current_stock_label.pack(side=tk.LEFT, padx=10)

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
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # 主显示区域
        display_frame = ttk.Frame(right_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：实时行情
        left_display = ttk.LabelFrame(display_frame, text="实时行情", padding="10")
        left_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 行情信息标签
        self.time_label = ttk.Label(left_display, text="更新时间: --", font=("Arial", 10))
        self.time_label.pack(anchor=tk.W, pady=2)

        self.price_label = ttk.Label(left_display, text="最新价格: --", font=("Arial", 14, "bold"))
        self.price_label.pack(anchor=tk.W, pady=5)

        self.ma_fast_label = ttk.Label(left_display, text="MA3: --", font=("Arial", 12))
        self.ma_fast_label.pack(anchor=tk.W, pady=2)

        self.ma_slow_label = ttk.Label(left_display, text="MA40: --", font=("Arial", 12))
        self.ma_slow_label.pack(anchor=tk.W, pady=2)

        self.distance_fast_label = ttk.Label(left_display, text="距MA3: --", font=("Arial", 10))
        self.distance_fast_label.pack(anchor=tk.W, pady=2)

        self.distance_slow_label = ttk.Label(left_display, text="距MA40: --", font=("Arial", 10))
        self.distance_slow_label.pack(anchor=tk.W, pady=2)

        self.trend_label = ttk.Label(left_display, text="趋势: --", font=("Arial", 11))
        self.trend_label.pack(anchor=tk.W, pady=2)

        # 右侧：交易信号
        right_display = ttk.LabelFrame(display_frame, text="交易信号", padding="10")
        right_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.signal_label = ttk.Label(right_display, text="信号: --", font=("Arial", 16, "bold"))
        self.signal_label.pack(anchor=tk.W, pady=5)

        self.confidence_label = ttk.Label(right_display, text="信心度: --", font=("Arial", 12))
        self.confidence_label.pack(anchor=tk.W, pady=2)

        self.reason_label = ttk.Label(right_display, text="原因: --", font=("Arial", 11), wraplength=300)
        self.reason_label.pack(anchor=tk.W, pady=5)

        # 底部日志区域
        log_frame = ttk.LabelFrame(right_frame, text="运行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame, height=8, yscrollcommand=log_scroll.set, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

    def on_stock_select(self, event):
        """股票选择事件"""
        selection = self.stock_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_stock = self.stock_list[index]
            self.current_stock_label.config(text=f"当前: {self.current_stock}")
            self.log(f"切换到股票: {self.current_stock}")
            # 更新显示
            self.update_display()

    def add_stock(self):
        """添加股票到监测列表"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加股票")
        dialog.geometry("300x100")

        ttk.Label(dialog, text="股票代码:").pack(pady=10)
        code_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=code_var, width=15)
        entry.pack(pady=5)

        def confirm():
            code = code_var.get().strip()
            if code and code not in self.stock_list:
                self.stock_list.append(code)
                self.stock_listbox.insert(tk.END, code)
                self.log(f"添加股票: {code}")
                dialog.destroy()
            elif code in self.stock_list:
                messagebox.showwarning("警告", "股票已存在")
            else:
                messagebox.showwarning("警告", "请输入股票代码")

        ttk.Button(dialog, text="确定", command=confirm).pack(pady=5)

    def remove_stock(self):
        """从监测列表删除股票"""
        selection = self.stock_listbox.curselection()
        if selection:
            index = selection[0]
            stock = self.stock_list[index]
            if len(self.stock_list) <= 1:
                messagebox.showwarning("警告", "至少保留一个股票")
                return
            self.stock_list.pop(index)
            self.stock_listbox.delete(index)
            if stock in self.stock_data:
                del self.stock_data[stock]
            self.log(f"删除股票: {stock}")
            # 如果删除的是当前股票，切换到第一个
            if stock == self.current_stock:
                self.current_stock = self.stock_list[0]
                self.stock_listbox.selection_set(0)
                self.current_stock_label.config(text=f"当前: {self.current_stock}")
                self.update_display()

    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

    def start_monitoring(self):
        """开始监测"""
        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("开始监测所有股票...")

        # 启动监测线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监测"""
        self.is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("停止监测")

    def monitor_loop(self):
        """监测循环"""
        while self.is_monitoring:
            try:
                # 获取所有股票的数据
                for stock in self.stock_list:
                    self.fetch_stock_data(stock)

                # 更新当前显示的股票
                self.update_display()

                # 等待刷新间隔
                interval = int(self.interval_var.get())
                time.sleep(interval)

            except Exception as e:
                self.log(f"监测出错: {str(e)}")
                time.sleep(5)

    def fetch_stock_data(self, symbol):
        """获取单个股票的数据"""
        try:
            # 获取实时价格
            quote_data = self.realtime_fetcher.get_realtime_quote(symbol)
            if quote_data is None:
                return

            # 提取价格（realtime_fetcher返回字典或float）
            if isinstance(quote_data, dict):
                price = quote_data.get('最新价', quote_data.get('price', None))
            else:
                price = float(quote_data)

            if price is None:
                return

            # 获取历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
            df = self.fetcher.get_stock_hist(symbol, start_date, end_date)

            if df is None or len(df) == 0:
                return

            # 生成交易信号
            fast_period = int(self.fast_var.get())
            slow_period = int(self.slow_var.get())
            signal_result = self.signal_generator.generate_signal(
                current_price=price,
                df=df,
                fast_period=fast_period,
                slow_period=slow_period
            )

            # 存储数据
            self.stock_data[symbol] = {
                'price': price,
                'quote_data': quote_data,
                'signal': signal_result,
                'update_time': datetime.now()
            }

        except Exception as e:
            self.log(f"获取 {symbol} 数据失败: {str(e)}")

    def update_display(self):
        """更新显示"""
        if self.current_stock not in self.stock_data:
            return

        data = self.stock_data[self.current_stock]
        price = data['price']
        signal = data['signal']
        update_time = data['update_time']

        # 更新时间
        self.time_label.config(text=f"更新时间: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 更新价格
        self.price_label.config(text=f"最新价格: {price:.2f} 元")

        # 更新均线
        self.ma_fast_label.config(text=f"MA{int(self.fast_var.get())}: {signal['ma_fast']:.2f} 元")
        self.ma_slow_label.config(text=f"MA{int(self.slow_var.get())}: {signal['ma_slow']:.2f} 元")

        # 更新距离
        self.distance_fast_label.config(text=f"距MA{int(self.fast_var.get())}: {signal['distance_to_fast']:+.2f}%")
        self.distance_slow_label.config(text=f"距MA{int(self.slow_var.get())}: {signal['distance_to_slow']:+.2f}%")

        # 更新趋势
        self.trend_label.config(text=f"趋势: {signal['trend']}")

        # 更新信号
        signal_text = signal['signal']
        signal_color = 'red' if signal_text == 'BUY' else ('green' if signal_text == 'SELL' else 'gray')
        self.signal_label.config(text=f"信号: {signal_text}", foreground=signal_color)

        # 更新信心度
        self.confidence_label.config(text=f"信心度: {signal['confidence']}%")

        # 更新原因
        self.reason_label.config(text=f"原因: {signal['reason']}")

    def manual_refresh(self):
        """手动刷新"""
        self.log("手动刷新...")
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        """执行刷新"""
        try:
            for stock in self.stock_list:
                self.fetch_stock_data(stock)
            self.update_display()
            self.log("刷新完成")
        except Exception as e:
            self.log(f"刷新失败: {str(e)}")


def main():
    root = tk.Tk()
    app = MultiStockMonitorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
