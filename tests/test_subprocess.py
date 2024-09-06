import logging
import multiprocessing
import os
import subprocess
from platform import system
from subprocess import TimeoutExpired
import re
from tempfile import tempdir

import pytest

from dtm.main import subprocess_commands


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


def test_subprocess_commands(tmpdir):

    if system() == "Windows":
        commands = ["dir"]
    else:
        commands = ["ls"]
    responses = subprocess_commands(commands=commands, paths=[tempdir, tempdir + "\\folder_a"], shell=True, pipe=True)

    assert len(responses) == 2
    response = responses[0]
    assert response.get("returncode") == 0
    assert response.get("status") == "completed"


def test_illegal_command_type(subproc_command):
    with pytest.raises(TypeError) as exc:
        r = subproc_command(command=1, pipe=True)
    assert exc.match("The command must be a string not a <class 'int'>.")


def test_command_timeout(subproc_command, mocker):
    command = "dummy"
    timeout = 1

    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=command, timeout=timeout))

    response = subproc_command(command=command, pipe=True, timeout=timeout)

    assert response.get("status") == "timeout"
    assert response.get("msg") == f'Command "{command}" timed out after {timeout} seconds.'


def test_command_failed(subproc_command, mocker):
    command = "dummy"
    expected_returncode = 1

    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(cmd=command, returncode=expected_returncode))

    response = subproc_command(command=command, pipe=True)

    assert response.get("status") == "error"
    assert response.get("returncode") == expected_returncode
    assert response.get("msg") == f'Command "dummy" returned non-zero exit status 1.'


def test_directory_not_found(subproc_command, mocker):
    command = "dummy"
    expected_returncode = 1

    mocker.patch("subprocess.run", side_effect=NotADirectoryError)

    response = subproc_command(command=command, pipe=True)

    assert response.get("status") == "error"
    assert response.get("returncode") == expected_returncode
    assert re.match(r"The path .* is invalid\. The directory does not exist\.", response.get("msg"))