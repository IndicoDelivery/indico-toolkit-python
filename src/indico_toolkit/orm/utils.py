import re

UNDERSCORE_PATTERN = re.compile(
    r"""
    (?<=[0-9])      # preceded by number
    (?=[a-zA-Z])    # followed by letter
    |
    (?<=[a-zA-Z])   # preceded by letter
    (?=[0-9])       # followed by number
    |
    (?<=[a-z])      # preceded by lowercase
    (?=[A-Z])       # followed by uppercase
    |
    (?<=[A-Z])      # preceded by uppercase
    (?=[A-Z][a-z])  # followed by uppercase then lowercase
    """,
    re.X,
)


def snake_cased(name: str) -> str:
    return UNDERSCORE_PATTERN.sub("_", name).casefold()
