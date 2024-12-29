import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd

from analysis.factor_analysis import FactorAnalyzer

def format_period(period):
    """将预测周期转换为更易读的格式"""
    if period == 'future_return_1d':
        return '1天'
    elif period == 'future_return_5d':
        return '5天'
    elif period == 'future_return_10d':
        return '10天'
    return period

def format_factor(factor):
    """将因子名称转换为更易读的格式"""
    factor_names = {
        'volume_ma5': '5日成交量均线',
        'volume_ma10': '10日成交量均线',
        'volume_ratio': '成交量比率',
        'momentum_5': '5日动量',
        'momentum_10': '10日动量',
        'momentum_20': '20日动量',
        'volatility_5': '5日波动率',
        'volatility_10': '10日波动率',
        'volatility_20': '20日波动率',
        'rsi': 'RSI指标',
        'macd': 'MACD',
        'macd_hist': 'MACD柱',
        'price_position': '价格位置'
    }
    return factor_names.get(factor, factor)

def print_factor_analysis(results):
    """打印因子分析结果"""
    print("\n=== 因子分析摘要 ===")
    
    # 按预测周期分组显示最有效的因子
    periods = ['future_return_1d', 'future_return_5d', 'future_return_10d']
    
    for period in periods:
        period_results = results[results['period'] == period].copy()
        period_results['abs_ic'] = period_results['ic'].abs()
        top_factors = period_results.nlargest(3, 'abs_ic')
        
        print(f"\n{format_period(period)}预测效果最好的因子：")
        for _, row in top_factors.iterrows():
            direction = "正" if row['ic'] > 0 else "负"
            print(f"- {format_factor(row['factor'])}:")
            print(f"  • 与收益{direction}相关，IC值为{row['ic']:.3f}")
            print(f"  • 多空组合收益率为{row['long_short_return']*100:.2f}%")

def print_strategy_suggestions(suggestions):
    """打印策略建议"""
    print("\n=== 交易策略建议 ===")
    
    # 最佳IC因子
    best_ic = suggestions['best_ic_factor']
    print(f"\n1. 最可靠的信号 - {format_factor(best_ic['factor'])}")
    print(f"   预测时间范围：{format_period(best_ic['period'])}")
    direction = "正" if best_ic['ic'] > 0 else "负"
    print(f"   相关方向：{direction}相关（IC = {best_ic['ic']:.3f}）")
    print(f"   使用建议：{format_factor(best_ic['factor'])}越{'高' if best_ic['ic'] > 0 else '低'}，未来{format_period(best_ic['period'])}的上涨概率越{'大' if best_ic['ic'] > 0 else '小'}")
    
    # 最佳收益因子
    best_return = suggestions['best_return_factor']
    print(f"\n2. 最佳收益信号 - {format_factor(best_return['factor'])}")
    print(f"   预测时间范围：{format_period(best_return['period'])}")
    print(f"   策略收益：{best_return['return']*100:.2f}%")
    direction = "高" if best_return['return'] > 0 else "低"
    print(f"   使用建议：做多{format_factor(best_return['factor'])}{direction}的股票，做空{format_factor(best_return['factor'])}{'低' if best_return['return'] > 0 else '高'}的股票")
    
    print("\n3. 具体操作建议：")
    for suggestion in suggestions['suggestions']:
        print(f"   • {suggestion}")

def main():
    # 设置控制台输出编码
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 创建因子分析器
    analyzer = FactorAnalyzer('600570')
    
    # 计算因子
    print("正在计算技术因子...")
    analyzer.calculate_factors()
    
    # 分析因子
    print("\n分析因子与收益的关系...")
    analysis_results = analyzer.analyze_factors()
    
    # 打印分析结果
    print_factor_analysis(analysis_results)
    
    # 获取并打印策略建议
    suggestions = analyzer.get_strategy_suggestion()
    print_strategy_suggestions(suggestions)
    
    # 绘制最佳因子的分析图
    print("\n正在生成最佳因子的详细分析图表...")
    analyzer.plot_factor_analysis(suggestions['best_ic_factor']['factor'])

if __name__ == "__main__":
    main()
