=======================
Quant
=======================

-------
License
-------
Copyright (C) 2011 Michael Ihde

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA 02111-1307 USA.

-----
Intro
-----

Quant is a python-based, technical analysis tool for trading strategies.  It takes
a particularily simplistic view of the market and only allows trading decisions to
be made after the market has closed.

The goal of Quant is to provide a useful experimentation framework to explore
trading strategies that are applicable to the casual investor who is managing a
401k, IRA, or other long-term investment.

Quant can be used without any programming knowledge, but a decent grasp of Python
will be required to create customized strategies.

-------
Install
-------

Quant runs directly from it's own directory, as such Quant is not 'installed'
in the usual sense.  Quant does require a few libraries to be available

On Ubuntu Linux::
    sudo apt-get install python-tables python-sqlite python-matplotlib python-yaml

---------------
Getting Started
---------------

Quant stores it's configuration and all data in ~/.quant.

All Quant portfolios are stored in ~/.quant/quant.cfg as a YAML entry.  Entires
in a portfolio can either be listed as absolute quantities or as cash values.
The former is useful is you are using Quant to analyze a real portfolio that
you currently own.  The latter is useful for backtesting strategies as it
ensures that your portfolio assets have proper ratios regardless of the
assets price at the start of the simulation.

Here is an example quant.cfg, the first portfolio uses cash values
while the second portfolio uses absolute quantities::
    portfolios:
        example_one: {$: 0, IWM: $30000, SPY: $45000, VWO: $25000}
        example_two: {$: 0, IWM: 30, SPY: 100, VWO: 50}

Quant can be run in three modes:

#. Interactive
#. One-shot
#. Scripted

To run in interactive mode, simply execute quant::
    $ ./quant

To run in one-shot mode::
    $ ./quant <command> <argments>

Finally, to run a script of commands::
    $ ./quant < commands.txt

An example script is provided in scripts/example.txt.  It is suggested that you
read it and then execute it::
    $ ./quant < scripts/example.txt

----
Misc
----

If you are developing new strategies, you may want to install HDFView, as it will
give you an easy way to explore the raw data in the output h5 files.  HDFView can
be downloaded from http://www.hdfgroup.org/hdf-java-html/hdfview/

You may also like to read these resources to learn more about Quantitive trading:

- http://www.smartquant.com/introduction/openquant_strategy.pdf
- Quantitative Trading: How to Build Your Own Algorithmic Trading Business by Ernest P. Chan
