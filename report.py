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
import tables
import datetime
import math
from utils.progress_bar import ProgressBar
from pycommando.commando import command

def calculate_performance(inputfname="~/.quant/simulation.h5"):
    report = {}

    inputFile = tables.openFile(os.path.expanduser(inputfname), "r")
    try:
        tbl = inputFile.getNode("/Performance", classname="Table")

        equity_curve = zip([datetime.datetime.fromordinal(int(x)) for x in tbl.col("date")], tbl.col("value"))
        starting_date, starting_value = equity_curve[0]
        ending_date, ending_value = equity_curve[-1] 

        # Analysis
        max_draw_down_duration = {'days': 0, 'start': None, 'end': None}
        max_draw_down_amount = {'amount': 0.0, 'high': None, 'low': None}
        daily_returns = [10000.0]
        #benchmark_returns = [10000.0]
        #excess_returns = []

        last = equity_curve[0]
        highwater = equity_curve[0] # The highwater date and equity
        lowwater = equity_curve[0] # The highwater date and equity
        for date, equity in equity_curve[1:]:
            # If we have passed the highwater or we are at the end of the simulation
            if equity >= highwater[1] or date == equity_curve[-1][0]:
                drawdown_dur = (date - highwater[0]).days
                drawdown_amt = highwater[1] - lowwater[1] 
                if drawdown_dur > max_draw_down_duration['days']:
                    max_draw_down_duration['days'] = drawdown_dur
                    max_draw_down_duration['start'] = highwater
                    max_draw_down_duration['end'] = (date, equity)
                if drawdown_amt > max_draw_down_amount['amount']:
                    max_draw_down_amount['amount'] = drawdown_amt
                    max_draw_down_amount['high'] = highwater
                    max_draw_down_amount['low'] = lowwater
                highwater = (date, equity)
                lowwater = (date, equity)

            if equity <= lowwater[1]:
                lowwater = (date, equity)

            daily_return = (equity - last[1]) / last[1]
            daily_returns.append((daily_return * daily_returns[-1]) + daily_returns[-1])

            last = (date, equity)

        total_days = (ending_date - starting_date).days
        total_years = float(total_days) / 365.0
        equity_return = ending_value - starting_value
        equity_percent = 100.0 * (equity_return / starting_value)
        cagr = 100.0 * (math.pow((ending_value / starting_value), (1 / total_years)) - 1)
        drawdown_percent = 0.0
        if max_draw_down_amount['high'] != None:
            drawdown_percent = 100.0 * (max_draw_down_amount['amount'] / max_draw_down_amount['high'][1])
      
        report['period'] = total_days
        report['starting_date'] = starting_date
        report['starting_value'] = starting_value
        report['ending_date'] = ending_date
        report['ending_value'] = ending_value
        report['ending_value'] = ending_value
        report['equity_return'] = equity_return
        report['equity_percent'] = equity_percent 
        report['cagr'] = cagr
        report['drawdown_dur'] = max_draw_down_duration['days']
        report['drawdown_amt'] = max_draw_down_amount['amount']
        report['drawdown_per'] = drawdown_percent
        report['initial_pos'] = (starting_date, starting_value)
        report['final_pos'] = (ending_date, ending_value)

        report['orders'] = []
        # Calculate cost-basis/and profit on trades using single-category method
        tbl = inputFile.getNode("/Orders", classname="Table")
        winning = 0
        losing = 0
        largest_winning = (0, "")
        largest_losing = (0, "")
        conseq_win = 0
        conseq_lose = 0
        largest_conseq_win = 0
        largest_conseq_lose = 0
        total_profit = 0
        total_win = 0
        total_lose = 0
        total_trades = 0
        for order in tbl.iterrows():
            o = (datetime.datetime.fromordinal(order['date']).date(), order['executed_quantity'], order['executed_price'], order['basis'], order['order'])
            report['orders'].append(o)
            if order['order_type'] == "SELL":
                total_trades += 1
                profit = (order['executed_price'] - order['basis']) * order['executed_quantity']
                total_profit += profit
                if profit > 0:
                    winning += 1
                    conseq_win += 1
                    total_win += profit
                    if conseq_lose > largest_conseq_lose:
                        largest_conseq_lose = conseq_lose
                    conseq_lose = 0
                elif profit < 0:
                    losing += 1
                    conseq_lose += 1
                    total_lose += profit
                    if conseq_win > largest_conseq_win:
                        largest_conseq_win = conseq_win
                    conseq_win = 0

                if profit > largest_winning[0]:
                    largest_winning = (profit, order['date_str'])
                if profit < largest_losing[0]:
                    largest_losing = (profit, order['date_str'])

        if winning == 0:
            avg_winning = 0
        else:
            avg_winning = total_win / winning
        if losing == 0:
            avg_losing = 0
        else:
            avg_losing = total_lose / losing
        if conseq_win > largest_conseq_win:
            largest_conseq_win = conseq_win
        if conseq_lose > largest_conseq_lose:
            largest_conseq_lose = conseq_lose

        report['total_trades'] = total_trades
        report['winning_trades'] = winning
        report['losing_trades'] = losing
        if total_trades > 0:
            report['avg_trade'] = total_profit / total_trades
        else:
            report['avg_trade'] = 0
        report['avg_winning_trade'] = avg_winning
        report['avg_losing_trade'] = avg_losing
        report['conseq_win'] = largest_conseq_win
        report['conseq_lose'] = largest_conseq_lose
        report['largest_win'] = largest_winning
        report['largest_lose'] = largest_losing

    finally:
        inputFile.close()

    return report

