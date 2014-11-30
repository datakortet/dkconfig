#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import inspect
import sys
import glob
import re

__doc__ = """
Basic usage
-----------
Most of the methods of ConfigParser (https://docs.python.org/2/library/configparser.html#ConfigParser.RawConfigParser)
should be usable in a relatively obvious way, however, ``dkconfig`` tries to
give you some sane defaults to make your life easier, e.g. it will create
files/headers/keys that don't exist::

    /tst> ll
    /tst> dkconfig foo.ini set header key value
    /tst> cat foo.ini
    [header]
    key = value

Sections can be added::

    /tst> dkconfig foo.ini add_section header2
    /tst> cat foo.ini
    [header]
    key = value

    [header2]

re-adding them is a no-op (and doesn't throw an exception)::

    /tst> dkconfig foo.ini add_section header2
    /tst> cat foo.ini
    [header]
    key = value

    [header2]

the values command pretty prints the keys and values::

    /tst> dkconfig foo.ini values
    key => value

the ``dos`` command will output the key/values as dos ``set`` commands::

    /tst> dkconfig foo.ini dos
    set "KEY=value"
    /tst> dkconfig foo.ini dos > tmp.bat && tmp.bat
    /tst> echo %KEY%
    value

the ``bash`` command does the same for bash::

    /tst> dkconfig foo.ini bash
    export KEY="value"

You can read values directly into dos variables in the regular convuluted way::

    /tst> for /f "delims=" %a in ('dkconfig foo.ini get header key') do @set KEY=%a
    /tst> echo %KEY%
    value

Bash has a more sane syntax for this::

    bash$ export KEY=$(dkconfig foo.ini get header key)
    bash$ echo $KEY
    value

The appropriate error returns are set if a key is missing::

    /tst> dkconfig foo.ini get header missing
    /tst> echo %ERRORLEVEL%
    1

    /tst> dkconfig foo.ini get header key
    value
    /tst> echo %ERRORLEVEL%
    0
"""
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
from contextlib import contextmanager
from lockfile import LockFile


def _printres(val):
    if val is None:
        print("")
        return
    if isinstance(val, list):
        if not val:
            print("")
            return
        first = val[0]
        if isinstance(first, tuple):
            keylen = max(len(k) for k, v in val)
            for item in val:
                print(item[0].ljust(keylen), '=>', item[1])
        else:
            for item in val:
                print(item)
    else:
        print(val)


class Config(configparser.RawConfigParser):
    exit = 0

    def help(self, cmdname=None):
        """List all commands, or help foo to get help on foo.
        """
        cmds = [name for name in dir(self)
                if not name.startswith('_')
                and inspect.ismethod(getattr(self, name))]
        if cmdname is None or cmdname not in cmds:
            return cmds

        firstline = inspect.getsourcelines(getattr(self, cmdname))[0][0]
        docstring = inspect.getdoc(getattr(self, cmdname))
        return firstline.strip() + '\n\n' + docstring

    def add_section(self, section):
        "Silently accept existing sections."
        try:
            # super(Config, self).add_section(section)
            # ConfigParser is an old style class (can't use super)
            configparser.RawConfigParser.add_section(self, section)
        except configparser.DuplicateSectionError:
            pass

    def get(self, section, option):
        "Get an option from a section (returns None if it can't find it)."
        try:
            return configparser.RawConfigParser.get(self, section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.exit = 1
            return None

    def set(self, section, option, value):
        """Set an option in a section (creates the section if it doesn't exist.
        """
        if not self.has_section(section):
            self.add_section(section)
        return configparser.RawConfigParser.set(self, section, option, value)

    def setlist(self, section, key, *lst):
        if not self.has_section(section):
            self.add_section(section)
        listval = '\n'.join([str(item) for item in lst])
        configparser.RawConfigParser.set(self, section, key, listval)

    def values(self, *sections):
        "Return all values in the config file."
        res = []
        sections = sections or self.sections()
        for sect in sections:
            res += self.items(sect)
        return res

    def dos(self, *sections):
        "Return values as dos set statements."

        def convert_val(v):
            m = re.match(r'\w:(?:/[^/]*)*', v)
            if m:
                # it's a path
                return v.replace('/', '\\')
            return v
            # print("converting:", v, type(v))
            # return re.sub(r'\$(.*)\b', r"%%\1%%", v, re.I)

        return ['set "%s=%s"' % (k.upper(), convert_val(v))
                for k, v in self.values(*sections)]

    def bash(self, *sections):
        "Return values as bash export statements."
        return ['export %s="%s"' % (k.upper(), v) for k, v in self.values(*sections)]


@contextmanager
def parser(fname):
    cp = Config()
    lock = LockFile(fname + '.lock')
    with lock:
        try:
            cp.read(fname)
        except IOError as e:
            # file not found: errno == 2 (it will be created below)
            if e.errno != 2:
                raise
        yield cp
        cp.write(open(fname, 'w'))


def config(filename, command='cat', flags=(), *args):
    "Main entry point for this module."
    if '--debug' in flags:
        print("\n==> CONFIG:", filename, command, args, '\n')
    args = [arg for arg in args if not arg.startswith('-')]
    if command == 'cat':
        # a+ -> read + create if not exist
        print(open(filename, 'a+').read())
        return 0

    with parser(filename) as p:
        cmd = getattr(p, command)
        res = cmd(*args)
        _printres(res)
        return p.exit


def piped_input():
    "Do we have piped input?"
    if sys.platform == 'win32':
        return []
    return []       # TODO: find a way to use both py.test capsys and select on sys.stdin..
    import select

    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if ready:
        return [line.strip() for line in sys.stdin.readlines()]
    return []


def parse_commandline(arguments=None):
    """[prog] [glob/filename] cmd args* [--flags]
       ... | [prog] cmd args* [--flags]
    """
    if arguments is None:
        arguments = sys.argv[1:]
    progargs = [a for a in arguments if not a.startswith('-')]
    progflags = [f for f in arguments if f.startswith('-')]
    argcount = len(progargs)

    def getarg(n, default=None):
        if n < argcount:
            return progargs[n]
        return default

    # find . -name "*.ini" -print | config - values
    fnames = piped_input()
    if not (progargs or fnames):
        # nothing to do
        print(__doc__)
        sys.exit(0)

    if fnames:
        command = getarg(0, 'cat')
        args = progargs[1:]
    else:
        fnames = glob.glob(progargs[0])
        if not fnames:
            with open(progargs[0], 'a+'): pass
            fnames = [progargs[0]]
        command = getarg(1, 'cat')
        args = progargs[2:]

    return fnames, command, args, progflags


def main(cmdline=""):
    params = cmdline.split() if isinstance(cmdline, basestring) else sys.argv[1:]
    fnames, command, args, flags = parse_commandline(params)
    #print(locals())
    retcode = 0

    for fname in fnames:
        retcode += config(fname, command, flags, *args)

    sys.exit(retcode)


if __name__ == "__main__":
    main(sys.argv[1:])
