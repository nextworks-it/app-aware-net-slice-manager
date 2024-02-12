import requests
from core import resource_manager_url, resource_manager_log
from core.exceptions import ResourceManagerNotReadyException, NotExistingEntityException
import core.db_manager as db
import yaml

def get_clusters_from_resource_manager():
    try:
        return requests.get(f"http://{resource_manager_url}/api/v1/resource-inventory/clusters").json()
    except requests.exceptions.RequestException as e:
        resource_manager_log.error(f"Failed to get nodes from resource manager: {e}")
        raise ResourceManagerNotReadyException
    
def cluster_is_k8s(cluster) -> bool:
    if cluster.get("type", None) == "k8s":
        return True
    return False

def config_is_k8s(cluster) -> bool:
    if cluster.get("platformConfig", {}).get("type", None) == "k8s":
        return True
    return False

def get_node_list_from_cluster(cluster):
    node_list = []
    for node in cluster.get("nodes", []):
        node_name = node.get("platformNode", {}).get("k8sNode", {}).get("metadata", {}).get("name", None)
        if node_name:
            node_list.append(node_name)
        else:
            resource_manager_log.error(f"Something wrong retrieving name from node {node}")
            continue
    return node_list

def get_kubeconfig_from_cluster(cluster):
    return cluster.get("platformConfig", {}).get("config", {})

def get_current_context_from_cluster(cluster):
    return get_kubeconfig_from_cluster(cluster).get("current-context", None)

def get_nodes_from_cluster(cluster):
    return cluster.get("nodes", [])

def get_id_from_node(node):
    return node.get("id", None)

def get_name_from_node(node):
    return node.get("platformNode", {}).get("k8sNode", {}).get("metadata", {}).get("name", None)

def use_cluster_from_cluster_id(cluster_id):
    with open('/root/.kube/config', 'w') as f:
        f.write(yaml.dump(db.get_cluster_by_id(cluster_id)[3]))

def use_cluster_from_name(cluster_name):
    with open('/root/.kube/config', 'w') as f:
        f.write(yaml.dump(db.get_cluster_by_name(cluster_name)[3]))
   
def reload_config_from_resource_manager():
    resource_manager_log.debug("Reloading config from resource manager")
    cluster_list = get_clusters_from_resource_manager()
    for cluster in cluster_list:
        cluster_id = cluster.get("id", None)
        cluster_name = get_current_context_from_cluster(cluster)
        cluster_kubeconfig = get_kubeconfig_from_cluster(cluster)
        try:
            cluster_id_from_db = db.get_cluster_by_id(cluster_id)
            resource_manager_log.debug(f"   Cluster id from db {cluster_id_from_db}")
            db.update_cluster(cluster_id, dict(
                type = "KUBERNETES",
                name = cluster_name,
                kubeconfig = cluster_kubeconfig
            ))
        except NotExistingEntityException:
            resource_manager_log.debug(f"   Cluster id {cluster_id} does not exist in the db")
            db.insert_cluster(dict(
                cluster_id = cluster_id,
                type = "KUBERNETES",
                name = cluster_name,
                kubeconfig = cluster_kubeconfig
            ))
        nodes_from_db = db.get_cluster_nodes_by_cluster_id(cluster_id)
        resource_manager_log.debug(f"   Cluster Nodes by cluster id {nodes_from_db}")
        resource_manager_log.debug(f"   Cluster {cluster_id}")
        resource_manager_log.debug(f"      Nodes")
        if cluster_is_k8s(cluster) and config_is_k8s(cluster):
            nodes = get_nodes_from_cluster(cluster)
            db.delete_cluster_node_by_cluster_id(cluster_id)
            for n in nodes:
                node_id = get_id_from_node(n)
                node_name = get_name_from_node(n)
                db.insert_cluster_node(dict(
                        cluster_node_id = node_id,
                        name = node_name,
                        labels = dict(
                            project = "IANA"
                        ),
                        cluster_id = cluster_id
                    ), cluster_id)
        locations = db.get_locations_by_cluster_id(cluster_id)
        resource_manager_log.info(f"Found Locations {locations}")
        if not locations: 
            db.insert_location(dict(
                locationName = cluster_name,
                latitude = 0.0,
                longitude = 0.0,
                coverageRadius = 100,
                segment = "EDGE",
            ), cluster_id)

            


