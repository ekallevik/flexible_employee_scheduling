import os

ENVIRONMENT = "local" if not os.environ.get("CI", False) else "CI"

DEFAULT_COMPETENCY = [0]

DAYS_IN_WEEK = 7
SATURDAY_INDEX = 5
SUNDAY_INDEX = 6
