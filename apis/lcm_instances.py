from flask_restx import Namespace, Resource, fields
from flask import request, abort
from core import app_quota_manager
from core import exceptions
from core import db_manager
from core.enums import InstantiationStatus, NsiNotificationType, NsiStatus
from core import intent_translation_manager
from core import nsmf_manager
from core import vao_manager
from marshmallow import Schema
from threading import Thread
import marshmallow.fields

api = Namespace('lcm/instances', description='Application-Aware NSM LCM APIs')

# Intent Model Specification

location_constraint = api.model('location_constraint', {
    'geographicalAreaId': fields.String,
    'applicationComponentId': fields.String
}, strict=True)

computing_constraint = api.model('computing_constraint', {
    'applicationComponentId': fields.String,
    'ram': fields.String(required=True),
    'cpu': fields.String(required=True),
    'storage': fields.String(required=True)
}, strict=True)

profile_params = api.model('profile_params', {
    'availability': fields.Float,
    'errorRate': fields.Float,
    'isolationLevel': fields.String(enum=['NO_ISOLATION', 'LOGICAL', 'PHYSICAL']),
    'maximumNumberUE': fields.Integer,
    'uESpeed': fields.Float,
    'uEDensity': fields.Float,
    'ulThroughput': fields.Float,
    'dlThroughput': fields.Float,
    'ulThroughputUE': fields.Float,
    'dlThroughputUE': fields.Float,
    'dataRate': fields.Float,
    'delay': fields.Float,
    'jitter': fields.Float,
    'priorityLevel': fields.Integer,
    'rrhCellPower0': fields.String,
    'enableLteEnb': fields.Boolean
}, strict=True)
slice_profile = api.model('slice_profile', {
    'sliceType': fields.String(enum=['EMBB', 'URLLC', 'MMTC'], required=True),
    'profileParams': fields.Nested(profile_params, required=True,
                                   description='Slice Profile Parameters', skip_none=True)
}, strict=True)
networking_constraint = api.model('networking_constraint', {
    'applicationComponentId': fields.String,
    'applicationComponentEndpointId': fields.String,
    'sliceProfiles': fields.Nested(slice_profile, required=True, as_list=True,
                                   description='List of Slice Profiles', skip_none=True)
}, strict=True)

intent = api.model('intent', {
    'callbackUrl': fields.String,
    'locationConstraints': fields.Nested(location_constraint, required=True, as_list=True,
                                         description='List of Geographical Area Identifiers', skip_none=True),
    'computingConstraints': fields.Nested(computing_constraint, required=True, as_list=True,
                                          description='List of Computing Constraints', skip_none=True),
    'networkingConstraints': fields.Nested(networking_constraint, required=True, as_list=True,
                                           description='List of Networking Constraints', skip_none=True)
}, strict=True)

# Vertical Application Slice Status Model Specification

vas_status = api.model('vas_status', {
    'vasi': fields.String(required=True),
    'status': fields.String(enum=['INSTANTIATING', 'INSTANTIATED',
                                  'FAILED', 'TERMINATING', 'TERMINATED'], required=True)
}, strict=True)

network_slice_status = api.model('network_slice_status', {
    'networkSliceId': fields.String(required=True),
    'status': fields.String(enum=['INSTANTIATING', 'INSTANTIATED',
                                  'FAILED', 'TERMINATING', 'TERMINATED'], required=True)
}, strict=True)

cluster_info = api.model('cluster_info', {
    'certificate-authority-data': fields.String(required=True),
    'server': fields.String(required=True)
}, strict=True)
cluster = api.model('cluster', {
    'cluster': fields.Nested(cluster_info, required=True, description='K8s Cluster', skip_none=True),
    'name': fields.String(required=True)
}, strict=True)
context_info = api.model('context_info', {
    'cluster': fields.String(required=True),
    'user': fields.String(required=True),
    'namespace': fields.String(required=True)
}, strict=True)
context = api.model('context', {
    'context': fields.Nested(context_info, required=True, description='K8s Context', skip_none=True),
    'name': fields.String(required=True)
}, strict=True)
preferences = api.model('preferences', {}, strict=True)
user_info = api.model('user_info', {
    'token': fields.String(required=True),
    'client-key-data': fields.String(required=True)
}, strict=True)
user = api.model('user', {
    'user': fields.Nested(user_info, required=True, description='K8s User', skip_none=True),
    'name': fields.String(required=True)
}, strict=True)
kubeconfig = api.model('kubeconfig', {
    'geographicalAreaId': fields.String(required=True),
    'apiVersion': fields.String(required=True),
    'clusters': fields.Nested(cluster, required=True, as_list=True, description='K8s Clusters', skip_none=True),
    'contexts': fields.Nested(context, required=True, as_list=True, description='K8s Contexts', skip_none=True),
    'current-context': fields.String(required=True),
    'kind': fields.String(enum=['Config'], required=True),
    'preferences': fields.Nested(preferences, required=True, description='K8s Preferences', skip_none=True),
    'users': fields.Nested(user, required=True, as_list=True, description='K8s Users', skip_none=True)
}, strict=True)

