import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde
import akshare as ak
import webbrowser
import os

class PerformanceAnalyzer:
    def __init__(self, portfolio_values, stock_code=None):
        """
        初始化性能分析器
        
        Parameters:
        -----------
        portfolio_values : pandas.Series
            投资组合价值序列
        stock_code : str, optional
            股票代码
        """
        self.portfolio_values = portfolio_values
        self.stock_code = stock_code
        self.stock_chinese_name = None
        
        # 获取股票中文名称
        if stock_code:
            try:
                # 使用tushare的基础数据接口
                import tushare as ts
                ts.set_token('your_token_here')  # 需要先在tushare网站注册获取token
                pro = ts.pro_api()
                
                # 获取股票基本信息
                df = pro.stock_basic(exchange='', list_status='L')
                stock_info = df[df['symbol'] == stock_code]
                if not stock_info.empty:
                    self.stock_chinese_name = stock_info.iloc[0]['name']
                    print(f"获取到股票信息: {stock_code} - {self.stock_chinese_name}")
            except Exception as e:
                print(f"获取股票信息时出错: {e}")
                
                # 如果tushare获取失败，尝试使用akshare
                try:
                    stock_info = ak.stock_individual_info_em(symbol=stock_code)
                    if not stock_info.empty:
                        # 尝试获取股票名称
                        name_row = stock_info[stock_info['item'].str.contains('名称|简称', na=False)]
                        if not name_row.empty:
                            self.stock_chinese_name = name_row.iloc[0]['value']
                            print(f"使用akshare获取到股票信息: {stock_code} - {self.stock_chinese_name}")
                except Exception as e2:
                    print(f"使用akshare获取股票信息时也出错: {e2}")
        
        self.initial_value = portfolio_values.iloc[0]
        
    def calculate_metrics(self):
        """计算性能指标"""
        # 计算每日收益率
        daily_returns = self.portfolio_values.pct_change().fillna(0)
        
        # 计算累积收益率
        total_return = (self.portfolio_values.iloc[-1] / self.portfolio_values.iloc[0] - 1) * 100
        
        # 计算年化收益率
        days = len(self.portfolio_values)
        annual_return = ((1 + total_return/100) ** (252/days) - 1) * 100
        
        # 计算波动率
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 计算夏普比率 (假设无风险收益率为3%)
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return/100 - risk_free_rate) / (volatility/100) if volatility != 0 else 0
        
        # 计算最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max * 100
        max_drawdown = abs(drawdowns.min())
        
        # 计算日胜率
        win_rate = len(daily_returns[daily_returns > 0]) / len(daily_returns[daily_returns != 0])
        
        return {
            '累积收益率': total_return,
            '年化收益率': annual_return,
            '波动率': volatility,
            '夏普比率': sharpe_ratio,
            '最大回撤': max_drawdown,
            '日胜率': win_rate * 100
        }
    
    def plot_summary(self, filename=None):
        """绘制策略表现汇总图"""
        # 创建图表
        fig = plt.figure(figsize=(16, 16))  # 进一步增加高度
        
        # 设置总标题
        title = 'MACD策略回测报告'
        if self.stock_code:
            if self.stock_chinese_name:
                title += f' - {self.stock_code} ({self.stock_chinese_name})'
            else:
                title += f' - {self.stock_code}'
        fig.suptitle(title, fontsize=16, y=0.98)
        
        # 设置网格布局，进一步增加间距
        gs = gridspec.GridSpec(3, 2, 
                             height_ratios=[2, 1.5, 1.5], 
                             hspace=0.5,    # 增加垂直间距
                             wspace=0.4,    # 增加水平间距
                             top=0.95,      # 调整顶部边距
                             bottom=0.07,   # 调整底部边距
                             left=0.12,     # 增加左边距
                             right=0.95)    # 保持右边距
        
        # 计算指标
        daily_returns = self.portfolio_values.pct_change().fillna(0) * 100
        cumulative_returns = (1 + daily_returns/100).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max * 100
        
        # 1. 累积收益率曲线
        ax1 = plt.subplot(gs[0, :])
        ax1.plot(cumulative_returns.index, cumulative_returns.values, 
                label='累积收益率', color='#1f77b4', linewidth=2)
        ax1.fill_between(drawdowns.index, 0, drawdowns.values, 
                        color='#ff9999', alpha=0.3, label='回撤')
        
        # 设置x轴日期格式
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # 设置网格和标题
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.set_title('策略累积收益率表现', pad=20, fontsize=12)
        ax1.set_ylabel('累积收益率（倍）', labelpad=10)  # 增加y轴标签间距
        ax1.legend(loc='upper left')
        
        # 优化y轴范围
        y_min = min(0.8, cumulative_returns.min() * 0.95)
        y_max = max(1.2, cumulative_returns.max() * 1.05)
        ax1.set_ylim(y_min, y_max)
        
        # 2. 日收益率分布直方图
        ax2 = plt.subplot(gs[1, 0])
        n, bins, patches = ax2.hist(daily_returns, bins=50, density=True, 
                                  alpha=0.75, color='#2ecc71')
        
        # 添加核密度估计
        kde = gaussian_kde(daily_returns)
        x_range = np.linspace(daily_returns.min(), daily_returns.max(), 100)
        ax2.plot(x_range, kde(x_range), 'r-', linewidth=2, label='密度估计')
        
        # 设置标题和标签
        ax2.set_title('日收益率分布', pad=20, fontsize=12)
        ax2.set_xlabel('日收益率 (%)', labelpad=10)  # 增加x轴标签间距
        ax2.set_ylabel('频率', labelpad=10)  # 增加y轴标签间距
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend()
        
        # 优化x轴范围
        x_range = max(abs(daily_returns.min()), abs(daily_returns.max()))
        ax2.set_xlim(-x_range * 1.1, x_range * 1.1)
        
        # 3. 回撤分析
        ax3 = plt.subplot(gs[1, 1])
        ax3.fill_between(drawdowns.index, drawdowns.values, 0, 
                        color='#e74c3c', alpha=0.5)
        ax3.plot(drawdowns.index, drawdowns.values, 
                color='#c0392b', linewidth=1, label='回撤')
        
        # 设置x轴日期格式
        ax3.xaxis.set_major_locator(mdates.YearLocator())
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # 设置标题和标签
        ax3.set_title('策略回撤分析', pad=20, fontsize=12)
        ax3.set_ylabel('回撤幅度 (%)', labelpad=10)  # 增加y轴标签间距
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.legend()
        
        # 4. 滚动收益率
        ax4 = plt.subplot(gs[2, 0])
        rolling_returns = daily_returns.rolling(window=20).mean() * 20  # 月化收益率
        ax4.plot(rolling_returns.index, rolling_returns.values, 
                color='#8e44ad', linewidth=1.5, label='20日滚动收益率')
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        
        # 设置x轴日期格式
        ax4.xaxis.set_major_locator(mdates.YearLocator())
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        # 设置标题和标签
        ax4.set_title('滚动收益率分析', pad=20, fontsize=12)
        ax4.set_xlabel('日期', labelpad=10)  # 增加x轴标签间距
        ax4.set_ylabel('月化收益率 (%)', labelpad=10)  # 增加y轴标签间距
        ax4.grid(True, linestyle='--', alpha=0.7)
        ax4.legend()
        
        # 5. 性能指标表格
        ax5 = plt.subplot(gs[2, 1])
        metrics = self.calculate_metrics()
        metrics_formatted = {
            '累积收益率': f"{metrics['累积收益率']:.2f}%",
            '年化收益率': f"{metrics['年化收益率']:.2f}%",
            '波动率': f"{metrics['波动率']:.2f}%",
            '夏普比率': f"{metrics['夏普比率']:.2f}",
            '最大回撤': f"{metrics['最大回撤']:.2f}%",
            '日胜率': f"{metrics['日胜率']:.2f}%"
        }
        
        # 创建表格
        cell_text = [[k, v] for k, v in metrics_formatted.items()]
        table = ax5.table(cellText=cell_text,
                         colLabels=['指标', '数值'],
                         cellLoc='center',
                         loc='center',
                         bbox=[0.1, 0.1, 0.8, 0.8])
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)
        
        # 设置单元格样式
        for (row, col), cell in table.get_celld().items():
            if row == 0:  # 表头
                cell.set_facecolor('#f0f0f0')
                cell.set_text_props(weight='bold')
            else:  # 数据行
                cell.set_facecolor('#ffffff')
                if col == 0:  # 指标名称列
                    cell.set_text_props(ha='right')
                else:  # 数值列
                    cell.set_text_props(ha='left')
        
        ax5.set_title('策略性能指标', pad=20, fontsize=12)
        ax5.axis('off')
        
        # 保存图表
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            
        # 显示图表
        plt.show()
