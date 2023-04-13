from kubernetes import client, config
from kubernetes.config.kube_config import ConfigException
from kubernetes.client.rest import ApiException
from core import quota_log
from core import exceptions
from core import db_manager
from base64 import b64decode
import uuid
import re
from core import platform_manager_client

pattern = re.compile('^([+-]?[0-9.]+)([eEinumkKMGTP]*[-+]?[0-9]*)$')


def create_constrained_ns(core_api: client.CoreV1Api, host: str, computing_constraint) -> str:
    # Create a namespace with random uuid as name
    ns_name = str(uuid.uuid4())
    ns = client.V1Namespace(metadata=client.V1ObjectMeta(name=ns_name))
    core_api.create_namespace(ns)

    quota_log.info('Created Namespace %s in K8s cluster %s.', ns_name, host)

    # Create the quota resource to constrain the created namespace
    rq = client.V1ResourceQuota(
        metadata=client.V1ObjectMeta(name=ns_name + '-quota'),
        spec=client.V1ResourceQuotaSpec(hard={
            'requests.cpu': computing_constraint['cpu'],
            'requests.memory': computing_constraint['ram'],
            'limits.cpu': computing_constraint['cpu'],
            'limits.memory': computing_constraint['ram'],
            'requests.storage': computing_constraint['storage']
        })
    )
    core_api.create_namespaced_resource_quota(ns_name, rq)

    quota_log.info('Created ResourceQuota %s-quota in K8s cluster %s.', ns_name, host)

    return ns_name


def create_constrained_sa(core_api: client.CoreV1Api, host: str,
                          rbac_api: client.RbacAuthorizationV1Api, ns_name: str) -> str:
    # Create a ServiceAccount with random uuid as name
    sa_name = str(uuid.uuid4())
    sa = client.V1ServiceAccount(metadata=client.V1ObjectMeta(name=sa_name))
    core_api.create_namespaced_service_account(ns_name, sa)

    quota_log.info('Created ServiceAccount %s in K8s cluster %s.', sa_name, host)

    sa_secret = client.V1Secret(metadata=client.V1ObjectMeta(name=sa_name + '-token', annotations={
        'kubernetes.io/service-account.name': sa_name}), type='kubernetes.io/service-account-token')
    core_api.create_namespaced_secret(ns_name, sa_secret)

    quota_log.info('Created Secret Token for Service Account %s in K8s cluster %s.', sa_name, host)

    # Create ClusterRole to define Service Accounts permissions in given namespace(s)
    c_role = client.V1ClusterRole(
        metadata=client.V1ObjectMeta(name='ns-sa-permissions'),
        rules=[
            client.V1PolicyRule(
                api_groups=['', 'extensions', 'apps'],
                resources=['*'],
                verbs=['*']
            ),
            client.V1PolicyRule(
                api_groups=['batch'],
                resources=['jobs', 'cronjobs'],
                verbs=['*']
            )
        ]
    )
    try:
        rbac_api.create_cluster_role(c_role)
        quota_log.info('Created ClusterRole ns-sa-permissions in K8s cluster %s.', host)
    except ApiException as e:
        if e.status == 409:
            quota_log.info('ClusterRole already exists.')
        else:
            raise e

    # Bind the created ServiceAccount to the ClusterRole to limit the access to the given namespace
    rb = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=sa_name + '-role-binding'),
        subjects=[
            client.V1Subject(
                kind='ServiceAccount',
                name=sa_name,
                namespace=ns_name
            )
        ],
        role_ref=client.V1RoleRef(
            api_group='rbac.authorization.k8s.io',
            kind='ClusterRole',
            name='ns-sa-permissions'
        )
    )
    rbac_api.create_namespaced_role_binding(ns_name, rb)

    quota_log.info('Created RoleBinding %s-role-binding in K8s cluster %s.', sa_name, host)

    return sa_name


