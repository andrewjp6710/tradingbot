import numpy as np

class SimpleBreakoutExample(QCAlgorithm):

    def Initialize(self):
        # Investing a hypothetical 100,000USD 
        self.SetCash(100000)
        
        # Algorithm will backtest with data from Jan 1st 2021 
        #to Jan 1st 2022
        self.SetStartDate(2021,1,1)
        self.SetEndDate(2022,1,1)
        
        # Investing in Qualcomm - a stock which I ran DCFs on and pitched for investment comps
        self.symbol = self.AddEquity("QCOM", Resolution.Daily).Symbol
        
        self.lookback = 25
        self.ceiling, self.floor = 40, 20
        
        #allows for certain amount of loss before it gets hit
        self.initialStopRisk = 0.9
        #how close it will follow asset's price by 
        self.trailingStopRisk = 0.9
        
        # Schedule function 1 minute after every market open
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), \
                        self.TimeRules.AfterMarketOpen(self.symbol, 1), \
                        Action(self.EveryMarketOpen))


    def OnData(self, data):
        # Plot security's price
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)

 
    def EveryMarketOpen(self):
        # Closing price of our stock for the past month
        close = self.History(self.symbol, 31, Resolution.Daily)["close"]
        #calc today's volatility 
        todayvol = np.std(close[1:31])
        #calc yesterday's volatility
        yesterdayvol = np.std(close[0:30])
        
        #average volatility
        deltavol = (todayvol - yesterdayvol) / todayvol
        self.lookback = round(self.lookback * (1 + deltavol))
        
        # upper and lower limit of lockback length
        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor
        
        # List of daily highs
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]
        
        # check we are not currently invested and that there is a breakout
        #a higher than the higest hig from self.high variable(wihout last data point)
        if not self.Securities[self.symbol].Invested and \
                self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1)
            # breakout level
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
        
        
        # implement trading stoploss - checking if we are invested
        if self.Securities[self.symbol].Invested:
            
            # if the order has not been sent yet, send an order
            if not self.Transactions.GetOpenOrders(self.symbol):
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, \
                                        -self.Portfolio[self.symbol].Quantity, \
                                        self.initialStopRisk * self.breakoutlvl)
            
            # save stoploss 
            # update new high if stoploss reached a new high
            # check if stop price not below initial stop price
            if self.Securities[self.symbol].Close > self.highestPrice and \
                    self.initialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
                # Save the new high to highestPrice
                self.highestPrice = self.Securities[self.symbol].Close
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
                self.stopMarketTicket.Update(updateFields)
                
                # print new stop price
                self.Debug(updateFields.StopPrice)
            
            # plot trailing stop price
            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))