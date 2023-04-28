#!/usr/local/bin/python
"""
Basic usage
-----------
Most of the methods of ConfigParser
(https://docs.python.org/2/library/configparser.html#ConfigParser.RawConfigParser)
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

from a batch file you would use it like this::

    dkconfig foo.ini dos > tmp.bat && call tmp.bat && del tmp.bat

the ``bash`` command does the same for bash, and you'll use it together with
eval::

    eval $(dkconfig foo.ini bash)

You can read values directly into dos variables in the regular way::

    > for /f "delims=" %a in ('dkconfig foo.ini get header key') do @set KEY=%a
    > echo %KEY%
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
import argparse
import configparser
import glob
import inspect
import os
import re
import sys
import tempfile
from contextlib import contextmanager

from lockfile import LockFile

from ._version import __version__


def _is_items(lst):
    """Is ``lst`` an items list?
    """
    try:
        res = list(lst)
        return False if any(len(item) != 2 for item in res) else res
    except (ValueError, TypeError):
        return False


def _is_iter(lst):
    """Is ``lst`` an iterator?
    """
    try:
        return list(lst)
    except Exception:
        return False


def format_items(items):
    """Print items formatted in two columns.
    """
    keylen = max(len(k) for k, v in items)
    for k, v in items:
        print(k.ljust(keylen), '=>', v)


def format_list(lst):
    """Print one item per line.
    """
    for item in lst:
        print(item)


def format_result(val):
    """Pretty print val.
    """
    if not val:
        return print("")

    if isinstance(val, (int, float, str)):
        return print(val)

    items = _is_items(val)
    if items:
        return format_items(items)

    lst = _is_iter(val)
    if lst:
        return format_list(lst)

    # mystery item
    print(val)  # pragma: nocover
    return None


class Config(configparser.RawConfigParser):
    """CLI Interface to configparser.
    """
    exit = 0
    _meta_commands = ['help']

    @property
    def commands(self):
        """Return all methods defined as self as a list.
        """
        def _ismethod(m):
            return inspect.ismethod(getattr(self, m))

        res = []
        for n in dir(self):
            if n != 'commands' and not n.startswith('_') and _ismethod(n):
                res.append(n)
        return res

    def help(self, cmdname=None):
        """List all commands, or help foo to get help on foo.
        """
        cmds = self.commands

        if cmdname is None or cmdname not in cmds:
            return [' ' * 4 + cmd for cmd in cmds]

        firstline = inspect.getsourcelines(getattr(self, cmdname))[0][0]
        docstring = inspect.getdoc(getattr(self, cmdname))
        return f'''
        {firstline.strip()}
            """
            {docstring}
            """'''

    def cat(self):
        """Output the contents to stdout.
        """
        self.write(sys.stdout)

    def read(self, fname, *args, **kw):  # pylint:disable=arguments-differ
        open(fname, 'a+').close()  # create file if it doesn't exist.
        return configparser.RawConfigParser.read(self, fname, *args, **kw)

    def add_section(self, section):
        """Silently accept existing sections.
        """
        try:
            # super(Config, self).add_section(section)
            # ConfigParser is an old style class (can't use super)
            configparser.RawConfigParser.add_section(self, section)
        except configparser.DuplicateSectionError:
            pass

    def get(self, section, option):  # pylint:disable=arguments-differ
        """Get an option from a section (returns None if it can't find it).
        """
        try:
            return configparser.RawConfigParser.get(self, section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.exit = 1
            return None

    def set(self, section, option, value=None):
        """Set an option in a section (creates the section if it doesn't exist.
        """
        if not self.has_section(section):
            self.add_section(section)
        return configparser.RawConfigParser.set(self, section, option, value)

    def setlist(self, section, key, *lst):
        """Set a list value.
        """
        if not self.has_section(section):
            self.add_section(section)
        listval = '\n'.join([str(item) for item in lst])
        configparser.RawConfigParser.set(self, section, key, listval)

    def values(self, *sections):  # pylint:disable=arguments-differ
        """Return all values in the config file.
        """
        res = []
        sections = sections or self.sections()
        for sect in sections:
            res += self.items(sect)
        return res

    def dos(self, *sections):
        """Return values as dos set statements.
        """

        def convert_val(v):
            """Converts from ini-style paths to .bat-style paths.
            """
            m = re.match(r'\w:(?:/[^/]*)*', v)
            if m:
                # it's a path
                return v.replace('/', '\\')
            return v

        return [f'set "{k.upper()}={convert_val(v)}"'
                for k, v in self.values(*sections)]

    def bash(self, *sections):
        """Return values as bash export statements.
        """
        return [f'export {k.upper()}="{v}"'
                for k, v in self.values(*sections)]


VAR_LOCK = '/var/lock'


def make_lock(fname, timeout=0):
    """Return a LockFile for `fname`, in an appropriate location.
    """
    # Don't put the lock file next to the file to be locked, since that
    # filesystem might not be as functional as we need it to be
    lockbase = VAR_LOCK if os.path.exists(VAR_LOCK) else tempfile.gettempdir()
    lockdir = os.path.join(lockbase, 'dkconfig')
    try:
        os.makedirs(lockdir)
    except os.error:
        if not os.path.exists(lockdir):
            lockdir = lockbase  # pragma: nocover

    lock_fname = os.path.join(lockdir, os.path.basename(fname))
    return LockFile(lock_fname, timeout=timeout)


@contextmanager
def parser(fname):
    """Context manager that provides locking semantics.
    """
    cp = Config()
    with make_lock(fname, timeout=7):
        try:
            cp.read(fname)
        except OSError as e:
            # file not found: errno == 2 (it will be created below)
            if e.errno != 2:
                raise
        yield cp
        cp.write(open(fname, 'w'))


def run(cmdline=None):
    """`run()` is the most convenient entry point for usage as a Python
       library::

           import dkconfig
           txt = dkconfig.run('foo.ini values')
           val = dkconfig.run('foo.ini get key')

       `run` does not call `sys.exit`.

       The commands can be meta-commands (commands about dkconfig, not
       an ini file).::

          dkconfig meta-command [args*] --flags

       e.g.::

          dkconfig help
          dkconfig help cmd

          dkconfig [glob/filename] cmd args* [--flags]

       i.e. dkconfig followed by a glob matchine one or more ini files,
       followed by a command and arguments to the command as specified in the
       docs (and any flags).

       .. TODO:: dkconfig should also be able to take file names from stdin

       ::
          <other-prog> | dkconfig cmd args* [--flags]

       this would let you quickly access common properties, e.g.::

          $ find . -maxdepth 2 -name "*.ini" -print | dkconfig - get site dns
          www.example.com
          www.example2.com
          ...

    """
    string_cmdline = isinstance(cmdline, str)
    params = cmdline.split() if string_cmdline else sys.argv[1:]
    p = argparse.ArgumentParser(
        description="Command line interface to ConfigParser"
    )
    p.add_argument('filename', nargs='?')
    p.add_argument('command')
    p.add_argument('--version', action='version',
                   version='%(prog)s ' + __version__)
    p.add_argument('-d', '--debug', action='store_true')

    args, unparsed = p.parse_known_args(params)

    if args.filename:
        # expand globs, but be careful so we can still create new files.
        #  Namespace(filename='*.ini', ...)
        #  Namespace(filename='foo.ini', ...)
        #  Namespace(filename='does-not-exist.ini', ...)
        args.filename = glob.glob(args.filename) or [args.filename]

    available_commands = Config().commands

    if not args.filename and args.command not in available_commands:
        # Namespace(filename=None, command='foo.ini')
        args.filename = [args.command]
        args.command = 'cat'

    if args.filename == ['help']:
        # Namespace(filename=['help'], command='values')
        args.filename = []
        unparsed.insert(0, args.command)
        args.command = 'help'

    assert args.command in available_commands

    if args.debug:
        print("ARGS:", args, unparsed, file=sys.stderr)
        sys.exit(0)

    def parse_kwarg(txt):
        """Parse command line flags.
        """
        m = re.match(r'--?(?P<key>\w+)(:=(?P<val>.*))', txt)
        if m:
            g = m.groupdict()
            return g['key'], g['val']
        return None

    def call_config(cp):
        """Call config command specified in args.command.
        """
        try:
            cmd = getattr(cp, args.command)
        except Exception:  # pragma: nocover
            print('error:', cp, args)
            raise
        remaining_opts = [param for param in unparsed if param.startswith('-')]
        pos_opts = [param for param in unparsed if not param.startswith('-')]
        for item in [parse_kwarg(opt) for opt in remaining_opts]:
            if item:
                pos_opts += item
        res = cmd(*pos_opts)
        format_result(res)
        return cp.exit

    if not args.filename:
        return call_config(Config())

    retcode = 0
    for fname in args.filename:
        with parser(fname) as p:
            retcode += call_config(p)
    return retcode > 0


def main(cmdline=None):
    """`main()` is the entry point for the dkconfig command line tool.
    """
    retcode = run(cmdline)
    sys.exit(retcode)


if __name__ == "__main__":  # pragma: nocover
    main(sys.argv[1:])
