import logging

import pytest

from dtm.main import log_response, parse_path_file


def test_parse_path_file(tmpdir):
    path_a = "path_a.txt"
    path_b = "path_b.txt"
    path_file_path = tmpdir.join("some_paths.txt")
    path_file_path.write(f"{path_a}\n{path_b}")

    paths = parse_path_file(path_file_path)
    assert path_a in paths
    assert path_b in paths

def test_missing_parse_path_file():
    """ Kind of pointless test as is, #TODO: Check logging if entry is added"""
    with pytest.raises(IOError):
        parse_path_file("non_exisiting_file")


def test_log_response(ok_response, bad_response, tmpdir):
    output_status = tmpdir.join("status.txt")
    output_failed = tmpdir.join("failed.txt")
    log_response(response=[ok_response, bad_response],failed_tasks_path=output_failed, status_summary_path=output_status)

    assert str(ok_response["ppid"]) in output_status.read()
    assert str(bad_response["ppid"]) in output_status.read()

    assert ok_response["path"] not in output_failed.read()
    assert bad_response["path"] in output_failed.read()