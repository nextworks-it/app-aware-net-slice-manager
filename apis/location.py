from flask_restx import Namespace, Resource, fields

api = Namespace('location', description='Application-Aware NSM Location APIs')

# Geographical Area Model Specification

geographical_area = api.model('geographical_area', {
    'geographicalAreaId': fields.String(required=True),
    'latitude': fields.Float(required=True),
    'longitude': fields.Float(required=True),
    'coverageRadio': fields.Float(required=True)
})

# Error Message Model Specification

error_msg = api.model('error_msg', {'message': fields.String(required=True)})


@api.route('/')
class LocationCtrl(Resource):

    @api.doc('Get the list of Geographical Locations.')
    @api.marshal_list_with(geographical_area)
    @api.response(200, 'Geographical Locations')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def get(self):
        return []
