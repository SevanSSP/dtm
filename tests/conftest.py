import pytest
from dtm.main import multiprocess_functions, subprocess_command, ResponseDict


@pytest.fixture(scope='function')
def test_func_without_arguments():
    def _method(n):
        return multiprocess_functions(3 * [func], nprocesses=n)

    return _method


def func():
    return 'Some response.'


@pytest.fixture(scope='function')
def test_func_with_arguments():
    def _method(n):
        args = [['Joe', 16], ['Susie', 18], ['Aron', 8]]
        kwargs = [dict(sports=True), dict(sports=True), dict(sports=False)]
        return multiprocess_functions(3 * [func2], args, kwargs, nprocesses=n)

    return _method


def func2(name, age, sports=False):
    return f"{name} is {age} years old and {'is not' if not sports else 'is'} doing sports."


@pytest.fixture(scope='module')
def subproc_command():
    def _method(*args, **kwargs):
        return subprocess_command(*args, **kwargs)
    return _method

@pytest.fixture(scope='function')
def ok_response() -> ResponseDict:
    return ResponseDict(returncode=0, ppid=123, pid=1, path="dummy/ok_path", output=None, status="completed", msg="example response")

@pytest.fixture(scope='function')
def bad_response() -> ResponseDict:
    return ResponseDict(returncode=1, ppid=321, pid=1, path="dummy/bad_path", output=None, status="error", msg="example error response")
