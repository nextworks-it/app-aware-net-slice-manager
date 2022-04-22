from core import nest_catalogue_url, qi
from core.enums import SliceType
from core.exceptions import FailedIntentTranslationException
from typing import List, Tuple
from sys import maxsize
import requests


# Retrieve all the NESTs from the NEST Catalogue
def get_nests() -> List[dict]:
    try:
        response = requests.get('http://' + nest_catalogue_url + '/ns/catalogue/nestemplate')
    except requests.exceptions.RequestException as e:
        raise FailedIntentTranslationException(str(e))
    return response.json()


# Assign a Slice Type and the minimum delay to each NEST in the list received as input parameter
def map_nests_to_slice_type(nests: List[dict]) -> List[Tuple[dict, SliceType, int]]:
    nest_slice_type_map = []
    for nest in nests:
        qos_params = nest['gst']['sliceQoSparams']
        if qos_params is None:
            continue

        urllc = 0
        embb = 0
        min_delay = maxsize
        for qos_param in qos_params:
            qosi = qos_param['qosIndicator']
            if qosi is None:
                continue

            qii = qi[qosi]
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


def select_urllc_nest(delay: float) -> dict:
    nests = get_nests()
    nest_slice_type_map = map_nests_to_slice_type(nests)
    nest_slice_type_map = filter_nest_slice_type_map(nest_slice_type_map, SliceType.URLLC)
    nest_slice_type_map = \
        [nest_slice_type for nest_slice_type in nest_slice_type_map if float(nest_slice_type[2]) <= delay]

    if len(nest_slice_type_map) == 0:
        raise FailedIntentTranslationException('No NEST available with specified constraints.')

    return nest_slice_type_map[0][0]


def select_embb_nest(isolation_level: str) -> dict:
    nests = get_nests()
    nest_slice_type_map = map_nests_to_slice_type(nests)
    nest_slice_type_map = filter_nest_slice_type_map(nest_slice_type_map, SliceType.EMBB)

    _nest_slice_type_map = []
    for nest_slice_type in nest_slice_type_map:
        isolation = nest_slice_type[0]['gst']['isolation']
        if isolation is None:
            continue

        _isolation_level = isolation['isolationLevel']
        if _isolation_level is None:
            continue

        if isolation_level == _isolation_level:
            _nest_slice_type_map.append(nest_slice_type)

    if len(_nest_slice_type_map) == 0:
        raise FailedIntentTranslationException('No NEST available with specified constraints.')

    return _nest_slice_type_map[0][0]
