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
    MMTC = 3


class IsolationLevel(enum.Enum):
    NO_ISOLATION = 1
    LOGICAL = 2
    PHYSICAL = 3


class IsolationLevelMapping(enum.Enum):
    NO_ISOLATION = 'NoIsolation'
    LOGICAL = 'Logical'
    PHYSICAL = 'Physical'


class NsiNotificationType(enum.Enum):
    STATUS_CHANGED = 1
    ERROR = 2


class NsiStatus(enum.Enum):
    CREATED = 1
    INSTANTIATING = 2
    INSTANTIATED = 3
    CONFIGURING = 4
    TERMINATING = 5
    TERMINATED = 6
    FAILED = 7
    OTHER = 8


class Group(enum.Enum):
    EDGE = 1
    CORE = 2
    CLOUD = 3
