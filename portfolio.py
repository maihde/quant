#!/usr/bin/env python
#
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
from pycommando.commando import command
from config import CONFIG
from utils.date import ONE_DAY
import yahoo
import datetime
import math
import yaml

@command("portfolio_create")
def create(name, cash_percent=0.0, initial_position="{}"):
    if not CONFIG["portfolios"].has_key(name):
        CONFIG["portfolios"][name] = {}
        CONFIG["portfolios"][name]['$'] = cash_percent
        initial_position = yaml.load(initial_position)
        for sym, amt in initial_position.items():
            CONFIG["portfolios"][name][sym] = amt
        CONFIG.commit()
    else:
        raise StandardError, "Portfolio already exists"

@command("portfolio_delete")
def delete(name):
    if CONFIG["portfolios"].has_key(name):
        del CONFIG['portfolios'][name]
        CONFIG.commit()

@command("portfolio_risk")
def risk(portfolio, start, end, initial_value=10000.0):
    # Emulate risk reports found in beancounter
    # TODO
    raise NotImplementedError 