@command("report_performance")
def report_performance(inputfname="~/.quant/simulation.h5"):
    report = calculate_performance(inputfname)
    print
    print "######################################################################################"
    print " Report:", inputfname
    print
    print "Simulation Period: %(period)s days" % report
    print "Starting Value: $%(starting_value)0.2f" % report
    print "Ending Value: $%(ending_value)0.2f" % report
    print "Return: $%(equity_return)0.2f (%(equity_percent)3.2f%%)" % report
    print "CAGR: %(cagr)3.2f%%" % report
    print "Maximum Drawdown Duration: %(drawdown_dur)d days" % report
    print "Maxium Drawdown Amount: $%(drawdown_amt)0.2f (%(drawdown_per)3.2f%%)" % report
    print "Inital Position:", report['starting_date'], report['starting_value']
    print "Final Position:", report['ending_date'], report['ending_value']
    print

    # Calculate cost-basis/and profit on trades using single-category method
    print "Date\t\tQty\tPrice\tBasis\tOrder"
    for order in report['orders']:
        print "%s\t%0.2f\t%0.2f\t%0.2f\t%s" % order

    if report['total_trades'] > 0:
        print
        print "Total # of Trades:", report['total_trades']
        print "# of Winning Trades:", report['winning_trades']
        print "# of Losing Trades:", report['losing_trades']
        print "Percent Profitable:", report['winning_trades'] / report['total_trades']
        print
        print "Average Trade:", report['avg_trade']
        print "Average Winning Trade:", report['avg_winning_trade']
        print "Average Losing Trade:", report['avg_losing_trade']
        print
        print "Max. conseq. Winners:", report['conseq_win']
        print "Max. conseq. Losers:", report['conseq_lose']
        print "Largest Winning Trade:", report['largest_win'][0], report['largest_win'][1]
        print "Largest Losing Trade:", report['largest_lose'][0], report['largest_lose'][1]
    print "######################################################################################"
    print

@command("list_orders")
def list_orders(input_="~/.quant/simulation.h5", node="/Orders"):
    try:
        inputFile = tables.openFile(os.path.expanduser(input_), "r")
        tbl = inputFile.getNode(node, classname="Table")
        for d in tbl.iterrows():
            print d
    finally:
        inputFile.close()