vas_info = api.model('vas_info', {
    'vasStatus': fields.Nested(vas_status, required=True,
                               description='Vertical Application Slice Status', skip_none=True),
    'vaQuotaInfo': fields.Nested(kubeconfig, required=True, as_list=True,
                                 description='Vertical Application Quota Information', skip_none=True),
    'networkSliceStatus': fields.Nested(network_slice_status, required=True,
                                        description='5G Network Slice Status', skip_none=True),
    'vasConfiguration': fields.Nested(intent, required=True,
                                      description='Vertical Application Slice Configuration', skip_none=True),
    'nestId': fields.String(required=True)
}, strict=True)

# Error Message Model Specification

error_msg = api.model('error_msg', {'message': fields.String(required=True)})


# Network Slice Notification Model Specification

notification = api.model('notification', {
    'nsiId': fields.String(required=True),
    'nsiNotifType': fields.String(enum=['STATUS_CHANGED', 'ERROR'], required=True),
    'nsiStatus': fields.String(enum=['CREATED', 'INSTANTIATING', 'INSTANTIATED', 'CONFIGURING',
                                     'TERMINATING', 'TERMINATED', 'FAILED', 'OTHER'], required=True),
    'errors': fields.String(enum=['STATUS_TRANSITION'])
})


class VASPostSchema(Schema):
    context = marshmallow.fields.Str()


vas_post_schema = VASPostSchema()


