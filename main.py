from utils.data_loader import DataLoader
from backtest.backtest_engine import BacktestEngine
from strategies.macd_histogram_strategy import MACDHistogramStrategy
from analysis.performance_analyzer import PerformanceAnalyzer
import os
import pandas as pd
import numpy as np
import akshare as ak
import matplotlib
matplotlib.use('TkAgg')  # 设置matplotlib后端
import matplotlib.pyplot as plt

def get_stock_name(stock_code):
    """获取股票中文名称"""
    try:
        stock_info = ak.stock_individual_info_em(symbol=stock_code)
        return stock_info.iloc[0]['value']
    except:
        return stock_code

def main():
    # 设置股票代码和回测区间
    stock_code = '600570'
    stock_name = get_stock_name(stock_code)
    start_date = '2020-01-01'
    end_date = '2024-12-31'
    
    print(f"\n=== 开始回测 {stock_code} {stock_name} ===".encode('gbk').decode('gbk'))
    print(f"回测区间: {start_date} 至 {end_date}".encode('gbk').decode('gbk'))
    
    # 创建输出目录
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 创建数据目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # 初始化数据加载器
    loader = DataLoader()
    
    # 下载A股数据
    data = loader.download_data(stock_code, start_date, end_date, market='A')
    
    if data is None:
        print("获取数据失败，请检查网络连接和股票代码是否正确")
        return
    
    # 保存数据
    loader.save_data(os.path.join(data_dir, f'{stock_code}.csv'))
    
    # 初始化回测引擎
    engine = BacktestEngine(initial_cash=100000.0)
    
    # 添加数据和策略
    engine.add_data(data, name=f'{stock_code} {stock_name}')
    engine.add_strategy(MACDHistogramStrategy, 
                       fastperiod=12,     # 使用日线级别的MACD参数
                       slowperiod=26,
                       signalperiod=9)
    
    # 运行回测
    results = engine.run()
    
    # 获取回测统计
    stats = engine.get_performance_stats()
    print("\n=== 回测结果 ===".encode('gbk').decode('gbk'))
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}".encode('gbk').decode('gbk'))
        else:
            print(f"{key}: {value}".encode('gbk').decode('gbk'))
    
    # 计算每日收益率
    portfolio_values = []
    for i in range(len(data)):
        if i < len(engine.portfolio_values):
            portfolio_values.append(engine.portfolio_values[i])
        else:
            portfolio_values.append(portfolio_values[-1] if portfolio_values else 100000.0)
    
    portfolio_values = pd.Series(portfolio_values, index=data.index)
    portfolio_values = portfolio_values.ffill().bfill()
    initial_value = 100000.0  # 初始资金
    
    # 打印投资组合价值序列
    print("\n=== 投资组合价值序列 ===")
    print(portfolio_values)
    
    print("\n=== 投资组合价值 ===")
    print(f"初始价值: {initial_value:.2f}")
    print(f"最终价值: {portfolio_values.iloc[-1]:.2f}")
    print(f"收益率: {(portfolio_values.iloc[-1]/initial_value - 1) * 100:.2f}%")
    
    # 计算收益率序列
    daily_returns = portfolio_values.pct_change().fillna(0) * 100  # 日收益率（百分比）
    
    # 性能分析
    analyzer = PerformanceAnalyzer(portfolio_values, stock_code)
    metrics = analyzer.calculate_metrics()
    
    print("\n=== 策略性能指标 ===")
    print(f"累积收益率: {metrics['累积收益率']:.4f}")
    print(f"年化收益率: {metrics['年化收益率']:.4f}")
    print(f"夏普比率: {metrics['夏普比率']:.4f}")
    print(f"最大回撤: {metrics['最大回撤']:.4f}")
    print(f"日胜率: {metrics['日胜率']:.4f}")
    
    # 绘制汇总图表
    analyzer.plot_summary(os.path.join(output_dir, f'strategy_summary_{stock_code}.png'))
    
if __name__ == "__main__":
    main()
