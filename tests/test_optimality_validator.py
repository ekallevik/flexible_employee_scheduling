import pytest

from results.optimality_validator import OptimalityValidator

WORKING_DAYS_1 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
WORKING_DAYS_2 = [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1]
WORKING_DAYS_3 = [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1]


@pytest.fixture()
def validator():
    return OptimalityValidator(None, None, None)


@pytest.fixture()
def saturdays():
    return [5, 12]


@pytest.mark.parametrize(
    "working_days, consecutive_day_limit, expected",
    [
        ([0, 0, 0, 0, 0, 0, 0, 0], 3, 0),
        ([1, 1, 0, 1, 1, 0, 1, 1], 3, 0),
        ([1, 1, 1, 0, 1, 0, 1, 1], 3, 1),
        ([1, 1, 1, 0, 0, 1, 1, 1], 3, 2),
        ([1, 1, 1, 1, 0, 1, 1, 1], 3, 3),
        ([1, 1, 1, 1, 1, 1, 1, 1], 3, 6),
    ],
)
def test_count_consecutive_days(validator, working_days, consecutive_day_limit, expected):

    assert (
        validator.count_consecutive_day_violations(working_days, consecutive_day_limit) == expected
    )


@pytest.mark.parametrize(
    "working_days, consecutive_day_limit, expected",
    [([1, 1, 1, 1, 1], 5, True), ([1, 1, 1, 1, 0], 5, False)],
)
def test_violates_consecutive_days(validator, working_days, consecutive_day_limit, expected):

    assert validator.violates_consecutive_days(working_days, consecutive_day_limit) == expected


@pytest.mark.parametrize(
    "working_days, consecutive_day_limit", [([1, 1, 1, 1, 0, 1], 5), ([1, 1, 1, 1], 5)]
)
def test_violates_consecutive_days_raises_error_on_wrong_input(
    validator, working_days, consecutive_day_limit
):

    with pytest.raises(ValueError):
        validator.violates_consecutive_days(working_days, consecutive_day_limit)


@pytest.mark.parametrize(
    "working_days, expected",
    [
        ([1, 1, 0, 1, 1], {"working_days": 0, "off_days": 1}),
        ([1, 0, 1, 1, 0], {"working_days": 0, "off_days": 1}),
        ([1, 0, 1, 0, 1], {"working_days": 1, "off_days": 2}),
        ([0, 1, 0, 1, 0], {"working_days": 2, "off_days": 1}),
        ([0, 1, 1, 1, 0], {"working_days": 0, "off_days": 0}),
    ],
)
def test_count_isolated_days_violations(validator, working_days, expected):

    assert validator.count_isolated_days_violations(working_days) == expected


@pytest.mark.parametrize(
    "working_days, expected",
    [([1, 1, 0], False), ([1, 0, 1], False), ([0, 1, 0], True), ([0, 1, 1], False),],
)
def test_violates_isolated_working_days(validator, working_days, expected):

    assert validator.violates_isolated_working_days(working_days) == expected


@pytest.mark.parametrize(
    "working_days, expected",
    [([1, 1, 0], False), ([1, 0, 1], True), ([0, 1, 0], False), ([0, 1, 1], False),],
)
def test_violates_isolated_off_days(validator, working_days, expected):

    assert validator.violates_isolated_off_days(working_days) == expected


@pytest.mark.parametrize("working_days", [([1, 1, 1, 1]), ([1, 1])])
def test_violates_isolated_working_days_raises_error_on_wrong_input(validator, working_days):

    with pytest.raises(ValueError):
        validator.violates_isolated_working_days(working_days)


@pytest.mark.parametrize("working_days", [([1, 1, 1, 1]), ([1, 1])])
def test_violates_isolated_off_days_raises_error_on_wrong_input(validator, working_days):

    with pytest.raises(ValueError):
        validator.violates_isolated_working_days(working_days)


@pytest.mark.parametrize(
    "working_days, saturdays, expected",
    [
        ([1, 1, 1, 1, 1, 1], [5], False),
        ([1, 1, 1, 1, 1, 1, 1], [5], True),
        ([1, 1, 1, 1, 1, 1, 1, 1], [5], False),
    ],
)
def test_is_last_working_day_a_sunday(validator, working_days, saturdays, expected):

    assert validator.is_last_working_day_a_sunday(working_days, saturdays) == expected


@pytest.mark.parametrize(
    "working_days, expected", [(WORKING_DAYS_1, 0), (WORKING_DAYS_2, 2), (WORKING_DAYS_3, 1),]
)
def test_count_partial_weekend_violations(validator, saturdays, working_days, expected):

    assert validator.count_partial_weekend_violations(working_days, saturdays) == expected


def test_count_partial_weekend_violations_raises_error_on_wrong_input():
    pass

@pytest.mark.parametrize("weekend, expected", [
    ([1, 1], 0),
    ([1, 0], 1),
    ([0, 1], 1),
    ([0, 0], 0),
])
def test_violates_isolated_working_days(validator, weekend, expected):

    assert validator.violates_partial_weekends(weekend) == expected


def test_violates_partial_weekends_raises_error_on_wrong_input():
    pass
