import unittest
from dtm.main import execute_task
from platform import system

# TODO: Test running a script (does not require shell). Unfortunately we have to create a temp. file on the worker.


class TestCase(unittest.TestCase):
    def test_python(self):
        r = execute_task(('python --version', ), pipe=True)
        self.assertNotEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'error')

        r = execute_task(('python --version',), pipe=True, shell=True)
        self.assertEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'completed')

    def test_linux(self):
        if not system == 'Linux':
            pass
        else:
            r = execute_task(('ls', '-a'), pipe=True)
            self.assertNotEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'error')

            r = execute_task(('ls', '-a'), pipe=True, shell=True)
            self.assertEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'completed')

    def test_win(self):
        if not system == 'Windows':
            pass
        else:
            r = execute_task(('dir', '/s', '/b'), pipe=True)
            self.assertNotEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'error')

            r = execute_task(('dir', '/s', '/b'), pipe=True, shell=True)
            self.assertEqual(r.get('returncode'), 0)
            self.assertEqual(r.get('status'), 'completed')


if __name__ == '__main__':
    unittest.main()
