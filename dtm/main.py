"""
Module with functions for dispatching subprocess and managing multiprocess pools
"""
import multiprocessing as mp
import subprocess
import os
import json
import time
import logging
import argparse


# grab logger from multiprocessing package
logger = mp.get_logger()


# setup logging levels
LOGGING_LEVELS = dict(
    debug=logging.DEBUG,
    info=logging.INFO,
    warning=logging.WARNING,
    error=logging.ERROR,
)


def execute_task(command, path, shell=False, env=None, pipe=False, timeout=None):
    """
    Execute task in subprocess

    Parameters
    ----------
    command: tuple
        Sequence where the program to execute is the first item and the following items are arguments to the program.
    path : str
        Directory in which to execute program
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
    dict
        Process response
            returncode - 0 means success, non-zero code means failure
            ppid - parent process id
            pid - process id
            output - dump from standard out (empty if dumped to file)
            status - 'completed', 'failed' or 'timed out'
            msg - Description

    """
    # concatenate env variables to pass
    if env is not None:
        env = dict(**os.environ, **env)
    else:
        env = os.environ

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
                        returncode=1, status='timeout', output=e.stdout,
                        msg=f'Command "{e.cmd}" timed out after {e.timeout} seconds.')
        logger.debug("\t" + response.get('msg'))

    except subprocess.CalledProcessError as e:
        response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                        returncode=e.returncode, status='error', output=e.stdout,
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
                            returncode=p.returncode, status='completed', output=p.stdout,
                            msg=f'Command "{command}" returned exit status 0. Congratulations!.')
        else:
            # response CompletedProcess with returncode != 0 but no exception raised
            response = dict(pid=os.getpid(), ppid=os.getppid(), path=path,
                            returncode=p.returncode, status='error', output=p.stdout,
                            msg=f'Command "{command}" returned exit status {p.returncode}. See details in task log.')

        logger.debug("\t" + response.get('msg'))

    return response


def execute_tasks(command, paths, processes=None, shell=False, env=None, pipe=False, timeout=None):
    """
    Parallel execution of tasks

    Parameters
    ----------
    command: tuple
        Sequence where the program to execute is the first item and the following items are arguments to the program.
    paths : tuple
        Directories in which to execute program
    processes: int, optional
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
    # initiate worker pool
    pool = mp.Pool(processes=processes)
    logger.debug(f"Initiated pool of {processes} workers.")

    # dispatch processes
    logger.debug(f"Dispatching {len(paths)} tasks to worker pool...")
    processes = [pool.apply_async(execute_task, args=(command, p), kwds=dict(shell=shell, env=env, pipe=pipe, timeout=timeout))
                 for p in paths]

    # report pending tasks
    while pool._cache:
        logger.info(f"Number of tasks pending: {len(pool._cache)}")
        time.sleep(10)

    # prevent any more tasks from being submitted to the pool
    pool.close()
    logger.debug("Closed worker pool to prevent more tasks from being submitted.")

    # provides a synchronization point that can report some exceptions occurring in worker processes
    pool.join()
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
    parser.add_argument("-p", "--processes", type=int, nargs=1,
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
    fh = logging.FileHandler("log.txt", mode="w")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s - %(lineno)s: %(message)s")
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # work directory paths
    paths = parse_path_file(args.path_file)

    # transform command string into a tuple of command arguments
    command = tuple(args.command.split())

    # distribute tasks and collect response
    response = execute_tasks(command, paths, processes=args.processes, shell=args.shell, pipe=args.pipe_stdout)

    # write status listing 'status.txt'(only primary info)
    all_tasks = list()
    failed_tasks = list()
    all_tasks.append(f"{'Path':<70}{'PID':>10}{'PPID':>10}{'Status':>10}" + "\n")
    all_tasks.append(100 * "-" + "\n")
    for r in response:
        # for the overall status
        all_tasks.append(f"{r.get('path'):<70}{r.get('pid'):>10}{r.get('ppid'):>10}{r.get('status'):>10}" + "\n")

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