@api.route('/')
class VASCtrl(Resource):

    @api.doc('Get the list of Vertical Application Slice Instances.')
    @api.marshal_list_with(vas_info, skip_none=True)
    @api.response(200, 'Vertical Application Slice Instances')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def get(self):
        # Get all Vertical Application Slice Status
        _vas_status = None
        try:
            _vas_status = db_manager.get_va_status()
        except exceptions.DBException as e:
            abort(500, str(e))

        # Build the info model for each Vertical Application Slice Status
        # retrieving the correspondent Network Slice Status and Vertical
        # Application Quota Status
        _vas_info = []
        for status in _vas_status:
            vasi = status[0]
            _network_slice_status = None
            _va_quota_status = None
            try:
                ns_id = status[2]
                if ns_id is not None:
                    _network_slice_status = db_manager.get_network_slice_status_by_id(ns_id)
                else:
                    _network_slice_status = (None, None)
                _va_quota_status = db_manager.get_va_quota_status_by_vas_id(vasi)
            except (exceptions.DBException, exceptions.NotExistingEntityException) as e:
                abort(500, str(e))

            _vas_info.append({
                'vasStatus': {
                    'vasi': vasi,
                    'status': status[1]
                },
                'vaQuotaInfo': [quota[1] for quota in _va_quota_status],
                'networkSliceStatus': {
                    'networkSliceId': _network_slice_status[0],
                    'status': _network_slice_status[1]
                },
                'vasConfiguration': status[3],
                'nestId': status[4]
            })

        return _vas_info

    @api.doc('Request Vertical Application Slice Instantiation.')
    @api.expect(intent, validate=True)
    @api.response(200, 'Vertical Application Slice Identifier', model=fields.String)
    @api.response(400, 'Bad Request', model=error_msg)
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self):
        # Validate request parameters
        errors = vas_post_schema.validate(request.args)
        if errors:
            abort(400, str(errors))

        vas_intent = request.json

        # Create entry for vertical application slice
        vertical_application_slice_id = None
        try:
            vertical_application_slice_id = \
                db_manager.insert_va_status(InstantiationStatus.INSTANTIATING.name, vas_intent)
        # Abort if DB entry cannot be created
        except exceptions.DBException as e:
            abort(500, str(e))

        # Allocate K8s quota for each compute constraint
        k8s_configs = None
        try:
            k8s_configs = app_quota_manager.allocate_quotas(vas_intent['locationConstraints'],
                                                            vas_intent['computingConstraints'])
        # Abort if quota cannot be allocated
        except (exceptions.MissingContextException, exceptions.QuantitiesMalformedException) as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException as e2:
                abort(500, str(e2))
            abort(400, str(e))

        # Create DB entry for each allocated quota binding them to the
        # vertical_application_slice_id previously generated
        try:
            for k8s_config in k8s_configs:
                db_manager.insert_va_quota_status(k8s_config, vertical_application_slice_id)
        # Abort if DB entry cannot be created
        except exceptions.DBException as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException:
                pass
            finally:
                abort(500, str(e))

        # Retrieve the most appropriate NEST for the instantiation of the 5G Network Slice
        nest_id = None
        try:
            nest_id = intent_translation_manager.select_nest(vas_intent['networkingConstraints'])
            db_manager.update_va_status_with_nest_id(vertical_application_slice_id, nest_id)
        # Abort if Intent mapping fail or DB entry cannot be created
        except (exceptions.FailedIntentTranslationException, exceptions.DBException) as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException:
                pass
            finally:
                abort(500, str(e))
        # Abort if NEST cannot be selected due to condition not implemented
        except exceptions.NotImplementedException as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException as ee:
                abort(500, str(ee))
            abort(501, str(e))
        # Abort if Networking Constraints do not specify URLLC or EMBB NEST
        except exceptions.MalformedIntentException as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException as ee:
                abort(500, str(ee))
            abort(400, str(e))

        ns_id = None
        try:
            # jsessionid = nsmf_manager.nsmf_login('admin', 'admin')
            jsessionid = '1A530637289A03B07199A44E8D531427'
            ns_id = nsmf_manager.nsmf_create_slice_info(nest_id, jsessionid, vertical_application_slice_id)
            nsmf_manager.nsmf_instantiate(ns_id, jsessionid)
        # Abort if the 5G Network Slice instantiation request failed
        except exceptions.FailedNSMFRequestException as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException:
                pass
            finally:
                abort(500, str(e))

        try:
            db_manager.insert_network_slice_status(ns_id, InstantiationStatus.INSTANTIATING.name)
            db_manager.update_va_status_with_ns(vertical_application_slice_id, ns_id)
        # Abort if DB entries cannot be created and/or updated
        except exceptions.DBException as e:
            try:
                db_manager.update_va_with_status(vertical_application_slice_id, InstantiationStatus.FAILED.name)
            # Abort if DB entry cannot be updated
            except exceptions.DBException:
                pass
            finally:
                abort(500, str(e))

        return vertical_application_slice_id


