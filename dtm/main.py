"""
Module with functions for dispatching subprocess and managing multiprocess pools
"""
import multiprocessing as mp
import subprocess
import os
import json
import logging
import datetime
from typing import TypedDict, Literal, Optional

# grab logger from multiprocessing package
logger = mp.get_logger()


# setup logging levels
LOGGING_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warning=logging.WARNING,
    error=logging.ERROR,
)


class ResponseDict(TypedDict):
    returncode: int
    ppid: int
    pid: int
    path: str
    output: Optional[str]
    status: Literal["completed", "error", "timeout"]
    msg: str


def subprocess_command(command: str, path=None, shell=False, env=None, pipe=False, timeout=None) -> ResponseDict:
    """
    Execute command in subprocess.

    Parameters
    ----------
    command: str
        Command str (the program to execute is the first item and the following items are arguments to the program).
    path : str, optional
        Directory in which to execute program, current work directory by default
    shell : bool, optional
        Spin up a system dependent shell process (commonly /bin/sh on Linux or cmd.exe on Windows) and run the command
        within it. Not needed if calling an executable file.
    env : dict, optional
        Environmental variables passed to program
    pipe : bool, optional
        Pipe standard out/err from subprocesses to parent process. Default is to dump standard out/err to a log file in
        the specified work directory.
    timeout : int, optional
        Number of seconds before terminating the process

    Notes
    -----
    The command parameters are split as list if `shell` is False.

    Returns
    -------
    dict
        Process response
            returncode - 0 means success, non-zero code means failure
            ppid - parent process id
            pid - process id
            path - work directory
            output - dump from standard out (empty if dumped to file)
            status - 'completed', 'error' or 'timeout'
            msg - Description

    """
    # ensure correct type
    if not isinstance(command, str):
        logger.error(f"The command must be a string not a {type(command)}.")
        raise TypeError(f"The command must be a string not a {type(command)}.")

    # use current work directory if none is specified
    if path is None:
        path = os.getcwd()

    # concatenate env variables to pass
    if env is not None:
        env = dict(**os.environ, **env)
    else:
        env = os.environ

    # concatenate command parameters to string if shell
    if not shell:
        command = command.split()

    # choose handling of standard out/err
    if pipe:
        # pipe to parent process
        out = subprocess.PIPE
    else:
        # log stdout/stderr to file in path
        out = open(os.path.join(path, 'log.txt'), 'w')

    logger.debug("\t" + f"Executing command '{command}' in working directory '{path}.'")

    # execute subprocess and catch errors
    try:
        p = subprocess.run(command, stdout=out, shell=shell, stderr=subprocess.STDOUT, cwd=path, env=env,
                           timeout=timeout)

    except subprocess.TimeoutExpired as e:
        response: ResponseDict = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=1, status='timeout', output=e.stdout.decode() if e.stdout is not None else None,
                        msg=f'Command "{e.cmd}" timed out after {e.timeout} seconds.')
        logger.debug("\t" + response.get('msg'))

    except subprocess.CalledProcessError as e:
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=e.returncode, status='error',
                        output=e.stdout.decode() if e.stdout is not None else None,
                        msg=f'Command "{e.cmd}" returned non-zero exit status {e.returncode}.')
        logger.debug("\t" + response.get('msg'))

    except FileNotFoundError as e:
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=1, status='error', output='',
                        msg=f'Command "{command[0]}" could not be found.')
        logger.debug("\t" + response.get('msg'))
        logger.debug("\t" + str(e))

    except NotADirectoryError as e:
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=1, status='error', output='',
                        msg=f'The path "{path}" is invalid. The directory does not exist.')
        logger.debug("\t" + response.get('msg'))
        logger.debug("\t" + str(e))

    else:
        if p.returncode == 0:
            # response CompletedProcess with returncode 0
            response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                            returncode=p.returncode, status='completed',
                            output=p.stdout.decode() if p.stdout is not None else None,
                            msg=f'Command "{command}" returned exit status 0. Congratulations!.')
        else:
            # response CompletedProcess with returncode != 0 but no exception raised
            response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                            returncode=p.returncode, status='error',
                            output=p.stdout.decode() if p.stdout is not None else None,
                            msg=f'Command "{command}" returned exit status {p.returncode}. See details in task log.')

        logger.debug("\t" + response.get('msg'))

    return response


