# 量化交易系统

这是一个基于Python的量化交易系统，支持以下功能：

- 数据获取和处理
- 策略回测
- 数据统计分析
- 性能评估

## 项目结构

```
quant/
├── data/              # 存放历史数据
├── strategies/        # 交易策略
├── utils/            # 工具函数
├── backtest/         # 回测模块
└── analysis/         # 分析模块
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 安装依赖包
2. 在strategies目录下编写自己的交易策略
3. 运行回测脚本进行策略回测
4. 使用分析模块评估策略性能
