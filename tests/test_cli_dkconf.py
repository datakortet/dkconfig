# -*- coding: utf-8 -*-

import pytest

@pytest.fixture
def cli():
    def _cli(txt):
        """
        """
        pass
    return _cli


################################################################################

def test_debug(cli):
    cli("""
    > dkconfig foo.ini get header key -d
    = ...(command='get', ... filename=['foo.ini'], ...) ['header', 'key']

    """)


def test_create_file(cli):
    cli("""
    > dkconfig {FNAME:foo.ini} set header key value
    """)
