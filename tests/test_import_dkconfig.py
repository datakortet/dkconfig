# -*- coding: utf-8 -*-
import dkconfig
import dkconfig._version
import dkconfig.dkconfig


def test_import_dkconfig():
    assert dkconfig
    assert dkconfig._version
    assert dkconfig.dkconfig
