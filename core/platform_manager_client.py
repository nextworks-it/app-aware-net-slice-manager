""" DEPRECATED, USE RESOURCE MANAGER
import requests
from core import platform_manager_url, platform_manager_log
from kubernetes.config.kube_config import KubeConfigLoader
import yaml
import os
from core.exceptions import PlatformManagerNotReadyException


def get_config_from_platform_manager() -> dict:
    try:
        ret = requests.get(f"http://{platform_manager_url}/api/v1/platform-manager/platforms")
        ret_list = ret.json()
        kubeconfig_list = []
        for k in ret_list:
            try:
                if validate_kubeconfig(k['platformConfig']['config']):
                    kubeconfig_list.append(k['platformConfig']['config'])                
            except KeyError as e:
                platform_manager_log.error(f"Malformatted json from platform manager {e}")
        return kubeconfig_list
    except requests.exceptions.RequestException as e:
        platform_manager_log.error(f"Failed to get platforms from platform manager: {e}")
        raise PlatformManagerNotReadyException
    

def get_local_config() -> dict:
    if os.path.exists('.kube/config'):
        with open('.kube/config') as ff:
            local_kubeconfig = yaml.safe_load(ff.read())
            if validate_kubeconfig(local_kubeconfig):
                return local_kubeconfig
    else:
        return None
        

def merge_configs(configs) -> dict:
    if not isinstance(configs, list) or isinstance(configs, list) and len(configs) == 0:
        return {
            "apiVersion": "v1",
            "kind": "Config",
            "preferences": {},
            "current-context": "",
            "contexts": [],
            "users": [],
            "clusters": []
        }
    
    final_config = configs[0]

    # 1. Merge cluster list
    for c in configs:
        final_config['clusters'] = final_config['clusters'] + [c for c in c['clusters'] if not c in final_config['clusters']]
        final_config['users'] = final_config['users'] + [u for u in c['users'] if not u in final_config['users']]
        final_config['contexts'] = final_config['contexts'] + [c for c in c['contexts'] if not c in final_config['contexts']]
    
    return final_config

def validate_kubeconfig(kubeconfig) -> bool:
    try:
        KubeConfigLoader(config_dict = kubeconfig)
    except: 
        platform_manager_log.error(f"Malformatted kubeconfig \n \n{kubeconfig}")
        return False
    return True

def update_local_config() -> None: 
    kubeconfig_merged = merge_configs(get_config_from_platform_manager())
    platform_manager_log.info(f"Updated Local Config with {len(kubeconfig_merged['clusters'])} clusters, {len(kubeconfig_merged['users'])} users and {len(kubeconfig_merged['contexts'])} contexts")
    with open('/root/.kube/config', 'w') as f:
        f.write(yaml.dump(kubeconfig_merged))

"""