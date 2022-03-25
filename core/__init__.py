import logging
from kubernetes import client, config
from kubernetes.config.kube_config import ConfigException
from kubernetes.client.rest import ApiException

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

log = logging.getLogger('app-quota-manager')

try:
    # Load the kubeconfig on .kube/config
    config.load_kube_config()
except ConfigException:
    # If .kube/config is missing and the app-aware-nsm is running in a pod
    config.load_incluster_config()


# Create K8s clients
with client.ApiClient() as api_client:
    core_api = client.CoreV1Api(api_client)
    rbac_api = client.RbacAuthorizationV1Api(api_client)

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
except ApiException as e:
    if e.status == 409:
        log.info("ClusterRole already exists.")
