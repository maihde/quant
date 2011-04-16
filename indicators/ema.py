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

class EMAData(tables.IsDescription):
    date = tables.TimeCol()
    value = tables.Float32Col()

class EMA(object):
    def __init__(self, period):
        self.value = None
        self.alpha = 2.0 / (period+1)
        self.tbl = None

    def setupH5(self, h5file, h5where, h5name):
        if h5file != None and h5where != None and h5name != None:
            self.tbl = h5file.createTable(h5where, h5name, EMAData)

    def update(self, value, date=None):
        if self.value == None:
            self.value = value
        else:
            self.value = (value * self.alpha) + (self.value * (1 - self.alpha))
        if self.tbl != None and date:
            self.tbl.row["date"] = date.date().toordinal()
            self.tbl.row["value"] = self.value
            self.tbl.row.append()
            self.tbl.flush()

        return self.value

if __name__ == "__main__":
    import unittest

    class EMATest(unittest.TestCase):

        def test_Alpha(self):
            ema = EMA(9)
            self.assertEqual(ema.alpha, 0.2)

            ema = EMA(19)
            self.assertEqual(ema.alpha, 0.1)

        def test_ConstantValueAlgorithm(self):
            ema = EMA(15)
            self.assertEqual(ema.value, None)
            for i in xrange(50):
                ema.update(5.)
                self.assertEqual(ema.value, 5.)

        def test_ConstantZeroValueAlgorithm(self):
            ema = EMA(10)
            self.assertEqual(ema.value, None)
            for i in xrange(50):
                ema.update(0.)
                self.assertEqual(ema.value, 0.)

        def test_ConstantZeroValueAlgorithm(self):
            ema = EMA(9)
            self.assertEqual(ema.value, None)
            ema.update(1.)
            self.assertEqual(ema.value, 1.)
            ema.update(2.)
            self.assertAlmostEqual(ema.value, 1.2)


    unittest.main()
