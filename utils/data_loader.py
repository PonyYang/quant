import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

class DataLoader:
    def __init__(self):
        self.data = None
        
    def download_data(self, symbol, start_date, end_date=None, interval='1d', market='US'):
        """
        下载历史数据
        
        Parameters:
        -----------
        symbol : str
            股票代码，A股格式如'600000'，美股格式如'AAPL'
        start_date : str
            开始日期，格式：'YYYY-MM-DD'
        end_date : str, optional
            结束日期，格式：'YYYY-MM-DD'
        interval : str, optional
            数据间隔，默认'1d'表示日线数据
        market : str, optional
            市场类型，'US'表示美股，'A'表示A股
            
        Returns:
        --------
        pandas.DataFrame
            历史数据，包含开高低收成交量等信息
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        if market == 'A':
            # 处理A股数据
            try:
                # 获取A股日线数据
                df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date.replace('-', ''), 
                                      end_date=end_date.replace('-', ''), adjust="qfq")
                
                # 重命名列以匹配backtrader要求的格式
                df = df.rename(columns={
                    '日期': 'Date',
                    '开盘': 'Open',
                    '最高': 'High',
                    '最低': 'Low',
                    '收盘': 'Close',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                })
                
                # 设置日期索引
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                self.data = df
                
            except Exception as e:
                print(f"获取A股数据失败: {str(e)}")
                return None
                
        else:
            # 处理美股数据
            ticker = yf.Ticker(symbol)
            self.data = ticker.history(start=start_date, end=end_date, interval=interval)
            
        return self.data
    
    def save_data(self, filepath):
        """
        保存数据到CSV文件
        """
        if self.data is not None:
            self.data.to_csv(filepath)
            
    def load_data(self, filepath):
        """
        从CSV文件加载数据
        """
        self.data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return self.data
