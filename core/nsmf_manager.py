from core import nsmf_url
from core.exceptions import FailedNSMFRequestException
from core import nsmf_log
import requests


# Login to the NSMF
def nsmf_login(usr: str, psw: str) -> str:
    params = {'username': usr, 'password': psw}
    try:
        response = requests.post('http://' + nsmf_url + '/login', params=params)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 200:
        msg = 'Login failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    return response.cookies.get('JSESSIONID')


# Request the creation of the info entry for the new 5G Network Slice
def nsmf_create_slice_info(nest_id: str, jsessionid: str, vasi: str) -> str:
    cookies = {'JSESSIONID': jsessionid}
    payload = {
        'name': vasi,
        'description': vasi,
        'nestId': nest_id
    }
    try:
        response = requests.post('http://' + nsmf_url + '/vs/basic/nslcm/ns/nest', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 201:
        msg = 'Slice Info creation failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    return response.json()


# Request the instantiation of the 5G Network Slice
def nsmf_instantiate(ns_id: str, jsessionid: str):
    cookies = {'JSESSIONID': jsessionid}
    payload = {'nsiId': ns_id}
    try:
        response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/instantiate', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 202:
        msg = ns_id + ' Instantiation failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)


def nsmf_terminate(ns_id: str, jsessionid: str):
    cookies = {'JSESSIONID': jsessionid}
    payload = {'nsiId': ns_id}
    try:
        response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/terminate', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 202:
        msg = ns_id + ' Termination request failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)


def nsmf_get_nssi(ns_id: str, jsessionid: str) -> str:
    cookies = {'JSESSIONID': jsessionid}
    try:
        response = requests.get('http://' + nsmf_url + '/vs/basic/nslcm/ns/' + ns_id, cookies=cookies)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 200:
        msg = ns_id + ' GET info request failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    return response.json()['networkSliceSubnetIds'][0]


def nsmf_scale(ns_id: str, nssi_id: str, networking_constraints: dict, jsessionid: str):
    cookies = {'JSESSIONID': jsessionid}
    payload = {
        'actionType': 'CORE_RAN_CONFIGURATION',
        'nsiId': ns_id,
        'nssiId': nssi_id,
        'sliceSubnetType': 'CORE',
        'mmeInitialApnMaxBitrateDl': networking_constraints[0]['sliceProfiles'][0]['profileParams']['dlThroughput'],
        'mmeInitialApnMaxBitrateUl': networking_constraints[0]['sliceProfiles'][0]['profileParams']['ulThroughput']
    }

    try:
        response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/configure', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 202:
        msg = ns_id + ' Scale request failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)
