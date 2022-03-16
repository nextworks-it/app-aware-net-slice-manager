from flask_restx import Namespace, Resource, fields
import uuid

api = Namespace('lcm/instances', description='Application-Aware NSM LCM APIs')

# Vertical Application Slice Status Model Specification

vas_status = api.model('Vertical Application Slice Status', {
    'vasi': fields.String(required=True),
    'status': fields.String(enum=['INSTANTIATING', 'INSTANTIATED',
                                  'FAILED', 'TERMINATING', 'TERMINATED'], required=True)
})

network_slice_status = api.model('5G Network Slice Status', {
    'networkSliceId': fields.String(required=True),
    'status': fields.String(enum=['INSTANTIATING', 'INSTANTIATED',
                                  'FAILED', 'TERMINATING', 'TERMINATED'], required=True)
})

cluster_info = api.model('K8s Cluster Info', {
    'certificate-authority-data': fields.String(required=True),
    'server': fields.String(required=True)
})
cluster = api.model('K8s Cluster', {
    'cluster': fields.Nested(cluster_info, required=True, description='K8s Cluster'),
    'name': fields.String(required=True)
})
context_info = api.model('K8s Context Info', {
    'cluster': fields.String(required=True),
    'user': fields.String(required=True),
    'namespace': fields.String(required=True)
})
context = api.model('K8s Context', {
    'context': fields.Nested(context_info, required=True, description='K8s Context'),
    'name': fields.String(required=True)
})
preferences = api.model('K8s Preferences', {})
user_info = api.model('K8s User Info', {
    'token': fields.String(required=True),
    'client-key-data': fields.String(required=True)
})
user = api.model('K8s User', {
    'user': fields.Nested(user_info, required=True, description='K8s User'),
    'name': fields.String(required=True)
})
kubeconfig = api.model('K8s Config', {
    'apiVersion': fields.String(required=True),
    'clusters': fields.Nested(cluster, required=True, as_list=True, description='K8s Clusters'),
    'contexts': fields.Nested(context, required=True, as_list=True, description='K8s Contexts'),
    'current-context': fields.String(required=True),
    'kind': fields.String(enum=['Config'], required=True),
    'preferences': fields.Nested(preferences, required=True, description='K8s Preferences'),
    'users': fields.Nested(user, required=True, as_list=True, description='K8s Users')
})

vas_info = api.model('Vertical Application Slice Status Information', {
    'vasStatus': fields.Nested(vas_status, required=True, description='Vertical Application Slice Status'),
    'vaQuotaInfo': fields.Nested(kubeconfig, required=True, description='Vertical Application Quota Information'),
    'networkSliceStatus': fields.Nested(network_slice_status, required=True, description='5G Network Slice Status')
})

# Intent Model Specification

location_constraint = api.model('Location Constraint', {'geographicalAreaId': fields.String(required=True)})

computing_constraint = api.model('Computing Constraint', {
    'applicationComponentId': fields.String(required=True),
    'ram': fields.Float(required=True),
    'cpu': fields.Integer(required=True),
    'storage': fields.Integer(required=True)
})

profile_params = api.model('Profile Params', {
    'availability': fields.Float(required=True),
    'errorRate': fields.Float(required=True),
    'isolationLevel': fields.String(enum=['NO_ISOLATION', 'LOGICAL'], required=True),
    'maximumNumberUE': fields.Integer(required=True),
    'uESpeed': fields.Float(required=True),
    'uEDensity': fields.Float(required=True),
    'ulThroughput': fields.Float(required=True),
    'dlThroughput': fields.Float(required=True),
    'ulThroughputUE': fields.Float(required=True),
    'dlThroughputUE': fields.Float(required=True)
})
slice_profile = api.model('Slice Profile', {
    'sliceType': fields.String(enum=['EMBB', 'URLLC', 'MMTC'], required=True),
    'profileParams': fields.Nested(profile_params, required=True, description='Slice Profile Parameters')
})
networking_constraint = api.model('Networking Constraint', {
    'applicationComponentId': fields.String(required=True),
    'applicationComponentEndpointId': fields.String(required=True),
    'sliceProfiles': fields.Nested(slice_profile, required=True, as_list=True, description='List of Slice Profiles')
})

intent = api.model('Intent', {
    'locationConstraints': fields.Nested(location_constraint, required=True, as_list=True,
                                         description='List of Geographical Area Identifiers'),
    'computingConstraints': fields.Nested(computing_constraint, required=True, as_list=True,
                                          description='List of Computing Constraints'),
    'networkingConstraints': fields.Nested(networking_constraint, required=True, as_list=True,
                                           description='List of Networking Constraints')
})

scale_intent = api.model('Scale Intent', {
    'locationConstraints': fields.Nested(location_constraint, required=True, as_list=True,
                                         description='List of Geographical Area Identifiers'),
    'computingConstraints': fields.Nested(computing_constraint, required=True, as_list=True,
                                          description='List of Computing Constraints')
})

# Error Message Model Specification

error_msg = api.model('Error Message', {'message': fields.String(required=True)})


@api.route('/')
class VASCtrl(Resource):

    @api.doc('Get the list of Vertical Application Slice Instances.')
    @api.marshal_list_with(vas_info)
    @api.response(200, 'Vertical Application Slice Instances')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def get(self):
        return []

    @api.doc('Request Vertical Application Slice Instantiation.')
    @api.expect(intent, validate=True)
    @api.response(200, 'Vertical Application Slice Identifier', model=fields.String)
    @api.response(400, 'Bad Request', model=error_msg)
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self):
        return str(uuid.uuid4())


@api.route('/<uuid:vasi>')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASCtrlByID(Resource):

    @api.doc('Get a Vertical Application Slice by ID.')
    @api.marshal_with(vas_info)
    @api.response(200, 'Vertical Application Slice Instance')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def get(self, vasi):
        print(vasi)
        return {}

    @api.doc('Delete a Vertical Application Slice by ID.')
    @api.response(204, 'Vertical Application Slice Instance Deleted')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def delete(self, vasi):
        print(vasi)
        return '', 204


@api.route('/<uuid:vasi>/scale')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASScaleCtrl(Resource):

    @api.doc('Request to scale a Vertical Application Slice Instance')
    @api.expect(scale_intent, validate=True)
    @api.response(204, 'Vertical Application Slice Instance Scaling Requested')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def patch(self, vasi):
        print(vasi)
        return '', 204


@api.route('/<uuid:vasi>/terminate')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASTerminationCtrl(Resource):

    @api.doc('Request a Vertical Application Slice Instance termination')
    @api.response(204, 'Vertical Application Slice Instance Termination Requested')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self, vasi):
        print(vasi)
        return '', 204
