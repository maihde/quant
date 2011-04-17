#/usr/bin/env python
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
import logging
import datetime
import numpy
import os
import sys
import tables
import math
import yaml
from config import CONFIG
from yahoo import Market
from utils.progress_bar import ProgressBar
from utils.model import *
from utils.market import *
from utils.date import ONE_DAY
from pycommando.commando import command
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.ticker as ticker
import matplotlib.dates as dates

MARKET = Market()

def initialize_position(portfolio, date):
    p = CONFIG['portfolios'][portfolio]

    if not type(date) == datetime.datetime:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")

    # Turn the initial cash value into shares based off the portfolio percentage
    position = {'$': 0.0}
    market = Market()
    for instrument, amt in p.items():
        instrument = instrument.strip()
        if type(amt) == str:
            amt = amt.strip()

        if instrument == "$":
            position[instrument] += float(amt)
        else:
            d = date
            price = market[instrument][d].adjclose
            while price == None:
                # Walk backwards looking for a day that had a close price, but not too far
                # because the given instrument may not exist at any time for the given
                # date or prior to it
                d = d - ONE_DAY
                if (date - d) > datetime.timedelta(days=7):
                    break
                price = market[instrument][d].adjclose
            if price == None:
                # This occurs it the instrument does not exist in the market
                # at the start of the simulation period
                position[instrument] = Position(0.0, 0.0)
                if type(amt) == str and amt.startswith('$'):
                    amt = float(amt[1:])
                    position['$'] += amt
                else:
                    print "Warning.  Non-cash value used for instrument that is not available at start of simulation period"
            else:
                if type(amt) == str and amt.startswith('$'):
                    amt = float(amt[1:])
                    amt = math.floor(amt / price)
                position[instrument] = Position(float(amt), price)
    return position

def write_position(table, position, date):
    for instrument, p in position.items():
        table.row['date'] = date.date().toordinal()
        table.row['date_str'] = str(date.date())
        table.row['symbol'] = instrument 
        if instrument == '$':
            table.row['amount'] = 0
            table.row['value'] = p
        else:
            table.row['amount'] = p.amount
            table.row['basis'] = p.basis
            price = MARKET[instrument][date].adjclose
            if price:
                table.row['value'] = price
            else:
                table.row['value'] = 0.0
        table.row.append()

def write_performance(table, position, date):
    value = 0.0
    for instrument, p in position.items():
        if instrument == '$':
            value += p
        else:
            price = MARKET[instrument][date].adjclose
            if price:
                value += (price * p.amount)

    table.row['date'] = date.date().toordinal()
    table.row['date_str'] = str(date.date())
    table.row['value'] = value
    table.row.append()

def execute_orders(table, position, date, orders):
    for order in orders:
        logging.debug("Executing order %s", order)
        if position.has_key(order.symbol):
            ticker = MARKET[order.symbol]
            if order.order == Order.SELL:
                if order.price_type == Order.MARKET_PRICE:
                    strike_price = ticker[date].adjopen
                elif order.price_type == Order.MARKET_ON_CLOSE:
                    strike_price = ticker[date].adjclose
                else:
                    raise StandardError, "Unsupport price type"

                qty = None
                if order.quantity == "ALL":
                    qty = position[order.symbol].amount
                else:
                    qty = order.quantity

                if qty > position[order.symbol] or qty < 1:
                    logging.warn("Ignoring invalid order %s.  Invalid quantity", order)
                    continue
             
                price_paid = 0.0

                table.row['date'] = date.date().toordinal() 
                table.row['date_str'] = str(date.date())
                table.row['order_type'] = order.order
                table.row['symbol'] = order.symbol
                table.row['order'] = str(order)
                table.row['executed_quantity'] = qty
                table.row['executed_price'] = strike_price
                table.row['basis'] = position[order.symbol].basis 
                table.row.append()

                position[order.symbol].remove(qty, strike_price)
                position['$'] += (qty * strike_price)
                position['$'] -= 9.99 # TODO make trading cost configurable

            elif order.order == Order.BUY:
                if order.price_type == Order.MARKET_PRICE:
                    strike_price = ticker[date].adjopen
                elif order.price_type == Order.MARKET_ON_CLOSE:
                    strike_price = ticker[date].adjclose

                if type(order.quantity) == str and order.quantity[0] == "$":
                    qty = int(float(order.quantity[1:]) / strike_price)
                else:
                    qty = int(order.quantity)

                table.row['date'] = date.date().toordinal() 
                table.row['date_str'] = str(date.date())
                table.row['order_type'] = order.order
                table.row['symbol'] = order.symbol
                table.row['order'] = str(order)
                table.row['executed_quantity'] = qty
                table.row['executed_price'] = strike_price
                table.row['basis'] = 0.0
                table.row.append()

                position[order.symbol].add(qty, strike_price)
                position['$'] -= (qty * strike_price)
                position['$'] -= 9.99


