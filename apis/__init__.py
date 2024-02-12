from flask_restx import Api
from .lcm_instances import api as ns1
from .location import api as ns2

api = Api(
    title='Application-Aware Network Slice Manager',
    version='1.0',
    description='Application-Aware Network Slice Manager LCM APIs.'
)

api.add_namespace(ns1)
api.add_namespace(ns2)
