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

WARRANTY="""
BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY FOR THE
PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE
STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND
PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU
ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY
COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE THE
PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR
INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA
BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A
FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER
OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
"""
import time
import sys
import os
import traceback 
from pycommando.commando import command, Commando

##############################################################################
# Some built-in commands
@command("reload")
def reload_():
    """Quit"""
    mydir = os.path.abspath(os.path.dirname(sys.argv[0]))
    for cmd in os.listdir(mydir):
        if not cmd.endswith(".py"):
            continue
        name = cmd[0:-3]
        try:
            if name in sys.modules.keys():
                reload(sys.modules[name])
            else:
                __import__(name)
        except Exception:
            print "Error loading", name
            traceback.print_exc()

@command("quit")
@command("exit")
def exit():
    """Leave Quant"""
    sys.exit(0)

@command("license")
def license():
    """Shows license information"""
    print LICENSE

@command("warranty")
def warranty():
    """Shows warranty information"""
    print WARRANTY

@command("wait")
def wait():
    """Block's until CTRL-C is pressed, only useful at the end of scripts"""
    print "Press CTRL-C to exit"
    while True:
        time.sleep(1)

##############################################################################
# MAIN
##############################################################################
if __name__ == "__main__":
    reload_()

    import readline
    import config
    import logging
    from optparse import OptionParser

    if not os.path.exists(config.QUANT_DIR):
        os.mkdir(config.QUANT_DIR)

    # Setup some basic logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)


    parser = OptionParser()
    parser.add_option("-i", "--iteractive", dest="interactive", default=False, action="store_true")
    (options, args) = parser.parse_args()

    # Right now we have no mode other than iteractive
    commando = Commando()
    if len(args) == 0 or options.interactive:
        if os.isatty(sys.stdin.fileno()):
            print "Welcome to Quant."
            print "  Quant comes with ABSOLUTELY NO WARRANTY; type 'warranty' for details."  
            print "  This is free software, and you are welcome to redistribute it under certian conditions; type 'license' for details."
            print "Type 'help' to see a list of available commands."
        commando.cmdloop()
    else:
        commando.onecmd(" ".join(args))