def allocate_quota(computing_constraint, context: str):
    try:
        # Load the kubeconfig at .kube/config and change context to create
        # the resources for the quota in the specified K8s cluster
        platform_manager_client.update_local_config()
        config.load_kube_config(context=context)
    except ConfigException:
        # If .kube/config context is missing
        quota_log.error('Missing context ' + context + ' in .kube/config, abort.')
        raise exceptions.MissingContextException('Missing context ' + context)

    # Get host of K8s cluster
    host = client.Configuration.get_default_copy().host

    # Create K8s clients
    with client.ApiClient() as api_client:
        core_api = client.CoreV1Api(api_client)
        rbac_api = client.RbacAuthorizationV1Api(api_client)

    # Create the resources for the quota
    ns_name = create_constrained_ns(core_api, host, computing_constraint)
    sa_name = create_constrained_sa(core_api, host, rbac_api, ns_name)
    secret = core_api.read_namespaced_secret(sa_name + '-token', ns_name)

    # Get the ca.crt and token of the ServiceAccount created
    sa_secret_data = secret.data
    sa_secret_ca_crt = sa_secret_data['ca.crt']
    sa_secret_token = b64decode(sa_secret_data['token']).decode('utf-8')

    # Build and return the kubeconfig that should be used to manage the resources in the new quota
    cluster_name = str(uuid.uuid4())
    return {
        'apiVersion': 'v1',
        'clusters': [{
            'cluster': {
                'certificate-authority-data': sa_secret_ca_crt,
                'server': host
            },
            'name': cluster_name
        }],
        'contexts': [{
            'context': {
                'cluster': cluster_name,
                'namespace': ns_name,
                'user': sa_name
            },
            'name': context
        }],
        'current-context': context,
        'kind': 'Config',
        'preferences': {},
        'users': [{
            'user': {
                'token': sa_secret_token,
                'client-key-data': sa_secret_ca_crt
            },
            'name': sa_name
        }]
    }


def aggregate_quotas(cs_a: dict, cs_b: dict) -> dict:
    if cs_a is None:
        return {
            'cpu': cs_b['cpu'],
            'ram': cs_b['ram'],
            'storage': cs_b['storage']
        }

    cpu_a = pattern.search(cs_a['cpu'])
    ram_a = pattern.search(cs_a['ram'])
    sto_a = pattern.search(cs_a['storage'])

    return {
        'cpu': str(int(cpu_a.group(1)) + int(pattern.search(cs_b['cpu']).group(1))) + cpu_a.group(2),
        'ram': str(int(ram_a.group(1)) + int(pattern.search(cs_b['ram']).group(1))) + ram_a.group(2),
        'storage': str(int(sto_a.group(1)) + int(pattern.search(cs_b['storage']).group(1))) + sto_a.group(2)
    }


def allocate_quotas(location_constraints, computing_constraints):
    # Allocate quota for each computing constraint in the request
    k8s_configs = []

    for computing_constraint in computing_constraints:
        # Requirements must match the regex e.g. 4Gi
        if not pattern.match(computing_constraint.get('cpu')) or \
                not pattern.match(computing_constraint.get('ram') or
                                  not pattern.match(computing_constraint.get('storage'))):
            raise exceptions.QuantitiesMalformedException('Quantities must match the regular expression '
                                                          '^([+-]?[0-9.]+)([eEinumkKMGTP]*[-+]?[0-9]*)$')

    components_location_map = {}
    for loc in location_constraints:
        if loc['geographicalAreaId'] not in components_location_map:
            components_location_map[loc['geographicalAreaId']] = []

        components_location_map[loc['geographicalAreaId']].append(loc['applicationComponentId'])

    quotas = {}
    for geographicalAreaId, components in components_location_map.items():
        quota = None
        for component in components:
            quota = aggregate_quotas(quota, [cc for cc in computing_constraints
                                             if cc['applicationComponentId'] == component][0])
        quotas[geographicalAreaId] = quota

    _locations = db_manager.get_locations()
    locations = []
    for _location in _locations:
        locations.append({
            'geographicalAreaId': _location[0],
            'name': _location[1],
            'k8sContext': _location[2],
            'latitude': _location[3],
            'longitude': _location[4],
            'coverageRadius': _location[5],
            'segment': _location[6]
        })
    for geographicalAreaId, quota in quotas.items():
        k8s_config = allocate_quota(quota, [location for location in locations
                                            if location['geographicalAreaId']
                                            == geographicalAreaId][0]['k8sContext'])
        k8s_config['geographicalAreaId'] = geographicalAreaId
        k8s_configs.append(k8s_config)

    return k8s_configs


def delete_quota(kubeconfig):
    platform_manager_client.update_local_config()
    config.load_kube_config(context=kubeconfig['current-context'])
    with client.ApiClient() as api_client:
        core_api = client.CoreV1Api(api_client)

    try:
        core_api.delete_namespace(name=kubeconfig['contexts'][0]['context']['namespace'])
    except ApiException as e:
        raise e


def delete_quotas(quotas):
    try:
        for quota in quotas:
            delete_quota(quota[1])
    except ApiException as e:
        raise e
