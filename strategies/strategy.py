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
from utils.date import ONE_DAY
import tables

class Strategy(object):
    def __init__(self, start_date, end_date, initial_position, market, params, h5file=None):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_position = initial_position
        self.market = market
        self.params = params

        # Manage indicators, the dictionary is:
        #  key = symbol
        #  value = dictionary(key="indicator name", value=indicator)
        self.indicators = {}

        # If the strategy was passed h5 info, use it to store information
        self.h5file = h5file
        if h5file != None:
            self.indicator_h5group = h5file.createGroup("/", "Indicators")
            self.strategy_h5group = h5file.createGroup("/", "Strategy")

    def addIndicator(self, symbol, name, indicator):
        if not self.indicators.has_key(symbol):
            self.indicators[symbol] = {}
        self.indicators[symbol][name] = indicator

        if self.h5file != None:
            try:
                symgroup = self.h5file.getNode(self.indicator_h5group._v_pathname, symbol, classname="Group")  
            except tables.NoSuchNodeError:
                symgroup = self.h5file.createGroup(self.indicator_h5group._v_pathname, symbol)

            if self.h5file and self.indicator_h5group:
                indicator.setupH5(self.h5file, symgroup, name)

    def removeIndicator(self, symbol, name):
        del self.indicators[symbol][name]

    def updateIndicators(self, start_date, end_date=None):
        for symbol, indicators in self.indicators.items():
            ticker = self.market[symbol]
            if end_date != None:
                quotes = ticker[start_date:end_date] # Call this to cache everything
                end = end_date
            else:
                end = start_date + ONE_DAY

            d = start_date
            while d < end:
                quote = ticker[d]
                if quote.adjclose != None:
                    for indicator in indicators.values():
                        indicator.update(quote.adjclose, d)
                d += ONE_DAY

    def evaluate(self, date, position):
        raise NotImplementedError

    def finalize(self):
        self.h5file = None
        self.indicator_h5group = None
        self.strategy_h5group = None
