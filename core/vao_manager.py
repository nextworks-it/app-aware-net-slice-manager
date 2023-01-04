from core import db_manager
from core.exceptions import NotExistingEntityException, DBException, FailedVAONotificationException
from core import vao_log
import requests


def notify(ns_id: str):
    # Get Vertical Application Slice Status by VASI
    _vas_status = None
    try:
        _vas_status = db_manager.get_va_status_by_network_slice(ns_id)
    except (NotExistingEntityException, DBException) as e:
        msg = str(e)
        vao_log.info(msg)
        raise FailedVAONotificationException(msg)
    vasi = _vas_status[0]
    notification_uri = _vas_status[3]['callbackUrl']

    # Build the info model for the Vertical Application Slice Status
    # retrieving the correspondent Network Slice Status and Vertical
    # Application Quota Status
    _vas_info = None
    _network_slice_status = None
    _va_quota_status = None
    try:
        _network_slice_status = db_manager.get_network_slice_status_by_id(ns_id)
        _va_quota_status = db_manager.get_va_quota_status_by_vas_id(vasi)
    except (DBException, NotExistingEntityException) as e:
        msg = str(e)
        vao_log.info(msg)
        raise FailedVAONotificationException(msg)

    _vas_info = {
        'vasStatus': {
            'vasi': vasi,
            'status': _vas_status[1]
        },
        'vaQuotaInfo': [quota[1] for quota in _va_quota_status],
        'networkSliceStatus': {
            'networkSliceId': _network_slice_status[0],
            'status': _network_slice_status[1]
        },
        'vasConfiguration': _vas_status[3],
        'nestId': _vas_status[4]
    }

    try:
        requests.post(notification_uri, json=_vas_info)

        vao_log.info('Notification sent to %s : %s', notification_uri, _vas_info)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        vao_log.info(msg)
        raise FailedVAONotificationException(msg)
