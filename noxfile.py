import nox

# override default sessions
nox.options.sessions = ["lint", "tests"]


@nox.session
def lint(session):
    """Highlight syntactical and stylistic problems in the code."""
    session.install("flake8")
    session.run(
        "flake8",
        "dtm/",
        "--count",
        "--select=E9,F63,F7,F82",
        "--show-source",
        "--statistics",
    )
    session.run(
        "flake8",
        "dtm/",
        "--count",
        "--exit-zero",
        "--max-complexity=10",
        "--max-line-length=127",
        "--statistics",
    )


@nox.session
def tests(session):
    """Run test suite."""
    # install dependencies
    session.run("poetry", "install", external=True)
    session.install("pytest")
    session.install("pytest-mock")
    session.install("coverage")
    # session.install("-r", "requirements.txt")

    # unit tests
    testfiles = ["tests/"]
    session.run("coverage", "run", "-m", "pytest", *testfiles)
    session.notify("cover")


@nox.session
def cover(session):
    """Analyse and report test coverage."""
    session.install("coverage")
    session.run("coverage", "report", "--show-missing", "--omit=tests/*",  "--fail-under=88") # TODO: Increase test coverage to 95 %
    session.run("coverage", "erase")


@nox.session
def blacken(session):
    """Run black code formatter."""
    session.install("black", "isort")
    files = ["dtm", "tests", "noxfile.py"]
    session.run("black", *files, "--diff", "--color")
    session.run("isort", *files, "--diff")
