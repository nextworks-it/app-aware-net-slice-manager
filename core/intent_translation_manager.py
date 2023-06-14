from core import nest_catalogue_url, qi
from core.enums import SliceType, IsolationLevel, IsolationLevelMapping
from core.exceptions import FailedIntentTranslationException, NotImplementedException, MalformedIntentException
from typing import List, Tuple
from sys import maxsize
import requests


# Retrieve all the NESTs from the NEST Catalogue
def get_nests() -> List[dict]:
    try:
        response = requests.get('http://' + nest_catalogue_url + '/ns/catalogue/nestemplate')
    except requests.exceptions.RequestException as e:
        raise FailedIntentTranslationException(str(e))

    status_code = response.status_code
    if status_code != 200:
        raise FailedIntentTranslationException("NEST GET failed, status code: " + str(status_code))

    return response.json()


# Assign a Slice Type and the minimum delay to each NEST in the list received as input parameter
def map_nests_to_slice_type(nests: List[dict]) -> List[Tuple[dict, SliceType, int]]:
    nest_slice_type_map = []
    for nest in nests:
        gst = nest.get('gst')
        if gst is None:
            continue

        qos_params = gst.get('sliceQoSparams')
        if qos_params is None:
            continue

        urllc = 0
        embb = 0
        min_delay = maxsize
        for qos_param in qos_params:
            qosi = qos_param.get('qosIndicator')
            if qosi is None:
                continue

            qii = qi.get(qosi)
            if qii is None:
                continue

            if qii[0] == SliceType.URLLC.name:
                urllc += 1
            elif qii[0] == SliceType.EMBB.name:
                embb += 1
            else:
                continue

            delay = int(qii[1])
            if delay < min_delay:
                min_delay = delay

        if urllc == 0 and embb == 0:
            continue
        elif urllc >= embb:
            slice_type = SliceType.URLLC
        else:
            slice_type = SliceType.EMBB

        nest_slice_type_map.append((nest, slice_type, min_delay))

    return nest_slice_type_map


# Filter the <NEST, Slice Type> list received as input in a <NEST, Slice Type> list
# containing only NEST with the specified Slice Type
def filter_nest_slice_type_map(nest_slice_type_map: List[Tuple[dict, SliceType, int]],
                               slice_type: SliceType) -> List[Tuple[dict, SliceType, int]]:
    return [nest_slice_type for nest_slice_type in nest_slice_type_map if nest_slice_type[1].name == slice_type.name]


def filter_by_isolation_level(nest_slice_type_map: List[Tuple[dict, SliceType, int]],
                              isolation_level: str) -> List[Tuple[dict, SliceType, int]]:
    _nest_slice_type_map = []
    for nest_slice_type in nest_slice_type_map:
        gst = nest_slice_type[0].get('gst')
        if gst is None:
            continue

        isolation = gst.get('isolation')
        if isolation is None:
            continue

        _isolation_level = isolation.get('isolationLevel')
        if _isolation_level is None:
            continue

        if isolation_level == _isolation_level:
            _nest_slice_type_map.append(nest_slice_type)

    return _nest_slice_type_map


def filter_by_dl_throughput(nest_slice_type_map: List[Tuple[dict, SliceType, int]],
                            dl_throughput: float) -> List[Tuple[dict, SliceType, int]]:
    _nest_slice_type_map = []
    for nest_slice_type in nest_slice_type_map:
        gst = nest_slice_type[0].get('gst')
        if gst is None:
            continue

        downlink_throughput_ns = gst.get('downlinkThroughputNS')
        if downlink_throughput_ns is None:
            continue

        maximum_dl = downlink_throughput_ns.get('maximumDL')
        if maximum_dl is None:
            continue

        maximum_dl = float(maximum_dl)
        if maximum_dl >= dl_throughput:
            _nest_slice_type_map.append(nest_slice_type)

    return _nest_slice_type_map


