import pandas as pd
import numpy as np
import akshare as ak
from scipy import stats
import matplotlib.pyplot as plt
from tqdm import tqdm

class FactorAnalyzer:
    def __init__(self, stock_code, start_date='20200101', end_date='20241231'):
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.load_data()
        
    def load_data(self):
        """加载股票数据"""
        try:
            # 使用akshare获取股票数据
            df = ak.stock_zh_a_hist(symbol=self.stock_code, period="daily",
                                  start_date=self.start_date,
                                  end_date=self.end_date,
                                  adjust="qfq")
            
            # 检查数据是否为空
            if df is None or df.empty:
                raise Exception("获取到的数据为空")
            
            print("原始数据列名:", df.columns.tolist())
            
            # 确保所需的列都存在
            required_columns = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            
            # 重命名存在的列
            rename_dict = {}
            for cn, en in required_columns.items():
                if cn in df.columns:
                    rename_dict[cn] = en
            
            df.rename(columns=rename_dict, inplace=True)
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 按日期升序排序
            df.sort_index(inplace=True)
            
            self.data = df
            print(f"成功加载{len(df)}条数据")
            print("处理后的列名:", df.columns.tolist())
        except Exception as e:
            print(f"加载数据时出错: {e}")
            raise
            
    def calculate_factors(self):
        """计算各种技术因子"""
        df = self.data.copy()
        
        # 1. 动量因子
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
        df['momentum_20'] = df['close'].pct_change(20)
        
        # 2. 波动率因子
        df['volatility_5'] = df['close'].rolling(5).std()
        df['volatility_10'] = df['close'].rolling(10).std()
        df['volatility_20'] = df['close'].rolling(20).std()
        
        # 3. 成交量因子
        df['volume_ma5'] = df['volume'].rolling(5).mean()
        df['volume_ma10'] = df['volume'].rolling(10).mean()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(5).mean()
        
        # 4. 价格技术指标
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal']
        
        # 5. 价格位置指标
        df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / \
                             (df['high'].rolling(20).max() - df['low'].rolling(20).min())
        
        # 计算未来收益率（作为标签）
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_5d'] = df['close'].shift(-5) / df['close'] - 1
        df['future_return_10d'] = df['close'].shift(-10) / df['close'] - 1
        
        self.factor_data = df
        return df
    
    def analyze_factors(self):
        """分析因子与未来收益的相关性"""
        df = self.factor_data.copy()
        
        # 定义要分析的因子列表
        factors = ['momentum_5', 'momentum_10', 'momentum_20',
                  'volatility_5', 'volatility_10', 'volatility_20',
                  'volume_ma5', 'volume_ma10', 'volume_ratio',
                  'rsi', 'macd', 'macd_hist', 'price_position']
        
        # 定义预测周期
        predict_periods = ['future_return_1d', 'future_return_5d', 'future_return_10d']
        
        results = []
        for factor in factors:
            for period in predict_periods:
                # 确保因子和收益率数据对齐
                factor_data = pd.DataFrame({
                    'factor': df[factor],
                    'return': df[period]
                }).dropna()
                
                if len(factor_data) > 0:
                    # 计算IC值
                    ic = stats.spearmanr(factor_data['factor'], factor_data['return'])[0]
                    
                    # 计算分组收益差异
                    factor_data['group'] = pd.qcut(factor_data['factor'], q=5, labels=['G1', 'G2', 'G3', 'G4', 'G5'])
                    group_returns = factor_data.groupby('group', observed=True)['return'].mean()
                    long_short_return = group_returns['G5'] - group_returns['G1']
                    
                    results.append({
                        'factor': factor,
                        'period': period,
                        'ic': ic,
                        'long_short_return': long_short_return,
                        'sample_size': len(factor_data)
                    })
                
        return pd.DataFrame(results)
    
    def get_strategy_suggestion(self):
        """根据因子分析结果给出策略建议"""
        analysis_results = self.analyze_factors()
        
        # 找出最佳IC因子
        best_ic_idx = analysis_results['ic'].abs().idxmax()
        best_ic_factor = analysis_results.loc[best_ic_idx]
        
        # 找出最佳收益因子
        best_return_idx = analysis_results['long_short_return'].abs().idxmax()
        best_return_factor = analysis_results.loc[best_return_idx]
        
        # 生成策略建议
        suggestions = []
        
        # 基于IC的建议
        ic_direction = "正" if best_ic_factor['ic'] > 0 else "负"
        period_map = {
            'future_return_1d': '1天',
            'future_return_5d': '5天',
            'future_return_10d': '10天'
        }
        factor_map = {
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
        
        factor_name = factor_map.get(best_ic_factor['factor'], best_ic_factor['factor'])
        period_name = period_map.get(best_ic_factor['period'], best_ic_factor['period'])
        
        if abs(best_ic_factor['ic']) > 0.1:
            suggestions.append(
                f"主要策略信号：观察{factor_name}，当该指标{'上升' if best_ic_factor['ic'] > 0 else '下降'}时，"
                f"表明未来{period_name}可能{'上涨' if best_ic_factor['ic'] > 0 else '下跌'}的概率较大"
            )
            
            # 添加具体操作建议
            if best_ic_factor['ic'] > 0:
                suggestions.append(
                    f"建议操作：当{factor_name}突破近期高点时买入，持仓{period_name}；"
                    f"当{factor_name}跌破近期低点时卖出"
                )
            else:
                suggestions.append(
                    f"建议操作：当{factor_name}跌破近期低点时买入，持仓{period_name}；"
                    f"当{factor_name}突破近期高点时卖出"
                )
        else:
            suggestions.append(
                f"警示：目前所有技术指标的预测能力都较弱（最佳IC={abs(best_ic_factor['ic']):.3f}），"
                "建议降低仓位，谨慎操作"
            )
        
        # 添加风险提示
        if abs(best_ic_factor['ic']) > 0.1:
            suggestions.append(
                "风险控制：\n"
                "1. 建议单次操作仓位不超过30%\n"
                "2. 当亏损超过5%时坚决止损\n"
                "3. 获利10%以上时可以考虑部分止盈"
            )
        
        return {
            'best_ic_factor': {
                'factor': best_ic_factor['factor'],
                'period': best_ic_factor['period'],
                'ic': best_ic_factor['ic']
            },
            'best_return_factor': {
                'factor': best_return_factor['factor'],
                'period': best_return_factor['period'],
                'return': best_return_factor['long_short_return']
            },
            'suggestions': suggestions
        }
    
    def plot_factor_analysis(self, factor_name):
        """绘制因子分析图"""
        df = self.factor_data.copy()
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        
        # 1. 因子值随时间的变化
        axes[0, 0].plot(df.index, df[factor_name])
        axes[0, 0].set_title(f'{factor_name}因子时间序列')
        axes[0, 0].set_xlabel('日期')
        axes[0, 0].set_ylabel('因子值')
        
        # 2. 因子值的分布
        axes[0, 1].hist(df[factor_name].dropna(), bins=50)
        axes[0, 1].set_title(f'{factor_name}因子分布')
        axes[0, 1].set_xlabel('因子值')
        axes[0, 1].set_ylabel('频数')
        
        # 3. 因子值与未来收益的散点图
        axes[1, 0].scatter(df[factor_name], df['future_return_5d'], alpha=0.5)
        axes[1, 0].set_title(f'{factor_name}因子与5日收益率散点图')
        axes[1, 0].set_xlabel('因子值')
        axes[1, 0].set_ylabel('5日收益率')
        
        # 4. 分组收益分析
        factor_data = pd.DataFrame({
            'factor': df[factor_name],
            'return': df['future_return_5d']
        }).dropna()
        factor_data['group'] = pd.qcut(factor_data['factor'], q=5, labels=['G1', 'G2', 'G3', 'G4', 'G5'])
        group_returns = factor_data.groupby('group', observed=True)['return'].mean()
        axes[1, 1].bar(range(5), group_returns)
        axes[1, 1].set_title(f'{factor_name}因子分组收益分析')
        axes[1, 1].set_xlabel('分组')
        axes[1, 1].set_ylabel('平均收益率')
        axes[1, 1].set_xticks(range(5))
        axes[1, 1].set_xticklabels(group_returns.index)
        
        plt.tight_layout()
        plt.show()
