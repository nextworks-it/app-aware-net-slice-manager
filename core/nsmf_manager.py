from core import nsmf_url
from core.exceptions import FailedNSMFRequestException
from core import nsmf_log
import requests
from requests.auth import HTTPBasicAuth
import os
import string
import random
import uuid

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
    return str(uuid.uuid4())
    username = os.getenv("NSMF_USERNAME", default=None) 
    password = os.getenv("NSMF_PASSWORD", default=None) 
    cookies = {'JSESSIONID': jsessionid}
    payload = {
        'name': vasi,
        'description': vasi,
        'nestId': nest_id
    }
    try:
        if username:
            nsmf_log.info("Auth with user/pass")
            response = requests.post('http://' + nsmf_url + '/vs/basic/nslcm/ns/nest', auth=HTTPBasicAuth(username, password), json=payload)
        else:
            nsmf_log.info("Auth with cookies")
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
    username = os.getenv("NSMF_USERNAME", default="admin") 
    password = os.getenv("NSMF_PASSWORD", default="password") 
    cookies = {'JSESSIONID': jsessionid}
    payload = {'nsiId': ns_id}
    try:
        if username:
            nsmf_log.info("Auth with user/pass")
            response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/instantiate', auth=HTTPBasicAuth(username, password), json=payload)
        else:
            nsmf_log.info("Auth with cookies")
            response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/instantiate', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 202 and status_code != 200:
        msg = ns_id + ' Instantiation failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)


def nsmf_terminate(ns_id: str, jsessionid: str):
    username = os.getenv("NSMF_USERNAME", default="admin") 
    password = os.getenv("NSMF_PASSWORD", default="password") 
    cookies = {'JSESSIONID': jsessionid}
    payload = {'nsiId': ns_id}
    try:
        if username:
            nsmf_log.info("Auth with user/pass")
            response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/terminate', auth=HTTPBasicAuth(username, password), json=payload)
        else:
            nsmf_log.info("Auth with cookies")
            response = requests.put('http://' + nsmf_url + '/vs/basic/nslcm/ns/' +
                                ns_id + '/action/terminate', cookies=cookies, json=payload)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

    status_code = response.status_code
    if status_code != 202 and status_code != 200:
        msg = ns_id + ' Termination request failed, status code: ' + str(status_code)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)

def nsmf_onboard_dummy_nst(jsessionid = None):
    username = os.getenv("NSMF_USERNAME", default=None) 
    password = os.getenv("NSMF_PASSWORD", default=None) 
    cookies = {'JSESSIONID': jsessionid}

    id = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    payload={
       "nst": {
         "nstId": "nstid-" + id,
         "nstName": "nstname-" + id,
         "nstVersion": "v0.0.1",
         "nstProvider": "Nextworks",
         "nstServiceProfileList": [
           {
             "serviceProfileId": "ath-inin-urllc-sp-real",
             "maxNumberofUEs": 15000,
             "latency": 10,
             "resourceSharingLevel": True,
             "sST": "URLLC",
             "availability": 7.68,
             "delayTolerance": False,
             "deterministicComm": {
               "detCommAvailability": False
             },
             "dLThptPerSlice": 500000000,
             "dLThptPerUE": 50000,
             "guaThpt": 500000,
             "maxThpt": 1150000,
             "uLThptPerSlice": 500000000,
             "uLThptPerUE": 15000,
             "maxPktSize": 3500,
             "maxNumberofConns": 200000,
             "survivalTime": "30 days",
             "resourceType": "DelayCriticalGBR"
           }
         ],
         "nsst": {
             "nsstId": None,
             "nsstName": "nsst",
             "nsstVersion": "1.0",
             "nsstProvider": None,
             "operationalState": False,
             "administrativeState": None,
             "nsInfo": None,
             "sliceProfileList": [],
             "nsstList": [],
             "nsdInfo": None,
             "type": "E2E"
         }
       }
     }
    
    try:   
        if username:
            response = requests.post('http://' + nsmf_url + '/ns/catalogue/nstemplate', auth=HTTPBasicAuth(username, password), json=payload)
        else:
            response = requests.post('http://' + nsmf_url + '/ns/catalogue/nstemplate', cookies=cookies)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)
    
    status_code = response.status_code
    return response.text
    

def nsmf_translate_nst_to_nest(nst_id, jsessionid = None):
# curl -X POST -u admin:nextworks --location localhost:8083/ns/catalogue/nsttranslator \
# --header 'Content-Type: application/json' \
# --data '{
#     "nstId":  "nstid-'${ID}'"
# }'
    username = os.getenv("NSMF_USERNAME", default=None) 
    password = os.getenv("NSMF_PASSWORD", default=None) 
    cookies = {'JSESSIONID': jsessionid}

    nst_id = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    payload={
        "nstId":  nst_id
    }
    
    try:   
        if username:
            response = requests.post('http://' + nsmf_url + '/ns/catalogue/nsttranslator', auth=HTTPBasicAuth(username, password), json=payload)
        else:
            response = requests.post('http://' + nsmf_url + '/ns/catalogue/nsttranslator', cookies=cookies)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        nsmf_log.info(msg)
        raise FailedNSMFRequestException(msg)
    
    status_code = response.status_code
    return response.text