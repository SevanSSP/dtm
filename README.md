# DTM
[![Build and test package](https://github.com/SevanSSP/dtm/actions/workflows/build.yml/badge.svg)](https://github.com/SevanSSP/dtm/actions/workflows/build.yml)
[![Publish Python package to Packagr](https://github.com/SevanSSP/dtm/actions/workflows/publish.yml/badge.svg)](https://github.com/SevanSSP/dtm/actions/workflows/publish.yml)
## Description
Python package for managing tasks executed in parallel processes.

A task is defined by a **command** and a **work directory**. The work directory typically contain input files etc.

## Installation
Install the package from Packagr using pip

```bash
 pip install dtm --extra-index-url https://api.packagr.app/EYvhW6SyL/
```

## Usage
### Import package
Import *dtm* and start using the function in there.

```python
import dtm
```  

But the command line interface (CLI) is probably more useful.

### CLI
Run in parallel a predefined script `run.cmd` within a large set of work directories, each 
containing job specific input.

Consider this example: You have setup a large number of SIMO-RIFLEX runs, each run has its own work directory with input
files (`sys-a.dat` and `a_inpmod.inp` etc.)

Maybe your preprocessing/setup created a list of all work directory paths. If not, open the terminal at the root of the 
work directory tree and fetch the path to all the work directories to a file *paths.txt*. Assuming that the lowest level
directory matches the pattern `hs*_tp*`.

```bash
dir /s /b hs*_tp* > paths.txt
```

*paths.txt* would now look something like

```
/home/some_job/ballast/hs1.5_tp5.0_d45/
/home/some_job/ballast/hs2.5_tp6.5_d45/
...
...
/home/some_job/ballast/hs10.5_tp15.5_d125/
/home/some_job/ballast/hs12.5_tp20.0_d125/
```

Then execute `run.cmd` in all work directories utilizing all available CPUs

```bash
dtm run.cmd paths.txt
```

Use only 4 CPUs 

```bash
dtm run.cmd paths.txt --processes 4
```

Stop processes that run more than 60 seconds.

```bash
dtm run.cmd paths.txt --processes 4 --timeout 60
```

The status of all processes is written to *status.txt*. Paths to work directories of failed processes is written to 
*failed_paths.txt* for easy rerun. Detailed log with traceback is written to *log.txt*. Main INFO is piped to stdout.

## Documentation
No documentation yet. Sorry!
