from kubernetes import client
from core import core_api, rbac_api
import uuid


def create_constrained_ns(requests_cpu: str, requests_memory: str, limits_cpu: str, limits_memory: str) -> str:
    # Create a namespace with random uuid as name
    ns_name = str(uuid.uuid4())
    ns = client.V1Namespace(metadata=client.V1ObjectMeta(name=ns_name))
    core_api.create_namespace(ns)

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

    return ns_name


def create_constrained_sa(ns_name: str):
    # Create a ServiceAccount with random uuid as name
    sa_name = str(uuid.uuid4())
    sa = client.V1ServiceAccount(metadata=client.V1ObjectMeta(name=sa_name))
    core_api.create_namespaced_service_account(ns_name, sa)

    # Bind the created ServiceAccount to the ClusterRole to limit the access to the given namespace
    rb = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=sa_name + 'role-binding'),
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

    return sa_name
