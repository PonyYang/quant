import backtrader as bt

class MACrossStrategy(bt.Strategy):
    """
    移动平均线交叉策略
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    
    params = (
        ('short_period', 20),  # 短期均线周期
        ('long_period', 50),   # 长期均线周期
    )
    
    def __init__(self):
        # 计算移动平均线
        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)
        
    def next(self):
        if not self.position:  # 还没有仓位
            if self.crossover > 0:  # 金叉买入
                self.buy()
        else:  # 已有仓位
            if self.crossover < 0:  # 死叉卖出
                self.sell()
                
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行价格: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'卖出执行价格: {order.executed.price:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
            
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