def subprocess_commands(commands: list[str], paths: list[str], nprocesses=None, shell=False, env=None, pipe=False, timeout=None) -> list[ResponseDict]:
    r"""
    Execute commands over many work directories in several parallel subprocess.

    Parameters
    ----------
    commands: list
        Commands to execute in each of the work directories/paths specified. If `commands` is of length 1, that
        command will be executed in each of the work directories.
    paths : list
        Directories in which to execute program
    nprocesses: int, optional
        Choose the number of concurrent processes. Default the number of CPUs, see ´os.cpu_count()´
    shell : bool, optional
        Spin up a system dependent shell process (commonly /bin/sh on Linux or cmd.exe on Windows) and run the command
        within it. Not needed if calling an executable file.
    env : dict, optional
        Environmental variables passed to program
    pipe : bool, optional
        Pipe standard out/err from subprocesses to parent process. Default is to dump standard out/err to a log file in
        the specified work directory.
    timeout : int, optional
        Number of seconds before terminating the process

    Returns
    -------
    list
        Collection of subprocess response

    """
    if isinstance(commands, (list, tuple)):
        if len(commands) == 1:
            commands *= len(paths)      # duplicate command for all work directories

        elif len(commands) != len(paths):
            logger.error(f"The number of commands must 1 or equal the number of paths. You specified "
                         f"{len(commands)} commands and {len(paths)} paths.")
    else:
        logger.error(f"The `commands` parameter must be a tuple or a list, not {type(commands)}.")

    # initiate worker pool
    pool = mp.Pool(processes=nprocesses)
    logger.debug(f"Initiated pool of {nprocesses} workers.")

    # dispatch processes
    logger.debug(f"Dispatching {len(paths)} tasks to worker pool...")
    subprocesses = [pool.apply_async(subprocess_command, args=(c,), kwds=dict(path=p, shell=shell, env=env, pipe=pipe,
                                                                              timeout=timeout))
                    for c, p in zip(commands, paths)]

    # report pending tasks
    t0 = datetime.datetime.now()
    while pool._cache:
        t1 = datetime.datetime.now()
        if (t1 - t0).total_seconds() >= 15:
            logger.debug(f"Number of tasks pending: {len(pool._cache)}")
            t0 = datetime.datetime.now()

    # prevent any more tasks from being submitted to the pool
    pool.close()
    logger.debug("Closed worker pool to prevent more tasks from being submitted.")

    # provides a synchronization point that can report some exceptions occurring in worker processes
    pool.join()
    logger.debug("Join worker processes.")

    # retrieve response from processes
    response: list[ResponseDict] = [p.get() for p in subprocesses]
    logger.debug("Retrieved response from the processes:")
    logger.debug(json.dumps(response, indent=2))

    return response


def multiprocess_functions(functions, args=None, kwargs=None, nprocesses=None) -> list[ResponseDict]:
    """
    Multiprocess functions.

    Parameters
    ----------
    functions: list
        Functions to execute.
    args : list[list], optional
        Function positional arguments.
    kwargs : list[dict], optional
        Function keyword arguments.
    nprocesses: int, optional
        Choose the number of concurrent processes. Default the number of CPUs, see ´os.cpu_count()´

    Returns
    -------
    list
        Collection of function responses.

    Notes
    -----
    The order of the returned response equals the order of the input functions and its arguments.

    """
    if args is not None and len(functions) != len(args):
        logger.error(f"The number of functions must equal the number of argument sets. You specified {len(functions)} "
                     f"functions and {len(args)} argument sets.")
    elif args is None:
        args = [list() for _ in functions]

    if kwargs is not None and len(functions) != len(kwargs):
        logger.error(f"The number of functions must equal the number of keyword argument sets. You specified "
                     f"{len(functions)} functions and {len(kwargs)} argument sets.")
    elif kwargs is None:
        kwargs = [dict() for _ in functions]

    # initiate worker pool
    pool = mp.Pool(processes=nprocesses)
    logger.debug(f"Initiated pool of {nprocesses} workers.")

    # dispatch processes
    logger.debug(f"Dispatching {len(functions)} tasks to worker pool...")
    processes = [pool.apply_async(f, args=a, kwds=k) for f, a, k in zip(functions, args, kwargs)]

    # report pending tasks
    t0 = datetime.datetime.now()
    while pool._cache:
        t1 = datetime.datetime.now()
        if (t1 - t0).total_seconds() >= 15:
            logger.debug(f"Number of tasks pending: {len(pool._cache)}")
            t0 = datetime.datetime.now()

    # prevent any more tasks from being submitted to the pool
    # pool.close()
    logger.debug("Closed worker pool to prevent more tasks from being submitted.")

    # provides a synchronization point that can report some exceptions occurring in worker processes
    # pool.join()
    logger.debug("Join worker processes.")

    # retrieve response from processes
    response = [p.get() for p in processes]
    logger.debug("Retrieved response from the processes:")
    logger.debug(json.dumps(response, indent=2))

    return response


def parse_path_file(filename: str) -> list[str]:
    """
    Read list of work directory paths from file

    Parameters
    ----------
    filename: str
        Path to text file with work directory paths, only one per line.

    Returns
    -------
    list
        Work directory paths

    """
    try:
        paths = open(filename).read().splitlines()
    except IOError as e:
        logger.exception(f"Could not open file '{filename}'.'")
        raise e
    else:
        logger.debug(f"Parsed work directory paths from '{filename}'.")
        return paths


def log_response(response: list[ResponseDict], status_summary_path: str = "status.txt", failed_tasks_path: str = "failed_paths.txt") -> None:
    """

    Parameters
    ----------
    response : list
        Dictionaries of process response
    status_summary_path: str
        Path to write status summary to
    failed_tasks_path: str
        Path to write list of failed tasks to

    Notes
    -----
    Writes
    """
    # write status listing 'status.txt'(only primary info)
    all_tasks = list()
    failed_tasks = list()
    path_length = 5 + max(len(_.get('path')) for _ in response)  # longest path (for output formatting)
    all_tasks.append(f"{'Path':<{path_length}}{'PID':>10}{'PPID':>10}{'Status':>10}" + "\n")
    all_tasks.append((path_length + 30) * "-" + "\n")
    for r in response:
        # for the overall status
        all_tasks.append(f"{r.get('path'):<{path_length}}{r.get('pid'):>10}{r.get('ppid'):>10}{r.get('status'):>10}" +
                         "\n")

        if r.get('returncode') != 0:
            # only the failed cases
            failed_tasks.append(r.get('path') + "\n")

    # write status summary
    with open(status_summary_path, 'w') as f:
        f.writelines(all_tasks)
    logger.info("Task status written to 'status.txt.")

    # list paths to failed runs
    if len(failed_tasks) > 0:
        with open(failed_tasks_path, 'w') as f:
            f.writelines(failed_tasks)
        logger.info("Paths to failed tasks written to 'failed_paths.txt.")
