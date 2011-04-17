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
import tables

###############################################################################
# Data structures used by filters/strategies/riskmanagement
###############################################################################
class Order(object):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"
    BUY_TO_OPEN = "BUY_TO_OPEN"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"
    SELL_TO_OPEN = "SELL_TO_OPEN"

    MARKET_PRICE = "MARKET_PRICE"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

    def __init__(self, order, symbol, quantity, price_type, stop=None, limit=None):
        self._order = order
        self._sym = symbol
        self._qty = quantity
        self._price_type = price_type
        self._stop = stop
        self._limit = limit

    # Use propreties so that the Order class attributes behave as 
    # readonly
    def getOrder(self):
        return self._order
    order = property(fget=getOrder)
    
    def getSymbol(self):
        return self._sym
    symbol = property(fget=getSymbol)

    def getQuantity(self):
        return self._qty
    quantity = property(fget=getQuantity)

    def getPriceType(self):
        return self._price_type
    price_type = property(fget=getPriceType)

    def getStop(self):
        return self._stop
    stop = property(fget=getStop)

    def getLimit(self):
        return self._limit
    limit = property(fget=getLimit)

    def __str__(self):
        if type(self._qty) == "float":
            qty = "$%0.2f" % self.quantity
        else:
            qty = self.quantity
        res = "%s %s %s at %s" % (self.order, qty, self.symbol, self.price_type)
        if self.price_type in (Order.LIMIT):
           res += " " + self.limit
        elif self.price_type in (Order.STOP):
           res += " " + self.stop
        elif self.price_type in (Order.STOP_LIMIT):
           res += " " + self.limit + " when " + self.stop
        return res

class Position(object):
    def __init__(self, amount, basis):
        self.amount = amount
        self.basis = basis

    def add(self, qty, price_paid):
        v = (self.amount * self.basis) + (qty * price_paid)
        self.amount += qty
        self.basis = v / self.amount

    def remove(self, qty, price_sold):
        self.amount -= qty

    def __str__(self):
        return str(self.amount)

###############################################################################
# PyTables data structures
###############################################################################
class OrderData(tables.IsDescription):
    date = tables.TimeCol()
    order_type = tables.StringCol(16)
    symbol = tables.StringCol(16)
    date_str = tables.StringCol(16)
    order = tables.StringCol(64)
    executed_quantity = tables.Int32Col()
    executed_price = tables.Float32Col()
    basis = tables.Float32Col()

class PositionData(tables.IsDescription):
    date = tables.TimeCol()
    date_str = tables.StringCol(16)
    symbol = tables.StringCol(16)
    amount = tables.Int32Col()
    value = tables.Float32Col()
    basis = tables.Float32Col() # The basis using single-category averaging

class PerformanceData(tables.IsDescription):
    date = tables.TimeCol()
    date_str = tables.StringCol(16)
    value = tables.Float32Col()

###############################################################################
# Helper functions
###############################################################################
def openOutputFile(filepath):
    """After opening the file, get the tables like this.
   
    file.getNode("/Orders")
    file.getNode("/Position")
    file.getNode("/Performance")
    """
    try:
        os.remove(os.path.expanduser(filepath))
    except OSError:
        pass
    outputFile = tables.openFile(os.path.expanduser(filepath), mode="w", title="Quant Simulation")
    outputFile.createTable("/", 'Orders', OrderData)
    outputFile.createTable("/", 'Position', PositionData)
    outputFile.createTable("/", 'Performance', PositionData)
    return outputFile
