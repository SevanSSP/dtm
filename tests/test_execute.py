import unittest
from dtm.main import execute_task

# TODO: Test running a script (does not require shell). Unfortunately we have to create a temp. file on the worker.


class TestCase(unittest.TestCase):
    def test_commands_requiring_shell(self):
        r = execute_task(('dir', '/s', '/b'), pipe=True)
        self.assertEqual(r.get('returncode'), 1)
        self.assertEqual(r.get('status'), 'error')

        r = execute_task(('dir', '/s', '/b'), pipe=True, shell=True)
        self.assertEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'completed')

        r = execute_task(('python --version', ), pipe=True)
        self.assertEqual(r.get('returncode'), 1)
        self.assertEqual(r.get('status'), 'error')

        r = execute_task(('python --version',), pipe=True, shell=True)
        self.assertEqual(r.get('returncode'), 0)
        self.assertEqual(r.get('status'), 'completed')


if __name__ == '__main__':
    unittest.main()
