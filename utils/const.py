import os

ENVIRONMENT = "local" if not os.environ.get("CI", False) else "CI"
