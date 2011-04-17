# A module for all built-in commands.
# vim: sw=4: et
LICENSE="""
Copyright (C) 2011  Michael Ihde

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
import datetime
import os
import tables
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.ticker as ticker

from indicators.ema import EMA
from indicators.rsi import RSI 
from indicators.simplevalue import SimpleValue
from strategy import Strategy
from utils.model import Order
from utils.date import ONE_DAY

class SymbolData(tables.IsDescription):
    date = tables.TimeCol()
    closing = tables.Float32Col()
    ema_short = tables.Float32Col()
    ema_long = tables.Float32Col()

class Trending(Strategy):
    DEF_LONG_DAYS = 200
    DEF_SHORT_DAYS = 15
    DEF_RSI_PERIOD = 14

    def __init__(self, start_date, end_date, initial_position, market, params, h5file=None):
        Strategy.__init__(self, start_date, end_date, initial_position, market, params, h5file)
        for symbol in initial_position.keys():
            if symbol == "$":
                continue

            self.addIndicator(symbol, "value", SimpleValue()) 
            try:
                short = params['short']
            except KeyError:
                short = Trending.DEF_SHORT_DAYS
            self.addIndicator(symbol, "short", EMA(short)) 
            try:
                long_ = params['long']
            except KeyError:
                long_ = Trending.DEF_LONG_DAYS
            self.addIndicator(symbol, "long", EMA(long_)) 
            try:
                rsi = params['rsi']
            except KeyError:
                rsi = Trending.DEF_RSI_PERIOD
            self.addIndicator(symbol, "rsi", RSI(rsi)) 

        # Backfill the indicators 
        try:
            backfill = params['backfill']
        except KeyError:
            backfill = long_

        d = start_date - (backfill * ONE_DAY)
        self.updateIndicators(d, start_date)
    
    def evaluate(self, date, position, market):
        self.updateIndicators(date)
       
        # Based of indicators, create signals
        buyTriggers = []
        sellTriggers = []
        for symbol, qty in position.items():
            if symbol != '$':
                ticker = market[symbol]
                close_price = ticker[date].adjclose
                if self.indicators[symbol]["short"].value < self.indicators[symbol]["long"].value:
                    sellTriggers.append(symbol)
                elif self.indicators[symbol]["short"].value > self.indicators[symbol]["long"].value:
                    buyTriggers.append(symbol)
       
        # Using the basic MoneyManagement strategy, split all available cash
        # among all buy signals
        # Evaluate sell orders
        orders = []
        for sellTrigger in sellTriggers:
            if position[sellTrigger].amount > 0:
                orders.append(Order(Order.SELL, sellTrigger, "ALL", Order.MARKET_PRICE))

        # Evaluate all buy orders
        if len(buyTriggers) > 0:
            cash = position['$']
            cashamt = position['$'] / len(buyTriggers)
            for buyTrigger in buyTriggers:
                ticker = market[buyTrigger]
                close_price = ticker[date].adjclose
                if close_price != None:
                    estimated_shares = int(cashamt / close_price)
                    # Only issues orders that buy at least one share
                    if estimated_shares >= 1:
                        orders.append(Order(Order.BUY, buyTrigger, "$%f" % cashamt, Order.MARKET_PRICE))
                
        return orders

CLAZZ = Trending
