from kubernetes import client, config
from kubernetes.config.kube_config import ConfigException
from kubernetes.client.rest import ApiException
from core import log
from core import exceptions
from base64 import b64decode
import uuid


def get_computing_constraints():
    return None


def create_constrained_ns(core_api: client.CoreV1Api, host: str, requests_cpu: str, requests_memory: str,
                          limits_cpu: str, limits_memory: str) -> str:
    # Create a namespace with random uuid as name
    ns_name = str(uuid.uuid4())
    ns = client.V1Namespace(metadata=client.V1ObjectMeta(name=ns_name))
    core_api.create_namespace(ns)

    log.info('Created Namespace %s in K8s cluster %s.', ns_name, host)

    # Create the quota resource to constrain the created namespace
    rq = client.V1ResourceQuota(
        metadata=client.V1ObjectMeta(name=ns_name + '-quota'),
        spec=client.V1ResourceQuotaSpec(hard={
            'requests.cpu': requests_cpu,
            'requests.memory': requests_memory,
            'limits.cpu': limits_cpu,
            'limits.memory': limits_memory
        })
    )
    core_api.create_namespaced_resource_quota(ns_name, rq)

    log.info('Created ResourceQuota %s-quota in K8s cluster %s.', ns_name, host)

    return ns_name


def create_constrained_sa(core_api: client.CoreV1Api, host: str,
                          rbac_api: client.RbacAuthorizationV1Api, ns_name: str) -> str:
    # Create a ServiceAccount with random uuid as name
    sa_name = str(uuid.uuid4())
    sa = client.V1ServiceAccount(metadata=client.V1ObjectMeta(name=sa_name))
    core_api.create_namespaced_service_account(ns_name, sa)

    log.info('Created ServiceAccount %s in K8s cluster %s.', sa_name, host)

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
        log.info('Created ClusterRole ns-sa-permissions in K8s cluster %s.', host)
    except ApiException as e:
        if e.status == 409:
            log.info('ClusterRole already exists.')
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

    log.info('Created RoleBinding %s-role-binding in K8s cluster %s.', sa_name, host)

    return sa_name


def allocate_quota(context: str, requests_cpu: str, requests_memory: str, limits_cpu: str, limits_memory: str):
    get_computing_constraints()

    try:
        # Load the kubeconfig at .kube/config and change context to create
        # the resources for the quota in the specified K8s cluster
        config.load_kube_config(context=context)
    except ConfigException:
        # If .kube/config context is missing
        log.error('Missing kubeconfig at .kube/config, abort.')
        raise exceptions.MissingContextException('Missing context %s.', context)

    # Get host of K8s cluster
    host = client.Configuration.get_default_copy().host

    # Create K8s clients
    with client.ApiClient() as api_client:
        core_api = client.CoreV1Api(api_client)
        rbac_api = client.RbacAuthorizationV1Api(api_client)

    # Create the resources for the quota
    ns_name = create_constrained_ns(core_api, host, requests_cpu, requests_memory, limits_cpu, limits_memory)
    sa_name = create_constrained_sa(core_api, host, rbac_api, ns_name)

    # Retrieve the secrets created in the namespace
    secrets = core_api.list_namespaced_secret(ns_name).items
    while len(secrets) != 2:
        secrets = core_api.list_namespaced_secret(ns_name).items

    # Filter for the secret of the ServiceAccount created
    secret_name = sa_name + '-token-'
    secrets = [x for x in secrets if secret_name in x.metadata.name]

    secrets_len = len(secrets)
    if secrets_len == 0:
        raise exceptions.ServiceAccountSecretException('Missing ServiceAccount Secret for ServiceAccount %s.', sa_name)
    elif secrets_len > 1:
        raise exceptions.ServiceAccountSecretException('Too Many ServiceAccount Secret for ServiceAccount %s.', sa_name)

    # Get the ca.crt and token of the ServiceAccount created
    sa_secret_data = secrets[0].data
    sa_secret_ca_crt = sa_secret_data['ca.crt']
    sa_secret_token = b64decode(sa_secret_data['token']).decode('utf-8')

    # Build and return the kubeconfig that should be used to manage the resources in the new quota
    cluster_name = str(uuid.uuid4())
    context_name = str(uuid.uuid4())
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
            'name': context_name
        }],
        'current-context': context_name,
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
