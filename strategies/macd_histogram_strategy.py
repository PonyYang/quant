import backtrader as bt
import numpy as np

class MACDHistogramStrategy(bt.Strategy):
    params = (
        ('fastperiod', 12),
        ('slowperiod', 26),
        ('signalperiod', 9),
        ('exit_profit_pct', 0.15),     # 止盈比例
        ('exit_loss_pct', 0.07),       # 止损比例
        ('trend_ema_period', 60),      # 趋势判断EMA周期
        ('volume_ma_period', 20),      # 成交量MA周期
        ('macd_threshold', 0.0),       # MACD柱状图阈值
    )

    def __init__(self):
        # MACD指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fastperiod,
            period_me2=self.p.slowperiod,
            period_signal=self.p.signalperiod
        )
        
        # MACD柱状图
        self.macd_hist = self.macd.macd - self.macd.signal
        
        # 趋势判断EMA
        self.trend_ema = bt.indicators.EMA(self.data.close, period=self.p.trend_ema_period)
        
        # 成交量MA
        self.volume_ma = bt.indicators.SMA(self.data.volume, period=self.p.volume_ma_period)
        
        # 记录买入价格
        self.buy_price = None
        
        # 用于防止重复信号
        self.order = None
        self.last_operation = None
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
            
        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
            
        self.log(f'交易利润: 毛利润={trade.pnl:.2f}, 净利润={trade.pnlcomm:.2f}')
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}'.encode('gbk').decode('gbk'))
        
    def should_buy(self):
        # 1. MACD柱状图由负转正
        curr_hist = self.macd_hist[0]  # 当前柱状图
        prev_hist = self.macd_hist[-1] if len(self.macd_hist) > 1 else 0  # 前一个柱状图
        
        macd_cross_up = prev_hist < self.p.macd_threshold and curr_hist > self.p.macd_threshold
        
        # 2. 价格在趋势线上方
        price_above_trend = self.data.close[0] > self.trend_ema[0]
        
        # 3. 成交量放大
        volume_increase = self.data.volume[0] > self.volume_ma[0] * 1.2
        
        # 4. MACD快线在零轴上方
        macd_above_zero = self.macd.macd[0] > 0
        
        return (macd_cross_up and price_above_trend and volume_increase and macd_above_zero and
                self.last_operation != 'buy')
                
    def should_sell(self):
        if not self.position:
            return False
            
        # 1. 止盈
        if self.buy_price:
            current_profit_pct = (self.data.close[0] - self.buy_price) / self.buy_price
            if current_profit_pct >= self.p.exit_profit_pct:
                self.log(f'触发止盈: 当前收益率={current_profit_pct*100:.2f}%')
                return True
                
        # 2. 止损
        if self.buy_price:
            current_loss_pct = (self.buy_price - self.data.close[0]) / self.buy_price
            if current_loss_pct >= self.p.exit_loss_pct:
                self.log(f'触发止损: 当前亏损率={current_loss_pct*100:.2f}%')
                return True
                
        # 3. MACD柱状图由正转负
        curr_hist = self.macd_hist[0]
        prev_hist = self.macd_hist[-1] if len(self.macd_hist) > 1 else 0
        
        macd_cross_down = prev_hist > -self.p.macd_threshold and curr_hist < -self.p.macd_threshold
        
        # 4. 价格跌破趋势线
        price_below_trend = self.data.close[0] < self.trend_ema[0]
        
        if macd_cross_down:
            self.log('MACD柱状图死叉卖出信号')
        elif price_below_trend:
            self.log('价格跌破趋势线卖出信号')
            
        return (macd_cross_down or price_below_trend) and self.last_operation != 'sell'
        
    def next(self):
        if self.order:
            return
            
        if not self.position:  # 没有持仓
            if self.should_buy():
                size = int(self.broker.getcash() * 0.95 / self.data.close[0])  # 使用95%资金买入
                self.order = self.buy(size=size)
                self.last_operation = 'buy'
                self.log(f'买入信号: MACD柱状图金叉, 价格={self.data.close[0]:.2f}')
                
        else:  # 有持仓
            if self.should_sell():
                self.order = self.sell(size=self.position.size)
                self.last_operation = 'sell'
                self.log(f'卖出信号: 价格={self.data.close[0]:.2f}')
