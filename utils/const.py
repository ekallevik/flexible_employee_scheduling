import os

ENVIRONMENT = "local" if not os.environ.get("CI", False) else "CI"

DEFAULT_COMPETENCY = [0]
DEFAULT_CONTRACTED_HOURS = 40
DEFAULT_DAILY_REST_HOURS = 8
DEFAULT_WEEKLY_REST_HOURS = 36
DEFAULT_DAILY_OFFSET = 4
DEFAULT_WEEKLY_OFFSET = 0

LIMIT_CONSECUTIVE_DAYS = 5

DAYS_IN_WEEK = 7
SATURDAY_INDEX = 5
SUNDAY_INDEX = 6

DESIRED_SHIFT_DURATION = [6, 12]
ALLOWED_SHIFT_DURATION = [5, 12]

WEEKLY_REST_DURATION = [36, 90]
MAX_REWARDED_WEEKLY_REST = 72

TIME_DEFINING_SHIFT_DAY = 20

NUMBER_OF_PREFERENCES_PER_WEEK = [1, 3]
DURATION_OF_PREFERENCES = [4, 8]  # IN HOURS


# Used in Implicit Model
HOURS_IN_A_DAY = 24
HOURS_IN_A_WEEK = 24*7

L_WORK = 0


M_WORK_ALLOCATION = 1000
