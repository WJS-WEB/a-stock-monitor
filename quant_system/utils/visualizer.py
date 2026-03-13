"""
工具模块 - 可视化工具
功能：
1. 绘制K线图
2. 绘制资金曲线
3. 绘制回测结果
"""
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle
import mplfinance as mpf
from loguru import logger


class Visualizer:
    """可视化工具类"""

    def __init__(self):
        """初始化可视化工具"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        logger.info("可视化工具初始化完成")

    def plot_kline(self, df, title='K线图', save_path=None):
        """
        绘制K线图
        :param df: 数据DataFrame，需包含 open, high, low, close, volume
        :param title: 图表标题
        :param save_path: 保存路径
        """
        try:
            # 确保索引是日期格式
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # 使用mplfinance绘制K线图
            mc = mpf.make_marketcolors(
                up='red', down='green',
                edge='inherit',
                wick='inherit',
                volume='inherit'
            )
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)

            # 添加均线
            add_plot = []
            if 'ma5' in df.columns:
                add_plot.append(mpf.make_addplot(df['ma5'], color='blue', width=1))
            if 'ma20' in df.columns:
                add_plot.append(mpf.make_addplot(df['ma20'], color='orange', width=1))

            kwargs = {
                'type': 'candle',
                'style': s,
                'title': title,
                'ylabel': '价格',
                'volume': True,
                'ylabel_lower': '成交量',
                'figsize': (14, 8)
            }

            if add_plot:
                kwargs['addplot'] = add_plot

            if save_path:
                kwargs['savefig'] = save_path

            mpf.plot(df, **kwargs)

            logger.info(f"K线图绘制完成: {title}")

        except Exception as e:
            logger.error(f"绘制K线图失败: {str(e)}")
            # 降级方案：使用matplotlib
            self._plot_kline_fallback(df, title, save_path)

    def _plot_kline_fallback(self, df, title, save_path):
        """K线图降级方案（不依赖mplfinance）"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})

        # 绘制收盘价折线
        ax1.plot(df.index, df['close'], label='收盘价', linewidth=1)

        if 'ma5' in df.columns:
            ax1.plot(df.index, df['ma5'], label='MA5', linewidth=1)
        if 'ma20' in df.columns:
            ax1.plot(df.index, df['ma20'], label='MA20', linewidth=1)

        ax1.set_title(title)
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 绘制成交量
        if 'volume' in df.columns:
            ax2.bar(df.index, df['volume'], width=0.8, alpha=0.5)
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_equity_curve(self, equity_data, title='资金曲线', save_path=None):
        """
        绘制资金曲线
        :param equity_data: 资金数据，可以是Series或DataFrame
        :param title: 图表标题
        :param save_path: 保存路径
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            if isinstance(equity_data, pd.Series):
                ax.plot(equity_data.index, equity_data.values, linewidth=2, label='资金曲线')
            elif isinstance(equity_data, pd.DataFrame):
                for col in equity_data.columns:
                    ax.plot(equity_data.index, equity_data[col], linewidth=2, label=col)

            ax.set_title(title, fontsize=14)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('资金', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                logger.info(f"资金曲线已保存: {save_path}")
            else:
                plt.show()

        except Exception as e:
            logger.error(f"绘制资金曲线失败: {str(e)}")

    def plot_backtest_summary(self, results, save_path=None):
        """
        绘制回测结果汇总图
        :param results: 回测结果字典
        :param save_path: 保存路径
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle('回测结果汇总', fontsize=16)

            # 1. 收益指标
            ax1 = axes[0, 0]
            metrics = ['总收益率', '年化收益率', '夏普比率']
            values = [
                results.get('total_return', 0),
                results.get('annual_return', 0),
                results.get('sharpe_ratio', 0)
            ]
            colors = ['green' if v > 0 else 'red' for v in values]
            ax1.bar(metrics, values, color=colors, alpha=0.7)
            ax1.set_title('收益指标')
            ax1.set_ylabel('数值')
            ax1.grid(True, alpha=0.3, axis='y')

            # 2. 风险指标
            ax2 = axes[0, 1]
            ax2.bar(['最大回撤'], [results.get('max_drawdown', 0)], color='red', alpha=0.7)
            ax2.set_title('风险指标')
            ax2.set_ylabel('回撤 (%)')
            ax2.grid(True, alpha=0.3, axis='y')

            # 3. 交易统计
            ax3 = axes[1, 0]
            trade_stats = ['总交易次数', '盈利次数', '亏损次数']
            trade_values = [
                results.get('total_trades', 0),
                results.get('won_trades', 0),
                results.get('lost_trades', 0)
            ]
            ax3.bar(trade_stats, trade_values, color=['blue', 'green', 'red'], alpha=0.7)
            ax3.set_title('交易统计')
            ax3.set_ylabel('次数')
            ax3.grid(True, alpha=0.3, axis='y')

            # 4. 胜率和盈亏比
            ax4 = axes[1, 1]
            performance = ['胜率 (%)', '盈亏比']
            performance_values = [
                results.get('win_rate', 0),
                results.get('profit_loss_ratio', 0)
            ]
            ax4.bar(performance, performance_values, color=['orange', 'purple'], alpha=0.7)
            ax4.set_title('绩效指标')
            ax4.set_ylabel('数值')
            ax4.grid(True, alpha=0.3, axis='y')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                logger.info(f"回测汇总图已保存: {save_path}")
            else:
                plt.show()

        except Exception as e:
            logger.error(f"绘制回测汇总图失败: {str(e)}")

    def plot_optimization_results(self, results_df, x_param, y_param, metric='total_return', save_path=None):
        """
        绘制参数优化结果热力图
        :param results_df: 优化结果DataFrame
        :param x_param: X轴参数名
        :param y_param: Y轴参数名
        :param metric: 评价指标
        :param save_path: 保存路径
        """
        try:
            # 透视表
            pivot_table = results_df.pivot_table(
                values=metric,
                index=y_param,
                columns=x_param,
                aggfunc='mean'
            )

            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(pivot_table.values, cmap='RdYlGn', aspect='auto')

            # 设置坐标轴
            ax.set_xticks(range(len(pivot_table.columns)))
            ax.set_yticks(range(len(pivot_table.index)))
            ax.set_xticklabels(pivot_table.columns)
            ax.set_yticklabels(pivot_table.index)

            ax.set_xlabel(x_param)
            ax.set_ylabel(y_param)
            ax.set_title(f'参数优化结果 - {metric}')

            # 添加颜色条
            plt.colorbar(im, ax=ax)

            # 在每个格子中显示数值
            for i in range(len(pivot_table.index)):
                for j in range(len(pivot_table.columns)):
                    text = ax.text(j, i, f'{pivot_table.values[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontsize=8)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                logger.info(f"优化结果图已保存: {save_path}")
            else:
                plt.show()

        except Exception as e:
            logger.error(f"绘制优化结果图失败: {str(e)}")


if __name__ == '__main__':
    print("可视化工具模块 - 使用示例请参考主程序")
