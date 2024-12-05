import backtrader as bt
import matplotlib.pyplot as plt
from dataloader import TushareData
from strategy import SimpleMovingAverage
from strategy import DoubleSMA
from strategy import RSI_SMA
from strategy import MACD
from strategy import RSI_SMA_MACD
from strategy import MeanReversion
from strategy import MeanReversionByStop

# plt.rcParams["font.sans-serif"] = ['SimHei']
# plt.rcParams["axes.unicode_minus"] = False

if __name__ == '__main__':
    # Add DataSet
    dataset = TushareData(isplot=True)
    # 汽车
    stock_ids = "600104.SH,000625.SZ,603912.SH"
    # 黄金
    # stock_ids = "601069.SH,600988.SH,600489.SH"
    # stock_ids = "603912.SH"
    data = dataset.fetch_data(stock_ids = stock_ids,start_time = "20231101",end_time = "20240901")
    
    # 历史收益率、波动方差、标准差计算

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(MACD)

    # Add the Data Feed to Cerebro
    for i in range(len(data)):
        cerebro.adddata(data[i])

    # Add addanalyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.002)

    # Add Sizer
    cerebro.addsizer(bt.sizers.PercentSizer, percents=33)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    result = cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('夏普比例: ', result[0].analyzers.SharpeRatio.get_analysis()['sharperatio'])
    print('最大回撤: ', result[0].analyzers.DrawDown.get_analysis()['drawdown'])

    cerebro.plot()