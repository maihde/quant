#!/usr/bin/env python
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
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.ticker as ticker
import matplotlib.dates as dates
from pycommando.commando import command
from utils.YahooQuote import *

@command("db_ls")
def list():
    """
    Lists the symbols that are in the database
    """
    return Market().cache.symbols()

@command("db_up")
def update(symbol):
    """
    Updates the historical daily prices for all stocks
    currently in the database.
    """
    market = Market()
    try:
        ticker = market[symbol]
        if ticker != None:
            ticker.updateHistory()
    except IndexError:
        market.updateHistory()

@command("db_flush")
def flush():
    """
    Completely removes the yahoo cache
    """
    os.remove(YahooQuote.CACHE) 
    Market()._dbInit()

@command("db_load")
def load(symbol=None):
    """
    Load's historical prices for a given ticker or index
    symbol from 1950 until today.  This may take a long time,
    especially if you don't provide a symbol because it will
    cache all major indexes from 1950 until today.
    """
    market = Market()
    if symbol == None:
        market.fetchHistory()
    else:
        ticker = market[symbol]
        if ticker != None:
            ticker.fetchHistory()

@command("db_fetch")
def fetch(symbol, start="today", end="today"):
    """
    Prints the daily price for the stock on a given day.
    """
    if start.upper() == "TODAY":
        day_start = datetime.date.today()
    else:
        day_start = datetime.datetime.strptime(start, "%Y-%m-%d")
    day_start = (day_start.year * 10000) + (day_start.month * 100) + day_start.day

    if end.upper() == "TODAY":
        day_end = None
    else:
        day_end = datetime.datetime.strptime(end, "%Y-%m-%d")
        day_end = (day_end.year * 10000) + (day_end.month * 100) + day_end.day

    ticker = Market()[symbol]
    if ticker != None:
        if day_end == None:
            return ticker[day_start]
        else:
            return ticker[day_start:day_end]

@command("db_plot")
def plot(symbol, start, end):
    """
    Prints the daily price for the stock on a given day.
    """

    quotes = fetch(symbol, start, end)
    x_data = [QuoteDate(q.date).toDateTime() for q in quotes]
    y_data = [q.adjclose for q in quotes]

    fig = plt.figure()
    fig.canvas.set_window_title("%s %s-%s" % (symbol, start, end))
    sp = fig.add_subplot(111)
    sp.plot(x_data, y_data, '-')
    x_locator = dates.AutoDateLocator()
    sp.xaxis.set_major_locator(x_locator)
    sp.xaxis.set_major_formatter(dates.AutoDateFormatter(x_locator))
    fig.autofmt_xdate()
    fig.show()
