class ServiceAccountSecretException(Exception):
    pass


class MissingContextException(Exception):
    pass


class QuantitiesMalformedException(Exception):
    pass


class DBException(Exception):
    pass


class NotExistingEntityException(Exception):
    pass


class FailedIntentTranslationException(Exception):
    pass


class NotImplementedException(Exception):
    pass


class MalformedIntentException(Exception):
    pass


class FailedNSMFRequestException(Exception):
    pass


class FailedVAONotificationException(Exception):
    pass

class PlatformManagerNotReadyException(Exception):
    pass
