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
import tables
import math
from ema import EMA

class RSIData(tables.IsDescription):
    date = tables.TimeCol()
    value = tables.Float32Col()

class RSI(object):

    def __init__(self, period):
        self.value = None
        self.last = None
        self.ema_u = EMA(period)
        self.ema_d = EMA(period)
        self.tbl = None
    
    def setupH5(self, h5file, h5where, h5name):
        if h5file != None and h5where != None and h5name != None:
            self.tbl = h5file.createTable(h5where, h5name, RSIData)

    def update(self, value, date=None):
        if self.last == None:
            self.last = value
        
        U = value - self.last
        D = self.last - value

        self.last = value

        if U > 0:
            D = 0
        elif D > 0:
            U = 0

        self.ema_u.update(U)
        self.ema_d.update(D)

        if self.ema_d.value == 0:
            self.value = 100.0
        else:
            rs = self.ema_u.value / self.ema_d.value
            self.value = 100.0 - (100.0 / (1 + rs))

        if self.tbl != None and date:
            self.tbl.row["date"] = date.date().toordinal()
            self.tbl.row["value"] = self.value
            self.tbl.row.append()
            self.tbl.flush()

        return self.value

if __name__ == "__main__":
    import unittest

    class RSITest(unittest.TestCase):

        def notest_ConstantValueAlgorithm(self):
            rsi = RSI(14)
            self.assertEqual(rsi.value, None)
            self.assertEqual(rsi.last, None)
            for i in xrange(50):
                rsi.update(5.)
                self.assertEqual(rsi.value, 100.0)

        def notest_NoDAlgorithm(self):
            rsi = RSI(14)
            self.assertEqual(rsi.value, None)
            self.assertEqual(rsi.last, None)
                
            rsi.update(5.)    # U = 0, D = 0
            self.assertEqual(rsi.value, 100.0)
            rsi.update(10.)   # U = 5, D = 0
            self.assertEqual(rsi.value, 100.0)
            rsi.update(15.)   # U = 5, D = 0
            self.assertEqual(rsi.value, 100.0)
            rsi.update(20.)   # U = 5, D = 0
            self.assertEqual(rsi.value, 100.0)

        def notest_NoUAlgorithm(self):
            rsi = RSI(14)
            self.assertEqual(rsi.value, None)
            self.assertEqual(rsi.last, None)
                
            rsi.update(50.)   # U = 0, D = 0
            self.assertEqual(rsi.value, 100.0)
            rsi.update(40.)   # U = 0 D = 10
            self.assertEqual(rsi.value, 0.0)
            rsi.update(30.)   # U = 0 D = 10
            self.assertEqual(rsi.value, 0.0)
            rsi.update(20.)   # U = 0 D = 10
            self.assertEqual(rsi.value, 0.0)

        def test_Algorithm(self):
            rsi = RSI(9)
            self.assertEqual(rsi.value, None)
            self.assertEqual(rsi.last, None)
                
            rsi.update(50.)   # U = 0, D = 0, ema_u = 0, ema_d = 0
            self.assertEqual(rsi.value, 100.0)
            rsi.update(40.)   # U = 0 D = 10, ema_u = 0, ema_d = 2, rs = 0
            self.assertEqual(rsi.value, 0.0)
            rsi.update(50.)   # U = 10 D = 0, ema_u = 2, ema_d = 1.6, rs = 1.25, rsi = 55.555555  
            self.assertAlmostEqual(rsi.value, 55.555555555555)

    unittest.main()
