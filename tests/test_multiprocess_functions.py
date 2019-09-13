import unittest
from dtm.main import multiprocess_functions


def func():
    return "Some response."


def func2(name, age, sports=False):
    return f"{name} is {age} years old and {'is not' if not sports else 'is'} doing sports."


class TestCase(unittest.TestCase):
    def test_func_without_arguments(self, n=None):
        r = multiprocess_functions(3 * [func], nprocesses=n)

        self.assertEqual(3, len(r))
        self.assertEqual(r[0], "Some response.")

        # sets does not have duplicates so if all items in r are equal the set will have only 1 value
        self.assertEqual(1, len(set(r)))

    def test_func_without_arguments_1(self):
        self.test_func_without_arguments(n=1)

    def test_func_without_arguments_3(self):
        self.test_func_without_arguments(n=3)

    def test_func_with_arguments(self, n=None):
        args = [['Joe', 16], ['Susie', 18], ['Aron', 8]]
        kwargs = [dict(sports=True), dict(sports=True), dict(sports=False)]
        r = multiprocess_functions(3 * [func2], args, kwargs, nprocesses=n)

        self.assertEqual(3, len(r))
        self.assertEqual("Aron is 8 years old and is not doing sports.", r[-1])

        # sets does not have duplicates so if all items in r are equal the set will have only 1 value
        # here all items should be different
        self.assertEqual(3, len(set(r)))

    def test_func_with_arguments_1(self):
        self.test_func_with_arguments(n=1)

    def test_func_with_arguments_3(self):
        self.test_func_with_arguments(n=3)

    def test_func_with_arguments_10(self):
        self.test_func_with_arguments(n=10)


if __name__ == '__main__':
    unittest.main()