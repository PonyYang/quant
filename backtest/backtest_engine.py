import backtrader as bt
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import webbrowser
import os
import numpy as np

# 设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
except:
    print("警告：未能正确设置中文字体，图表中的中文可能无法正常显示")

class BacktestEngine:
    def __init__(self, initial_cash=100000.0):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.initial_cash = initial_cash
        self.portfolio_values = []  # 用于存储每日的组合价值
        self.stock_name = None  # 用于存储股票名称
        
    def add_data(self, data, name=None):
        """添加回测数据"""
        self.data = data  # 保存原始数据以供后续使用
        self.stock_name = name  # 保存股票名称
        datafeed = bt.feeds.PandasData(dataname=data)
        self.cerebro.adddata(datafeed, name=name)
        
    def add_strategy(self, strategy_class, **kwargs):
        """添加交易策略"""
        self.cerebro.addstrategy(strategy_class, **kwargs)
        
    def run(self):
        """运行回测"""
        # 添加分析器
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual')
        
        # 记录每日的投资组合价值
        class ValueAnalyzer(bt.Analyzer):
            def __init__(self):
                self.values = []
                
            def next(self):
                self.values.append(self.strategy.broker.getvalue())
                
            def get_analysis(self):
                return self.values
        
        self.cerebro.addanalyzer(ValueAnalyzer, _name='value')
        
        results = self.cerebro.run()
        self.results = results[0]
        
        # 获取每日的投资组合价值
        self.portfolio_values = self.results.analyzers.value.get_analysis()
            
        return results
        
    def get_performance_stats(self):
        """获取回测性能统计"""
        # 计算收益率
        portfolio_value = self.cerebro.broker.getvalue()
        total_return = (portfolio_value - self.initial_cash) / self.initial_cash
        
        # 获取最大回撤
        drawdown = self.results.analyzers.drawdown.get_analysis()
        max_drawdown = drawdown['max']['drawdown'] if drawdown['max']['drawdown'] else 0
        
        # 计算年化收益率
        days = len(self.portfolio_values)
        annual_return = (1 + total_return) ** (252/days) - 1 if days > 0 else 0
        
        # 获取夏普比率
        sharpe = self.results.analyzers.sharpe.get_analysis()
        sharpe_ratio = sharpe['sharperatio'] if sharpe['sharperatio'] else 0
        
        # 获取交易统计
        trades = self.results.analyzers.trades.get_analysis()
        total_trades = trades.total.closed if hasattr(trades, 'total') else 0
        won_trades = trades.won.total if hasattr(trades, 'won') else 0
        win_rate = won_trades / total_trades if total_trades > 0 else 0
        
        return {
            '初始资金': self.initial_cash,
            '最终市值': portfolio_value,
            '总收益率': total_return * 100,
            '年化收益率': annual_return * 100,
            '最大回撤': max_drawdown,
            '夏普比率': sharpe_ratio,
            '总交易次数': total_trades,
            '胜率': win_rate * 100
        }
        
    def plot(self, filename=None):
        """绘制完整的回测报告"""
        # 创建图表
        fig = plt.figure(figsize=(15, 20))
        
        # 设置总标题
        title = 'MACD策略回测报告'
        if self.stock_name:
            title += f' - {self.stock_name}'
        fig.suptitle(title, fontsize=16, y=0.95)
        
        # 1. 收益率曲线
        ax1 = plt.subplot2grid((4, 1), (0, 0))
        portfolio_series = pd.Series(self.portfolio_values, index=self.data.index[-len(self.portfolio_values):])
        returns = portfolio_series.pct_change()
        cumulative_returns = (1 + returns).cumprod()
        ax1.plot(cumulative_returns.index, cumulative_returns.values, label='策略收益率', color='blue')
        ax1.fill_between(cumulative_returns.index, cumulative_returns.values, 1, alpha=0.3, color='blue')
        ax1.grid(True)
        ax1.set_title('累积收益率曲线')
        ax1.legend()
        
        # 2. K线图和交易点
        ax2 = plt.subplot2grid((4, 1), (1, 0))
        
        # 绘制K线
        for i in range(len(self.data)):
            if self.data['Open'].iloc[i] < self.data['Close'].iloc[i]:
                color = 'red'
            else:
                color = 'green'
            ax2.plot([self.data.index[i], self.data.index[i]], 
                    [self.data['Low'].iloc[i], self.data['High'].iloc[i]], 
                    color=color, linewidth=1)
            ax2.plot([self.data.index[i], self.data.index[i]], 
                    [self.data['Open'].iloc[i], self.data['Close'].iloc[i]], 
                    color=color, linewidth=3)
        
        # 标注买卖点
        trades = self.results.analyzers.trades.get_analysis()
        if 'closed' in trades:
            for trade in trades['closed']:
                entry_bar = trade['data'].entry.idx
                exit_bar = trade['data'].exit.idx
                entry_price = trade['data'].entry.price
                exit_price = trade['data'].exit.price
                
                ax2.plot(self.data.index[entry_bar], entry_price, '^', color='r', markersize=10, label='买入点')
                ax2.plot(self.data.index[exit_bar], exit_price, 'v', color='g', markersize=10, label='卖出点')
        
        ax2.set_title('K线图和交易点')
        ax2.grid(True)
        
        # 3. 回撤曲线
        ax3 = plt.subplot2grid((4, 1), (2, 0))
        drawdown = (portfolio_series / portfolio_series.expanding().max() - 1) * 100
        ax3.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
        ax3.plot(drawdown.index, drawdown.values, color='red', label='回撤百分比')
        ax3.set_title('回撤曲线')
        ax3.grid(True)
        ax3.legend()
        
        # 4. 性能指标
        ax4 = plt.subplot2grid((4, 1), (3, 0))
        stats = self.get_performance_stats()
        
        # 创建性能指标表格
        cell_text = []
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                if abs(value) > 100:
                    formatted_value = f'{value:,.0f}'
                else:
                    formatted_value = f'{value:.2f}%' if key not in ['夏普比率', '总交易次数'] else f'{value:.2f}'
            else:
                formatted_value = str(value)
            cell_text.append([key, formatted_value])
            
        table = ax4.table(cellText=cell_text,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.4, 0.4])
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 2)
        
        # 隐藏坐标轴
        ax4.axis('off')
        ax4.set_title('策略性能指标')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            # 在默认浏览器中打开图片
            abs_path = os.path.abspath(filename)
            webbrowser.open('file://' + abs_path)
        plt.close()
