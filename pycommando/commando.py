#!/usr/bin/env python
# vim: sw=4: et:
#
# Copyright (c) 2010 by Michael Ihde <mike.ihde@randomwalking.com>
#
#                All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software
# and its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Michael Ihde  not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# Michael Ihde DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL Michael Ihde BE LIABLE FOR
# ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#
import inspect
import sys
import string
import cmd
import new
import traceback
import pprint
import os

class Commando(cmd.Cmd):

    ISATTY = True
    def __init__(self, completekey='tab', stdin=sys.stdin, stdout=sys.stdout):
        cmd.Cmd.__init__(self, completekey, stdin, stdout)
        Commando.ISATTY = os.isatty(stdin.fileno()) 
        if not Commando.ISATTY: 
            self.prompt = ""

    def do_shell(self, argstr):
        pass

    def precmd(self, cmd):
        if cmd == "EOF":
            raise SystemExit
        return cmd

    def emptyline(self):
        pass

    def cmdloop(self, intro=None):
        try:
            cmd.Cmd.cmdloop(self, intro)
        except KeyboardInterrupt:
            pass
        except SystemExit:
            pass
        print

def parseargs(argstr):
    """Args are separated by white-space or commas.  Unless a value is
    surrounded by single quotes, white space will be trimmed.

    >>> parseargs('A B C')
    ('A', 'B', 'C')

    >>> parseargs('A    B    C')
    ('A', 'B', 'C')

    >>> parseargs('A, B, C')
    ('A', 'B', 'C')

    >>> parseargs('A B, C')
    ('A', 'B', 'C')
    
    >>> parseargs('A,   B, C')
    ('A', 'B', 'C')

    >>> parseargs('A,   B   C')
    ('A', 'B', 'C')

    >>> parseargs('A ,, C')
    ('A', None, 'C')

    >>> parseargs("'A ' ' B ' C")
    ('A ', ' B ', 'C')

    >>> parseargs("'A, B, C'")
    ('A, B, C',)

    >>> parseargs("'A, B' C")
    ('A, B', 'C')
    """
    args = []
    def parser():
        while True:
            char = (yield)
            if char != ' ': 
                arg_accumulator = []
                if char not in (',', "'", " "):
                    arg_accumulator.append(char)
                if char == "'":
                    while True:
                        char = (yield)
                        if char == "'":
                            break
                        else:
                            arg_accumulator.append(char)
                while True:
                    char = (yield)
                    if char in (',', " ", None):
                        arg = "".join(arg_accumulator)
                        if arg == "":
                            args.append(None)
                        else:
                            args.append(arg)
                        break
                    else:
                        arg_accumulator.append(char)

    p = parser()
    p.send(None) # Start up the coroutine
    for char in argstr:
        p.send(char)
    p.send(None)

    return tuple(args)

# DECORATOR
class command(object):
    def __init__(self, name, prompts=(), category=None):
        self.name = name
	self.prompts = {}
        for argname, prompt, argtype in prompts:
            self.prompts[argname] = (prompt, argtype)

    def promptForYesNo(self, prompt, default):
        val = None
        if not Commando.ISATTY: 
            val = default
        else:
            while val == None:
                if default == None:
                    input = raw_input(prompt + " Y/N: ")
                    if input.upper() in ("Y", "YES"):
                        val = True
                    elif input.upper() in ("N", "NO"):
                        val = False
                else:
                    if default == True:
                        val = raw_input(prompt + " [Y]/N: ")
                    elif default == False:
                        val = raw_input(prompt + " Y/[N]: ")
                    else:
                        raise ValueError

        if val.strip() == "":
            val = default
        elif val.upper() in ("Y", "YES"):
            val = True
        elif val.upper() in ("N", "NO"):
            val = False

        return val

    def promptForValue(self, prompt, default, val_type):
        val = None
        if not Commando.ISATTY: 
            val = default
        else:
            while val == None:
                if default == None:
                    input = raw_input(prompt + ": ")
                    if input.strip() != "":
                        val = input
                else:
                    val = raw_input(prompt + " [%s]: " % (default))
                    if val.strip() == "":
                        val = default
        try:
            val = val_type(val)
        except ValueError:
            val = None

        return val

    def __call__(self, f):
        # Pull out meta data about the function
        f_args, f_varargs, f_varkwargs, f_defaults = inspect.getargspec(f)
        if f_defaults != None:
            f_first_default_index = len(f_args) - len(f_defaults)
        else:
            f_first_default_index = None

        # Define the wrapped function
        def wrapped_f(commando, argstr):
	    args = parseargs(argstr)
            vals = []

            for i in xrange(len(f_args)):
                # See if this argument has a default or not
                default = None
                if f_first_default_index != None and i >= f_first_default_index:
                    default = f_defaults[i - f_first_default_index]

                try:
                    text, val_type = self.prompts[f_args[i]]
                except KeyError:
                    # No prompt was provided, so use a generic one
                    text = "Enter %s" % (f_args[i])
                    # infer the type from the default when possible
                    if default != None:
                        val_type = type(default)
                    else:
                        val_type = str
               
                val = None
                if i < len(args):
                    # The user passed the value so we don't need to prompt
                    # if args[i] is None (not to be confused with "None")
                    # then they explictly wanted the default (without a prompt)
                    # because they entered two commas back to back with an
                    # empty string
                    if (args[i]) != None:
                        if val_type == bool:
                            if args[i].upper() in ("Y", "YES", "TRUE"):
                                val = True
                            elif args[i].upper() in ("N", "NO", "FALSE"):
                                val = False
                            else:
                                raise ValueError
                        else:
                            val = val_type(args[i])
                    elif (args[i]) == None and default != None:
                        val = default
                    else:
                        if val_type == bool:
                            val = self.promptForYesNo(text, default)
                        else:
                            val = self.promptForValue(text, default, val_type)
                else:
                    # Treat bools as yes/no
                    if val_type == bool:
                        val = self.promptForYesNo(text, default)
                    else:
                        val = self.promptForValue(text, default, val_type)
                vals.append(val)

            if f_varargs != None and len(args) > len(f_args):
                vals.extend(args[len(f_args):])
            # Call the function and print the result using pprint
            try:
                result = f(*vals)
                if result != None:
                    if type(result) in (dict, list, tuple):
                        pprint.pprint(result)
                    else:
                        print result
            except Exception, e:
                traceback.print_exc()
                if not Commando.ISATTY: 
                    raise SystemExit

        # Inherit the provided docstring
        # and augment it with information about the arguments
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__doc__ = "\nUsage: %s %s\n\n %s" % (self.name, " ".join(f_args), f.__doc__)

        f_name = "do_" + self.name
        setattr(Commando, f_name, new.instancemethod(wrapped_f, None, Commando))

	# Don't return the wrapped function, because we want
	# to be able to call the functions without the prompt logic
        return f

if __name__ == "__main__":
    import doctest
    doctest.testmod()