def load_strategy(name):
    mydir = os.path.abspath(os.path.dirname(sys.argv[0]))
    strategydir = os.path.join(mydir, "strategies")
    sys.path.insert(0, strategydir)
    if name in sys.modules.keys():
        reload(sys.modules[name])
    else:
        __import__(name)

    clazz = getattr(sys.modules[name], "CLAZZ")
    sys.path.pop(0)

    return clazz


@command("analyze")
def analyze(strategy_name, portfolio, strategy_params="{}"):
    """Using a given strategy and portfolio, make a trading decision"""
    now = datetime.datetime.today()
    position = initialize_position(portfolio, now)

    # Initialize the strategy
    params = yaml.load(strategy_params)
    strategy_clazz = load_strategy(strategy_name)
    strategy = strategy_clazz(now, now, position, MARKET, params)
    
    orders = strategy.evaluate(now, position, MARKET)

    for order in orders:
        print order

@command("simulate")
def simulate(strategy_name, portfolio, start_date, end_date, output="~/.quant/simulation.h5", strategy_params="{}"):
    """A simple simulator that simulates a strategy that only makes
    decisions at closing.  Only BUY and SELL orders are supported.  Orders
    are only good for the next day.

    A price type of MARKET is executed at the open price the next day.

    A price type of MARKET_ON_CLOSE is executed at the close price the next day.

    A price type of LIMIT will be executed at the LIMIT price the next day if LIMIT
    is between the low and high prices of the day.

    A price type of STOP will be executed at the STOP price the next day if STOP
    is between the low and high prices of the day.

    A price type of STOP_LIMIT will be executed at the LIMIT price the next day if STOP
    is between the low and high prices of the day.
    """

    outputFile = openOutputFile(output)
    # Get some of the tables from the output file
    order_tbl = outputFile.getNode("/Orders")
    postion_tbl = outputFile.getNode("/Position")
    performance_tbl = outputFile.getNode("/Performance")
        
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # Start the simulation at closing of the previous trading day
    now = getPrevTradingDay(start_date)

    try:
        position = initialize_position(portfolio, now)

        # Pre-cache some info to make the simulation faster
        ticker = MARKET["^DJI"].updateHistory(start_date, end_date)
        for symbol in position.keys():
            if symbol != '$':
                MARKET[symbol].updateHistory(start=start_date, end=end_date)
        days = (end_date - start_date).days
        
        # Initialize the strategy
        params = yaml.load(strategy_params)
        strategy_clazz = load_strategy(strategy_name)
        strategy = strategy_clazz(start_date, end_date, position, MARKET, params, outputFile)

        p = ProgressBar(maxValue=days, totalWidth=80)
        print "Starting Simulation"

        while now <= end_date:

            # Write the initial position to the database
            write_position(postion_tbl, position, now)
            write_performance(performance_tbl, position, now)
            
            # Remember 'now' is after closing, so the strategy
            # can use any information from 'now' or earlier
            orders = strategy.evaluate(now, position, MARKET)
               
            # Go to the next day to evalute the orders
            now += ONE_DAY
            while not isTradingDay(now):
                now += ONE_DAY
                p.performWork(1)
                continue
            
            # Execute orders
            execute_orders(order_tbl, position, now, orders)

            # Flush the data to disk
            outputFile.flush()
            p.performWork(1)
            print p, '\r',

        p.updateAmount(p.max)
        print p, '\r',
        print '\n' # End the progress bar here before calling finalize
        orders = strategy.finalize()
    finally:
        outputFile.close()
