# -*- coding: utf-8 -*-
import dkconfig
import dkconfig.version
import dkconfig.dkconfig


def test_import_dkconfig():
    assert dkconfig
    assert dkconfig.version
    assert dkconfig.dkconfig
