import unittest
from dtm.main import subprocess_command
from platform import system

# TODO: Test running a script (does not require shell). Unfortunately we have to create a temp. file on the worker.


class TestCase(unittest.TestCase):
    def test_python(self):
        r = subprocess_command('python --version', pipe=True)
        self.assertEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'completed')

        r = subprocess_command('python --version', pipe=True, shell=True)
        self.assertEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'completed')

    def test_linux(self):
        if not system == 'Linux':
            pass
        else:
            r = subprocess_command('ls -a', pipe=True)
            self.assertNotEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'error')

            r = subprocess_command('ls -a', pipe=True, shell=True)
            self.assertEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'completed')

    def test_win(self):
        if not system == 'Windows':
            pass
        else:
            r = subprocess_command('dir /s /b', pipe=True)
            self.assertNotEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'error')

            r = subprocess_command('dir /s /b', pipe=True, shell=True)
            self.assertEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'completed')


if __name__ == '__main__':
    unittest.main()
