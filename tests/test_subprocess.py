from platform import system

# TODO: Test running a script (does not require shell). Unfortunately we have to create a temp. file on the worker.


def test_python(subproc_command):
    r = subproc_command('python --version', pipe=True)
    assert r.get('returncode') == 0
    assert r.get('status') == 'completed'

    r = subproc_command('python --version', pipe=True, shell=True)
    assert r.get('returncode') == 0
    assert r.get('status') == 'completed'


def test_linux(subproc_command):
    if not system() == 'Linux':
        pass
    else:
        r = subproc_command('ls -a', pipe=True)
        assert r.get('returncode') != 0
        assert r.get('status') == 'error'

        r = subproc_command('ls -a', pipe=True, shell=True)
        assert r.get('returncode') == 0
        assert r.get('status') == 'completed'


def test_win(subproc_command):
    if not system() == 'Windows':
        pass
    else:
        r = subproc_command('dir /s /b', pipe=True)
        assert r.get('returncode') != 0
        assert r.get('status') == 'error'

        r = subproc_command('dir /s /b', pipe=True, shell=True)
        assert r.get('returncode') == 0
        assert r.get('status') == 'completed'
