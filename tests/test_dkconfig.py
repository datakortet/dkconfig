import os
import pytest
from mock import MagicMock
import sys
from dkconfig import main, dkconfig


@pytest.fixture
def sysexit(monkeypatch):
    mock_exit = MagicMock()
    monkeypatch.setattr(sys, 'exit', mock_exit)
    return mock_exit


def test_is_functions():
    assert dkconfig._is_items({'a': 1, 'b': 2, 'c': 3}.items())
    assert not dkconfig._is_items(42)

    assert dkconfig._is_iter(['a', 'b', 'c'])
    assert dkconfig._is_iter((1, 2, 3))
    assert not dkconfig._is_iter(42)


def test_format_result(capsys):
    dkconfig.format_result(None)
    out, err = capsys.readouterr()
    assert out.strip() == ""

    dkconfig.format_result(42)
    out, err = capsys.readouterr()
    assert out.strip() == "42"

    dkconfig.format_result({'a': 1, 'b': 2, 'c': 3}.items())
    out, err = capsys.readouterr()
    assert out.strip() == "a => 1\nb => 2\nc => 3"

    dkconfig.format_result(['a', 'b', 'c'])
    out, err = capsys.readouterr()
    assert out.strip() == "a\nb\nc"

    dkconfig.format_result(4+3j)
    out, err = capsys.readouterr()
    assert out.strip() == "(4+3j)"


def test_parse_kwarg():
    assert dkconfig.run('help -42') == 0

    with pytest.raises(AssertionError):
        dkconfig.run('foo -42')

    # assert dkconfig.run('-- foo')
    # with pytest.raises():
    #     dkconfig.run('help -42', debug=True)


def test_debug(tmpdir, sysexit, capsys):
    file = tmpdir.join("foo.ini")
    main(f"{file} get header key -d")
    sysexit.assert_called_with(1)
    out, err = capsys.readouterr()
    err = err.replace('\\', '').strip()
    file = str(file).replace('\\','')
    # compare = """ARGS: Namespace(command='get', debug=True, filename=['%s']) ['header', 'key']""" % file
    # py39 = """ARGS: Namespace(filename=['%s'], command='get', debug=True) ['header', 'key']""" % file
    assert err.endswith(" ['header', 'key']")
    err = err[:-len(" ['header', 'key']")]
    assert err.startswith("ARGS: ")
    err = err[len("ARGS: "):]
    errdict = eval(err, {"Namespace": dict})  # should be valid Python by now, convert Namespace to dict
    assert errdict['command'] == 'get'
    assert errdict['debug'] is True
    assert errdict['filename'] == [file]
    

def test_file_error(tmpdir):
    amadir = tmpdir.join('i-am-a-dir.ini')
    os.makedirs(str(amadir))
    with pytest.raises(IOError):
        main(f"{amadir} set header key value")


def test_create_file(tmpdir, sysexit):
    assert len(tmpdir.listdir()) == 0
    main(f'{tmpdir.join("foo.ini")} set header key value')
    print("DIR:", tmpdir.listdir())
    assert len(tmpdir.listdir()) == 1
    sysexit.assert_called_with(0)


def test_set_get_value(tmpdir, sysexit, capsys):
    main(f'{tmpdir.join("foo.ini")} set header key value')
    main(f'{tmpdir.join("foo.ini")} get header key')
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'value'


def test_set_get_value2(tmpdir, sysexit, capsys):
    main("%s set header --key:=value" % tmpdir.join("foo.ini"))
    # print(tmpdir.join('foo.ini').read())
    main("%s get header key" % tmpdir.join("foo.ini"))
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert out.strip() == 'value'


def test_values(tmpdir, sysexit, capsys):
    main(f'{tmpdir.join("foo.ini")} set header key value')
    main(f'{tmpdir.join("foo.ini")} values')
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


def test_help(tmpdir, sysexit, capsys):
    main("help")
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    assert 'add_section' in out
    assert 'set' in out
    assert 'get' in out
    assert 'items' in out
    assert 'dos' in out
    assert 'bash' in out
    assert 'cat' in out
    assert 'values' in out
    assert 'write' in out


def test_help_command(tmpdir, sysexit, capsys):
    main("help values")
    sysexit.assert_called_with(0)
    out, err = capsys.readouterr()
    print('out:', repr(out))
    print('docstring', repr(dkconfig.Config.values.__doc__))
    assert dkconfig.Config.values.__doc__ in out
