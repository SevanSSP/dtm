def test_func_without_arguments_1(test_func_without_arguments):
    print(type(test_func_without_arguments))
    r = test_func_without_arguments(1)
    assert len(r) == 3
    assert r[0] == "Some response."

    # sets does not have duplicates so if all items in r are equal the set will have only 1 value
    # here all items should be different
    assert len(set(r)) == 1


def test_func_without_arguments_3(test_func_without_arguments):
    r = test_func_without_arguments(3)
    assert len(r) == 3
    assert r[0] == "Some response."

    # sets does not have duplicates so if all items in r are equal the set will have only 1 value
    # here all items should be different
    assert len(set(r)) == 1


def test_func_with_arguments_1(test_func_with_arguments):
    r = test_func_with_arguments(1)

    assert len(r) == 3
    assert r[-1] == "Aron is 8 years old and is not doing sports."

    # sets does not have duplicates so if all items in r are equal the set will have only 1 value
    # here all items should be different
    assert len(set(r)) == 3


def test_func_with_arguments_3(test_func_with_arguments):
    r = test_func_with_arguments(3)

    assert len(r) == 3
    assert r[-1] == "Aron is 8 years old and is not doing sports."

    # sets does not have duplicates so if all items in r are equal the set will have only 1 value
    # here all items should be different
    assert len(set(r)) == 3


def test_func_with_arguments_10(test_func_with_arguments):
    r = test_func_with_arguments(10)

    assert len(r) == 3
    assert r[-1] == "Aron is 8 years old and is not doing sports."

    # sets does not have duplicates so if all items in r are equal the set will have only 1 value
    # here all items should be different
    assert len(set(r)) == 3
