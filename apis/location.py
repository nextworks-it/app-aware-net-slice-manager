from flask_restx import Namespace, Resource, fields
from flask import request, abort
from core import db_manager
from core import exceptions

api = Namespace('location', description='Application-Aware NSM Location APIs')

# Geographical Area Model Specification


class DictItem(fields.Raw):
    pass


node = api.model('node', {
    'name': fields.String(required=True),
    'labels': DictItem(required=True)
}, strict=True)

cluster = api.model('cluster', {
    'name': fields.String(required=True),
    'type': fields.String(required=True),
    'nodes': fields.Nested(node, required=True, as_list=True,
                           description='List of cluster nodes', skip_none=True)
}, strict=True)

geographical_area = api.model('geographical_area', {
    'geographicalAreaId': fields.String(),
    'locationName': fields.String(required=True),
    'cluster': fields.Nested(cluster, required=True, description='cluster for this location', skip_none=True),
    'latitude': fields.Float(required=True),
    'longitude': fields.Float(required=True),
    'coverageRadius': fields.Float(required=True),
    'segment': fields.String(required=True)
}, strict=True)

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
            cluster_id = location[2]
            _cluster = None
            _nodes = None

            try:
                _cluster = db_manager.get_cluster_by_id(cluster_id)
                _nodes = db_manager.get_cluster_nodes_by_cluster_id(cluster_id)
            except exceptions.DBException as e:
                abort(500, str(e))

            _location.append({
                'geographicalAreaId': location[0],
                'locationName': location[1],
                'cluster': {
                    'name': _cluster[1],
                    'type': _cluster[2],
                    'nodes': [{'name': n[1], 'labels': n[2]} for n in _nodes]
                },
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
        location = request.json

        _cluster = location['cluster']
        cluster_id = None
        try:
            cluster_id = db_manager.insert_cluster(_cluster)
        except exceptions.DBException as e:
            abort(500, str(e))

        nodes = location['cluster']['nodes']
        for _node in nodes:
            try:
                db_manager.insert_cluster_node(_node, cluster_id)
            except exceptions.DBException as e:
                abort(500, str(e))

        geographical_area_id = None
        try:
            geographical_area_id = db_manager.insert_location(location, cluster_id)
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
        # Delete a Geographical Area Location
        try:
            location = db_manager.get_location_by_id(str(geographical_area_id))

            cluster_id = location[2]
            db_manager.delete_cluster_node_by_cluster_id(cluster_id)
            db_manager.delete_cluster(cluster_id)
            db_manager.delete_location(str(geographical_area_id))
        except exceptions.DBException as e:
            abort(500, str(e))

        # Create location
        location = request.json

        _cluster = location['cluster']
        cluster_id = None
        try:
            cluster_id = db_manager.insert_cluster(_cluster)
        except exceptions.DBException as e:
            abort(500, str(e))

        nodes = location['cluster']['nodes']
        for _node in nodes:
            try:
                db_manager.insert_cluster_node(_node, cluster_id)
            except exceptions.DBException as e:
                abort(500, str(e))

        try:
            db_manager.insert_location(location, cluster_id)
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
            location = db_manager.get_location_by_id(str(geographical_area_id))

            cluster_id = location[2]
            db_manager.delete_cluster_node_by_cluster_id(cluster_id)
            db_manager.delete_cluster(cluster_id)
            db_manager.delete_location(str(geographical_area_id))
        except exceptions.DBException as e:
            abort(500, str(e))

        return '', 204
