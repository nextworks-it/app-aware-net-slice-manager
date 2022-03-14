from flask_restx import Namespace, Resource

api = Namespace('lcm/instances', description='Application-Aware NSM LCM APIs')

# Add Intent Model


@api.route('/')
class VASCtrl(Resource):

    @api.doc('Get the list of Vertical Application Slice Instances.')
    @api.response(200, 'Vertical Application Slice Instances')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(500, 'Internal Server Error')
    def get(self):
        return 'List of VAS instances.'

    @api.doc('Request Vertical Application Slice Instantiation.')
    @api.response(200, 'Vertical Application Slice Identifier')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(500, 'Internal Server Error')
    def post(self):
        return 'New VAS requested.'


@api.route('/<vasi>')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASCtrlByID(Resource):

    @api.doc('Get a Vertical Application Slice by ID.')
    @api.response(200, 'Vertical Application Slice Instance')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @api.response(500, 'Internal Server Error')
    def get(self, vasi):
        print(vasi)
        return 'VAS instance.'

    @api.doc('Delete a Vertical Application Slice by ID.')
    @api.response(200, 'Vertical Application Slice Instance Deleted')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @api.response(500, 'Internal Server Error')
    def delete(self, vasi):
        print(vasi)
        return 'VAS instance deleted.'


@api.route('/<vasi>/scale')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASScaleCtrl(Resource):

    @api.doc('Request to scale a Vertical Application Slice Instance')
    @api.response(200, 'Vertical Application Slice Instance Scaling Requested')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @api.response(500, 'Internal Server Error')
    def patch(self, vasi):
        print(vasi)
        return 'VAS instance scaled'


@api.route('/<vasi>/terminate')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASTerminationCtrl(Resource):

    @api.doc('Request a Vertical Application Slice Instance termination')
    @api.response(200, 'Vertical Application Slice Instance Termination Requested')
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @api.response(500, 'Internal Server Error')
    def post(self, vasi):
        print(vasi)
        return 'VAS instance termination requested.'