@api.route('/network_slice/status_update')
class NetworkSliceStatusUpdateHandler(Resource):

    @api.doc('Notification Handler, manage the Network Slice status update')
    @api.expect(notification, validate=True)
    @api.response(200, 'No Content')
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self):
        # Handle Network Slice status notification
        _notification = request.json
        ns_id = _notification['nsiId']
        nsi_notification_type = NsiNotificationType[_notification['nsiNotifType']].name

        try:
            db_manager.get_network_slice_status_by_id(ns_id)
        except exceptions.NotExistingEntityException as e:
            abort(400, str(e))

        # Abort if notification type is 'ERROR'
        if nsi_notification_type == NsiNotificationType.ERROR.name:
            try:
                db_manager.update_network_slice_status(ns_id, InstantiationStatus.FAILED.name)
                db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)

                thread = Thread(target=vao_manager.notify, kwargs={'ns_id': ns_id})
                thread.start()

                return '', 200
            # Abort if DB entries cannot be updated
            except exceptions.DBException as e:
                try:
                    db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)
                # Abort if DB entry cannot be updated
                except exceptions.DBException:
                    pass
                finally:
                    abort(500, str(e))
        elif nsi_notification_type == NsiNotificationType.STATUS_CHANGED.name:
            nsi_status = NsiStatus[_notification['nsiStatus']].name
            # Ignore if the status received is CREATED, CONFIGURING or OTHER
            if nsi_status == NsiStatus.CREATED.name or nsi_status == NsiStatus.CONFIGURING.name \
                    or nsi_status == NsiStatus.OTHER.name:
                return '', 200
            # Abort if the Network Slice instantiation failed
            elif nsi_status == NsiStatus.FAILED.name:
                try:
                    db_manager.update_network_slice_status(ns_id, InstantiationStatus.FAILED.name)
                    db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)

                    thread = Thread(target=vao_manager.notify, kwargs={'ns_id': ns_id})
                    thread.start()

                    return '', 200
                # Abort if DB entries cannot be updated
                except exceptions.DBException as e:
                    try:
                        db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)
                    # Abort if DB entry cannot be updated
                    except exceptions.DBException:
                        pass
                    finally:
                        abort(500, str(e))
            # Update the Network Slice status if the notification is INSTANTIATING or TERMINATING
            elif nsi_status == NsiStatus.INSTANTIATING.name:
                try:
                    db_manager.update_network_slice_status(ns_id, InstantiationStatus[nsi_status].name)
                    return '', 200
                # Abort if DB entry cannot be updated
                except exceptions.DBException as e:
                    try:
                        db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)
                    # Abort if DB entry cannot be updated
                    except exceptions.DBException:
                        pass
                    finally:
                        abort(500, str(e))
            # Update the Network Slice status and the VAS status if the notification is INSTANTIATED or TERMINATED
            elif nsi_status == NsiStatus.INSTANTIATED.name:
                try:
                    db_manager.update_network_slice_status(ns_id, InstantiationStatus[nsi_status].name)
                    db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus[nsi_status].name)

                    thread = Thread(target=vao_manager.notify, kwargs={'ns_id': ns_id})
                    thread.start()

                    return '', 200
                # Abort if DB entries cannot be updated
                except exceptions.DBException as e:
                    try:
                        db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus.FAILED.name)
                    # Abort if DB entry cannot be updated
                    except exceptions.DBException:
                        pass
                    finally:
                        abort(500, str(e))
            elif nsi_status == NsiStatus.TERMINATING.name:
                try:
                    db_manager.update_network_slice_status(ns_id, InstantiationStatus[nsi_status].name)
                    return '', 200
                except exceptions.DBException as e:
                    abort(500, str(e))
            elif nsi_status == NsiStatus.TERMINATED.name:
                try:
                    db_manager.update_network_slice_status(ns_id, InstantiationStatus[nsi_status].name)
                    db_manager.update_va_with_status_by_network_slice(ns_id, InstantiationStatus[nsi_status].name)
                    return '', 200
                except exceptions.DBException as e:
                    abort(500, str(e))
            else:
                abort(400, 'Unrecognized Notification Type.')


@api.route('/<uuid:vasi>')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASCtrlByID(Resource):

    @api.doc('Get a Vertical Application Slice by ID.')
    @api.marshal_with(vas_info, skip_none=True)
    @api.response(200, 'Vertical Application Slice Instance')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def get(self, vasi):
        # Get Vertical Application Slice Status by VASI
        vasi = str(vasi)
        _vas_status = None
        try:
            _vas_status = db_manager.get_va_status_by_id(vasi)
        except exceptions.NotExistingEntityException as e:
            abort(404, str(e))
        except exceptions.DBException as e:
            abort(500, str(e))

        # Build the info model for the Vertical Application Slice Status
        # retrieving the correspondent Network Slice Status and Vertical
        # Application Quota Status
        _vas_info = None
        _network_slice_status = None
        _va_quota_status = None
        try:
            ns_id = _vas_status[2]
            if ns_id is not None:
                _network_slice_status = db_manager.get_network_slice_status_by_id(ns_id)
            else:
                _network_slice_status = (None, None)
            _va_quota_status = db_manager.get_va_quota_status_by_vas_id(vasi)
        except (exceptions.DBException, exceptions.NotExistingEntityException) as e:
            abort(500, str(e))

        _vas_info = {
            'vasStatus': {
                'vasi': vasi,
                'status': _vas_status[1]
            },
            'vaQuotaInfo': [quota[1] for quota in _va_quota_status],
            'networkSliceStatus': {
                'networkSliceId': _network_slice_status[0],
                'status': _network_slice_status[1]
            },
            'vasConfiguration': _vas_status[3],
            'nestId': _vas_status[4]
        }

        return _vas_info

    @api.doc('Delete a Vertical Application Slice by ID.')
    @api.response(204, 'Vertical Application Slice Instance Deleted')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def delete(self, vasi):
        # Get Vertical Application Slice Status by VASI
        vasi = str(vasi)
        _vas_status = None
        try:
            _vas_status = db_manager.get_va_status_by_id(vasi)
        except exceptions.NotExistingEntityException as e:
            abort(404, str(e))
        except exceptions.DBException as e:
            abort(500, str(e))

        if _vas_status[1] != InstantiationStatus.FAILED.name and\
                _vas_status[1] != InstantiationStatus.TERMINATED.name:
            abort(405, 'Vertical Application Slice Info' + vasi +
                  ' cannot be removed. Current Status: ' + _vas_status[1])

        ns_id = _vas_status[2]
        if ns_id is not None:
            try:
                db_manager.delete_network_slice_status_by_id(ns_id)
                return '', 204
            except exceptions.DBException as e:
                abort(500, str(e))

        try:
            db_manager.delete_va_quota_by_vas_id(vasi)
            db_manager.delete_va_status_by_id(vasi)
        except exceptions.DBException as e:
            abort(500, str(e))

        return '', 204


