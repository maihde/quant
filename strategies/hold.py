#!/usr/bin/env python
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
from strategy import Strategy
from utils.model import Order

class Hold(Strategy):
    """The most basic strategy.  It holds the initial postion and
    makes no trades....ever...for any reason.
    """
    def evaluate(self, date, position, market):
        return () # There are never any orders from this strategy

CLAZZ = Hold
