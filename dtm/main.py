"""
Module with functions for dispatching subprocess and managing multiprocess pools
"""
import multiprocessing as mp
import subprocess
import os
import json
import logging
import argparse
import datetime

# grab logger from multiprocessing package
logger = mp.get_logger()


# setup logging levels
LOGGING_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warning=logging.WARNING,
    error=logging.ERROR,
)


def subprocess_command(command, path=None, shell=False, env=None, pipe=False, timeout=None):
    """
    Execute command in subprocess.

    Parameters
    ----------
    command: str
        Command str (the program to execute is the first item and the following items are arguments to the program).
    path : str, optional
        Directory in which to execute program, current work directory by default
    shell : bool, optional
        Spin up a system dependent shell process (commonly \bin\sh on Linux or cmd.exe on Windows) and run the command
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
            status - 'completed', 'failed' or 'timed out'
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
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
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

    except NotADirectoryError as e:
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=1, status='error', output='',
                        msg=f'The path "{path}" is invalid. The directory does not exist.')
        logger.debug("\t" + response.get('msg'))

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


def subprocess_commands(commands, paths, nprocesses=None, shell=False, env=None, pipe=False, timeout=None):
    """
    Execute commands over many work directories in several parallel subprocess.

    Parameters
    ----------
    commands: list or str
        Commands to execute in each of the work directories/paths specified. If `commands` is a single string, that
        command will be executed in each of the work directories.
    paths : tuple
        Directories in which to execute program
    nprocesses: int, optional
        Choose the number of concurrent processes. Default the number of CPUs, see ´os.cpu_count()´
    shell : bool, optional
        Spin up a system dependent shell process (commonly \bin\sh on Linux or cmd.exe on Windows) and run the command
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
        if len(commands) != len(paths):
            logger.error(f"The number of commands must equal the number of work directories. You specified "
                         f"{len(commands)} commands and {len(paths)} work directories.")
    elif isinstance(commands, str):
        commands = [commands for _ in paths]    # duplicate command for all work directories
    else:
        logger.error(f"The `commands` parameter must be a string or a list, not {type(commands)}.")

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
    response = [p.get() for p in subprocesses]
    logger.debug("Retrieved response from the processes:")
    logger.debug(json.dumps(response, indent=2))

    return response


def multiprocess_functions(functions, args=None, kwargs=None, nprocesses=None):
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
    #pool.close()
    logger.debug("Closed worker pool to prevent more tasks from being submitted.")

    # provides a synchronization point that can report some exceptions occurring in worker processes
    #pool.join()
    logger.debug("Join worker processes.")

    # retrieve response from processes
    response = [p.get() for p in processes]
    logger.debug("Retrieved response from the processes:")
    logger.debug(json.dumps(response, indent=2))

    return response


def parse_path_file(filename):
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


def log_response(response):
    """

    Parameters
    ----------
    response : list
        Dictionaries of process response

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
    with open('status.txt', 'w') as f:
        f.writelines(all_tasks)
    logger.info("Task status written to 'status.txt.")

    # list paths to failed runs
    if len(failed_tasks) > 0:
        with open('failed_paths.txt', 'w') as f:
            f.writelines(failed_tasks)
        logger.info("Paths to failed tasks written to 'failed_paths.txt.")


def cli():
    """
    Command line interface for executing tasks
    """
    # create console argument parser
    parser = argparse.ArgumentParser(prog="dtm-run", description="Distributed task manager. Parallel execution of a"
                                                                 " command in many work directories.",)
    parser.add_argument("command", type=str,
                        help="Command to be executed in each work directory. Can be a shell command like 'dir' or path "
                             "to an executable '/home/bin/run_something.cmd'.")
    parser.add_argument("path_file", type=str, help="Textfile with work directory paths, only one per line.")
    parser.add_argument("-p", "--processes", type=int,
                        help="The number of worker processes to use. By default the OS CPU count is used.")
    parser.add_argument("-s", "--shell", action="store_true",
                        help="Spin up a system dependent shell process (commonly bash on Linux or cmd on Windows) and "
                             "run the command within it. Not needed if calling an executable file.")
    parser.add_argument("--pipe-stdout", action="store_true",
                        help="Pipe standard out/err from subprocesses to parent process.")
    parser.add_argument("-t", "--timeout", type=float, help="Number of seconds before terminating a single process.")
    parser.add_argument("-l", "--logging-level", default="info", choices=list(LOGGING_LEVELS.keys()),
                        help="Set logging level.")

    # parse command line arguments
    args = parser.parse_args()

    # configure base logger (initiated on module level)
    logger.setLevel(logging.DEBUG)  # set to lowest level to pipe everything to the handlers

    # configure streamhandler with higher log level (to stdout)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s: %(message)s")
    ch.setFormatter(formatter)
    ch.setLevel(LOGGING_LEVELS.get(args.logging_level))
    logger.addHandler(ch)

    # configure filehandler with lowest log level
    fh = logging.FileHandler("dtm_log.txt", mode="w")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s - %(lineno)s: %(message)s")
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # work directory paths
    paths = parse_path_file(args.path_file)

    # transform command string into a tuple of command arguments
    command = tuple(args.command.split())

    # distribute tasks and collect response
    response = subprocess_commands(command, paths, nprocesses=args.processes, shell=args.shell, pipe=args.pipe_stdout,
                                   timeout=args.timeout)

    # log the process response
    log_response(response)