@api.route('/<uuid:vasi>/scale')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASScaleCtrl(Resource):

    @api.doc('Request to scale a Vertical Application Slice Instance')
    @api.expect(intent, validate=True)
    @api.response(204, 'Vertical Application Slice Instance Scaling Requested')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(405, 'Method Not Allowed', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def patch(self, vasi):
        # Get Vertical Application Slice Status by VASI
        vasi = str(vasi)
        _vas_status = None
        try:
            _vas_status = db_manager.get_va_status_by_id(vasi)
        except exceptions.NotExistingEntityException as e:
            abort(404, str(e))
        except exceptions.DBException as e:
            abort(500, str(e))

        if _vas_status[1] != InstantiationStatus.INSTANTIATED.name:
            abort(405, 'Vertical Application Slice ' + vasi +
                  ' cannot be scaled. Current Status: ' + _vas_status[1])

        # Validate request parameters
        errors = vas_post_schema.validate(request.args)
        if errors:
            abort(400, str(errors))

        _va_quota_status = None
        try:
            _va_quota_status = db_manager.get_va_quota_status_by_vas_id(vasi)
        except exceptions.DBException as e:
            abort(500, str(e))

        vas_intent = request.json
        app_quota_manager.update_quotas(vas_intent['locationConstraints'],
                                        vas_intent['computingConstraints'],
                                        _va_quota_status)

        ns_id = _vas_status[2]
        jsessionid = '1A530637289A03B07199A44E8D531427'
        try:
            nsmf_manager.nsmf_scale(
                ns_id=ns_id,
                nssi_id=nsmf_manager.nsmf_get_nssi(ns_id, jsessionid),
                networking_constraints=vas_intent['networkingConstraints'],
                jsessionid=jsessionid
            )
        except exceptions.FailedNSMFRequestException as e:
            abort(500, str(e))

        return '', 204


@api.route('/<uuid:vasi>/terminate')
@api.param('vasi', 'Vertical Application Slice Identifier')
class VASTerminationCtrl(Resource):

    @api.doc('Request a Vertical Application Slice Instance termination')
    @api.response(204, 'Vertical Application Slice Instance Termination Requested')
    @api.response(401, 'Unauthorized', model=error_msg)
    @api.response(403, 'Forbidden', model=error_msg)
    @api.response(404, 'Not Found', model=error_msg)
    @api.response(405, 'Method Not Allowed', model=error_msg)
    @api.response(500, 'Internal Server Error', model=error_msg)
    def post(self, vasi):
        # Get Vertical Application Slice Status by VASI
        vasi = str(vasi)
        _vas_status = None
        try:
            _vas_status = db_manager.get_va_status_by_id(vasi)
        except exceptions.NotExistingEntityException as e:
            abort(404, str(e))
        except exceptions.DBException as e:
            abort(500, str(e))

        if _vas_status[1] != InstantiationStatus.INSTANTIATED.name and\
                _vas_status[1] != InstantiationStatus.FAILED.name:
            abort(405, 'Vertical Application Slice ' + vasi +
                  ' cannot be terminated. Current Status: ' + _vas_status[1])

        try:
            db_manager.update_va_with_status(vasi, InstantiationStatus.TERMINATING.name)
        except exceptions.DBException as e:
            abort(500, str(e))

        _va_quota_status = None
        try:
            _va_quota_status = db_manager.get_va_quota_status_by_vas_id(vasi)
        except exceptions.DBException as e:
            abort(500, str(e))

        app_quota_manager.delete_quotas(_va_quota_status)

        ns_id = _vas_status[2]
        if ns_id is not None:
            try:
                # jsessionid = nsmf_manager.nsmf_login('admin', 'admin')
                jsessionid = '1A530637289A03B07199A44E8D531427'
                nsmf_manager.nsmf_terminate(ns_id, jsessionid)
            except exceptions.FailedNSMFRequestException as e:
                abort(500, str(e))

        return '', 204
