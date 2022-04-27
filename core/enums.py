import enum


class InstantiationStatus(enum.Enum):
    INSTANTIATING = 1
    INSTANTIATED = 2
    FAILED = 3
    TERMINATING = 4
    TERMINATED = 5


class SliceType(enum.Enum):
    URLLC = 1
    EMBB = 2


class IsolationLevel(enum.Enum):
    NoIsolation = 1
    Logical = 2
    Physical = 3
