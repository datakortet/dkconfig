import pytest
from mock import MagicMock, Mock
import sys
from dkconfig import main, dkconfig


@pytest.fixture
def sysexit(monkeypatch):
    mock_exit = MagicMock()
    monkeypatch.setattr(sys, 'exit', mock_exit)
    return mock_exit


def test_create_file(tmpdir, sysexit):
    assert len(tmpdir.listdir()) == 0
    main("%s set header key value" % tmpdir.join("foo.ini"))
    print("DIR:", tmpdir.listdir())
    assert len(tmpdir.listdir()) == 1
    sysexit.assert_called_with(0)


def test_set_get_value(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s get header key" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'value'


def test_values(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s values" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'key => value'


def test_dos_path(tmpdir, sysexit, capsys):
    main("%s set header key c:/path/value" % tmpdir.join("foo.ini"))
    main("%s dos" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'set "KEY=c:\\path\\value"'


def test_dos(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s dos" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'set "KEY=value"'

def test_bash(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s bash" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'export KEY="value"'


def test_default_cmd_cat(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == '[header]\nkey = value'


def test_noargs(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == '[header]\nkey = value'


def test_setlist(tmpdir, sysexit, capsys):
    main("%s setlist header key a b c" % tmpdir.join("foo.ini"))
    main("%s get header key" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.split() == 'a b c'.split()


def test_get_missing(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s get header missing" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(1)
    out, err = capsys.readouterr()
    assert out.strip() == ""


def test_add_duplicate_section(tmpdir, sysexit, capsys):
    main("%s set header key value" % tmpdir.join("foo.ini"))
    main("%s add_section header" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == ""


# def test_help(tmpdir, sysexit, capsys):
#     main("help")
#     sysexit.assert_called_with(0)
#     out, err = capsys.readouterr()
#     assert out == dkconfig.__doc__