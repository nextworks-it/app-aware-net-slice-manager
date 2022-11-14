from flask_restx import Namespace, Resource, fields
from flask import request, abort
from core import db_manager
from core import exceptions

api = Namespace('location', description='Application-Aware NSM Location APIs')

# Geographical Area Model Specification

geographical_area = api.model('geographical_area', {
    'geographicalAreaId': fields.String(),
    'name': fields.String(required=True),
    'k8sContext': fields.String(required=True),
    'latitude': fields.Float(required=True),
    'longitude': fields.Float(required=True),
    'coverageRadius': fields.Float(required=True),
    'segment': fields.String(required=True)
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
        # Get all locations
        locations = None
        try:
            locations = db_manager.get_locations()
        except exceptions.DBException as e:
            abort(500, str(e))

        _location = []
        for location in locations:
            _location.append({
                'geographicalAreaId': location[0],
                'name': location[1],
                'k8sContext': location[2],
                'latitude': location[3],
                'longitude': location[4],
                'coverageRadius': location[5],
                'segment': location[6]
            })

        return _location

    @api.doc('Create Geographical Locations Area.')
    @api.expect(geographical_area, validate=True)
    @api.response(200, 'Geographical Area Id')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self):
        # Create location
        geographical_area_id = None
        try:
            geographical_area_id = db_manager.insert_location(request.json)
        except exceptions.DBException as e:
            abort(500, str(e))

        return geographical_area_id


@api.route('/<uuid:geographical_area_id>')
@api.param('geographical_area_id', 'Geographical Area Identifier')
class LocationCtrlById(Resource):

    @api.doc('Update a Geographical Location by Id')
    @api.expect(geographical_area, validate=True)
    @api.response(204, 'Geographical Area Id')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def patch(self, geographical_area_id):
        # Patch a Geographical Area Location
        try:
            db_manager.update_location(str(geographical_area_id), request.json)
        except exceptions.DBException as e:
            abort(500, str(e))

        return '', 204

    @api.doc('Delete a Geographical Location by Id')
    @api.response(204, 'Geographical Area Id')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def delete(self, geographical_area_id):
        # Delete a Geographical Area Location
        try:
            db_manager.delete_location(str(geographical_area_id))
        except exceptions.DBException as e:
            abort(500, str(e))

        return '', 204
