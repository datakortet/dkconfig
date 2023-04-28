
.. image:: https://github.com/datakortet/dkconfig/actions/workflows/ci-cd.yml/badge.svg
    :target: https://github.com/datakortet/dkconfig/actions/workflows/ci-cd.yml
    :alt: CI/CD Pipeline

.. image:: https://readthedocs.org/projects/dkconfig/badge/?version=latest
   :target: https://readthedocs.org/projects/dkconfig/?badge=latest
   :alt: Documentation Status

.. image:: https://codecov.io/gh/datakortet/dkconfig/branch/master/graph/badge.svg?token=EEyMx6KE7e
    :target: https://codecov.io/gh/datakortet/dkconfig
    :alt: Code Coverage

dkconfig -- command line access to ConfigParser
==================================================


Installing from PyPI
--------------------


   pip install dkconfig


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

