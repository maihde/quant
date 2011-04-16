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

class ProgressBar:
    def __init__(self, minValue = 0, maxValue = 10, totalWidth=12):
	self.progBar = "[]"   # This holds the progress bar string
	self.min = minValue
	self.max = maxValue
	self.span = maxValue - minValue
	self.width = totalWidth
	self.amount = 0       # When amount == max, we are 100% done 
	self.updateAmount(0)  # Build progress bar string

    def performWork(self, work):
	self.updateAmount(self.amount + work)

    def updateAmount(self, newAmount = 0):
	if newAmount < self.min: newAmount = self.min
	if newAmount > self.max: newAmount = self.max
	self.amount = newAmount

	# Figure out the new percent done, round to an integer
	diffFromMin = float(self.amount - self.min)
	percentDone = (diffFromMin / float(self.span)) * 100.0
	percentDone = round(percentDone)
	percentDone = int(percentDone)

	# Figure out how many hash bars the percentage should be
	allFull = self.width - 2
	numHashes = (percentDone / 100.0) * allFull
	numHashes = int(round(numHashes))

	# build a progress bar with hashes and spaces
	self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

	# figure out where to put the percentage, roughly centered
	percentPlace = (len(self.progBar) / 2) - len(str(percentDone)) 
	percentString = str(percentDone) + "%"

	# slice the percentage into the bar
	self.progBar = self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

    def __str__(self):
	return str(self.progBar)
