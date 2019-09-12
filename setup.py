from setuptools import setup, find_packages
import os


def read(fname):
    """Utility function to read the README file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dtm',
    version='0.2.0',
    packages=find_packages(exclude='tests'),
    url='https://github.com/SevanSSP/dtm',
    license='MIT',
    author='Per Voie',
    author_email='pev@sevanssp.com',
    description='Distributed task manager.',
    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'dtm=dtm.main:cli',
        ],
    }
)