def filter_by_ul_throughput(nest_slice_type_map: List[Tuple[dict, SliceType, int]],
                            ul_throughput: float) -> List[Tuple[dict, SliceType, int]]:
    _nest_slice_type_map = []
    for nest_slice_type in nest_slice_type_map:
        gst = nest_slice_type[0].get('gst')
        if gst is None:
            continue

        uplink_throughput_ns = gst.get('uplinkThroughputNS')
        if uplink_throughput_ns is None:
            continue

        max_uplink_throughput = uplink_throughput_ns.get('maxUplinkThroughput')
        if max_uplink_throughput is None:
            continue

        max_uplink_throughput = float(max_uplink_throughput)
        if max_uplink_throughput >= ul_throughput:
            _nest_slice_type_map.append(nest_slice_type)

    return _nest_slice_type_map


def select_urllc_nest(delay: float, isolation_level: str) -> dict:
    nests = get_nests()
    nest_slice_type_map = map_nests_to_slice_type(nests)
    nest_slice_type_map = filter_nest_slice_type_map(nest_slice_type_map, SliceType.URLLC)

    nest_slice_type_map = \
        [nest_slice_type for nest_slice_type in nest_slice_type_map if float(nest_slice_type[2]) <= delay]

    nest_slice_type_map = filter_by_isolation_level(nest_slice_type_map, isolation_level)

    if len(nest_slice_type_map) == 0:
        raise FailedIntentTranslationException('No URLLC NEST available with specified constraints.')

    return nest_slice_type_map[0][0]


def select_embb_nest(isolation_level: str,
                     dl_throughput: float,
                     ul_throughput: float) -> dict:
    nests = get_nests()
    nest_slice_type_map = map_nests_to_slice_type(nests)
    nest_slice_type_map = filter_nest_slice_type_map(nest_slice_type_map, SliceType.EMBB)

    nest_slice_type_map = filter_by_isolation_level(nest_slice_type_map, isolation_level)

    if dl_throughput != 0:
        nest_slice_type_map = filter_by_dl_throughput(nest_slice_type_map, dl_throughput)

    if ul_throughput != 0:
        nest_slice_type_map = filter_by_ul_throughput(nest_slice_type_map, ul_throughput)

    if len(nest_slice_type_map) == 0:
        raise FailedIntentTranslationException('No EMBB NEST available with specified constraints.')

    return nest_slice_type_map[0][0]


def select_nest(networking_constraints: List[dict]) -> str:
    urllc = 0
    embb = 0
    min_delay = maxsize
    max_isolation_level = IsolationLevel.NO_ISOLATION
    max_dl_throughput = 0
    max_ul_throughput = 0

    for networking_constraint in networking_constraints:
        slice_profiles = networking_constraint['sliceProfiles']
        for slice_profile in slice_profiles:
            slice_type = slice_profile['sliceType']
            profile_params = slice_profile['profileParams']
            if slice_type == SliceType.URLLC.name:
                urllc += 1

                delay = profile_params.get('delay')
                if delay is not None:
                    if delay < min_delay:
                        min_delay = delay

                isolation_level = profile_params.get('isolationLevel')
                if isolation_level is not None:
                    isolation_level = IsolationLevel[isolation_level]
                    if isolation_level.value > max_isolation_level.value:
                        max_isolation_level = isolation_level
            elif slice_type == SliceType.EMBB.name or slice_type == SliceType.MMTC.name:
                embb += 1

                isolation_level = profile_params.get('isolationLevel')
                if isolation_level is not None:
                    isolation_level = IsolationLevel[isolation_level]
                    if isolation_level.value > max_isolation_level.value:
                        max_isolation_level = isolation_level

                dl_throughput = profile_params.get('dlThroughput')
                if dl_throughput is not None:
                    if dl_throughput > max_dl_throughput:
                        max_dl_throughput = dl_throughput

                ul_throughput = profile_params.get('ulThroughput')
                if ul_throughput is not None:
                    if ul_throughput > max_ul_throughput:
                        max_ul_throughput = ul_throughput
            else:
                continue

    if urllc > 0 and embb > 0:
        raise NotImplementedException('Case with urllc > 0 and embb > 0 not implemented, abort.')
    elif urllc == 0 and embb == 0:
        raise MalformedIntentException('Malformed intent [networkingConstraints], abort')
    elif urllc > 0:
        nest = select_urllc_nest(min_delay, IsolationLevelMapping[max_isolation_level.name].value)
    else:
        nest = select_embb_nest(IsolationLevelMapping[max_isolation_level.name].value,
                                max_dl_throughput, max_ul_throughput)

    return nest['gst']['gstId']
