import enum


class InstantiationStatus(enum.Enum):
    INSTANTIATING = 1
    INSTANTIATED = 2
    FAILED = 3
    TERMINATING = 4
    TERMINATED = 5
