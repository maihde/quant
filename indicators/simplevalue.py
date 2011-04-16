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

class ValueData(tables.IsDescription):
    date = tables.TimeCol()
    value = tables.Float32Col()

class SimpleValue(object):
    def __init__(self):
        self.value = 0.0
        self.tbl = None

    def setupH5(self, h5file, h5where, h5name):
        if h5file != None and h5where != None and h5name != None:
            self.tbl = h5file.createTable(h5where, h5name, ValueData)

    def update(self, value, date=None):
        self.value = value
        if self.tbl != None and date:
            self.tbl.row["date"] = date.date().toordinal()
            self.tbl.row["value"] = self.value
            self.tbl.row.append()
            self.tbl.flush()

        return self.value
