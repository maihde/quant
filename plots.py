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
import sys
import tables
from utils.date import ONE_DAY
from pycommando.commando import command
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.ticker as ticker
import matplotlib.dates as dates

@command("show")
def show():
    """Shows all plots that have been created, only necessary if you are
    creating plots in a script.  Typically the last line of a script that
    creates plots will be 'show'.
    """
    plt.show()

@command("plot")
def plot(input_="~/.quant/simulation.h5", node="/Performance", x="date", y="value"):
    try:
        inputFile = tables.openFile(os.path.expanduser(input_), "r")
        tbl = inputFile.getNode(node, classname="Table")

        x_data = tbl.col(x)
        y_data = tbl.col(y)
    finally:
        inputFile.close()

    fig = plt.figure()
    sp = fig.add_subplot(111)
    sp.set_title(input_)
    sp.plot(x_data, y_data, '-')
    
    x_locator = dates.AutoDateLocator()
    sp.xaxis.set_major_locator(x_locator)
    sp.xaxis.set_major_formatter(dates.AutoDateFormatter(x_locator))

    #def format_date(value, pos=None):
    #    return datetime.datetime.fromordinal(int(value)).strftime("%Y-%m-%d")
    #sp.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    fig.autofmt_xdate()
    fig.show()

@command("plot_indicators")
def plot_indicators(symbol="", indicator="all", input_="~/.quant/simulation.h5", x="date", y="value"):

    inputFile = tables.openFile(os.path.expanduser(input_), "r")
    try:
        symbols = []
        if symbol == "":
            symbols = [grp._v_name for grp in inputFile.iterNodes("/Indicators", classname="Group")]
        else:
            symbols = (symbol,)

        for sym in symbols:
            fig = plt.figure()
            lines = []
            legend = []
            sp = fig.add_subplot(111)
            sp.set_title(input_ + " " + sym)
            for tbl in inputFile.iterNodes("/Indicators/" + sym, classname="Table"):
                if indicator == "all" or tbl._v_name == indicator:
                    x_data = tbl.col(x)
                    y_data = tbl.col(y)
                    line = sp.plot(x_data, y_data, '-')
                    lines.append(line)
                    legend.append(tbl._v_name)
                    x_locator = dates.AutoDateLocator()
                    sp.xaxis.set_major_locator(x_locator)
                    sp.xaxis.set_major_formatter(dates.AutoDateFormatter(x_locator))
            legend = fig.legend(lines, legend, loc='upper right')
            fig.autofmt_xdate()
            fig.show()
    finally:
        inputFile.close()
