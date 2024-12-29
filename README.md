# 量化交易系统

这是一个基于Python的量化交易系统，用于股票交易策略的回测和分析。系统提供完整的数据获取、策略回测、性能分析等功能。

## 主要功能

- 自动获取A股历史数据（基于akshare）
- 支持MACD等技术指标策略
- 完整的回测引擎
- 详细的性能分析报告
- 可视化交易结果

## 项目结构

```
quant/
├── data/              # 存放历史数据
├── output/            # 输出结果（图表、报告等）
├── strategies/        # 交易策略实现
│   └── macd_histogram_strategy.py    # MACD策略
├── utils/            # 工具函数
│   └── data_loader.py               # 数据加载器
├── backtest/         # 回测模块
│   └── backtest_engine.py          # 回测引擎
├── analysis/         # 分析模块
│   └── performance_analyzer.py     # 性能分析器
├── main.py          # 主程序
└── requirements.txt  # 项目依赖
```

## 环境要求

- Python 3.7+
- 依赖包：pandas, numpy, akshare, matplotlib

## 安装步骤

1. 克隆项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 在 `main.py` 中设置回测参数：
   - 股票代码
   - 回测起止日期
   - 初始资金

2. 运行回测：
```bash
python main.py
```

3. 查看结果：
   - 回测结果将保存在 `output` 目录
   - 包括绩效报告和图表分析

## 策略开发

1. 在 `strategies` 目录下创建新的策略类
2. 继承基础策略类并实现必要的方法：
   - `initialize()`: 策略初始化
   - `on_bar()`: 处理每个交易周期的数据

## 输出结果

- 回测统计指标
  - 总收益率
  - 年化收益率
  - 最大回撤
  - 夏普比率
- 交易记录
- 收益曲线图

## 注意事项

- 数据来源为 akshare，请确保网络连接正常
- 回测结果仅供参考，实盘交易需要考虑更多市场因素
- 建议先使用小规模数据进行测试
