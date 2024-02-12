from core import db_conn, db_log
from psycopg2 import DatabaseError
from core.exceptions import DBException, NotExistingEntityException
import json
import uuid

##################################################
# vertical_application_quota_status
##################################################
def insert_va_quota_status(kubeconfig, vertical_application_slice_id: str):
    # Create a new entry <uuid, kubeconfig> in the DB for a vertical application quota
    command = """
    INSERT INTO vertical_application_quota_status(vertical_application_quota_kubeconfig, 
    vertical_application_slice_id) VALUES (%s, %s) RETURNING vertical_application_quota_id
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (json.dumps(kubeconfig), vertical_application_slice_id))
        va_quota_id = cur.fetchone()[0]
        cur.close()
        db_conn.commit()

        db_log.info('Created new va_quota_status with ID %s', va_quota_id)

        return va_quota_id
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating vertical_application_quota_status: ' + str(error))


def get_va_quota_status():
    # Retrieve all va_quota_status entries from the DB
    command = """SELECT * FROM vertical_application_quota_status"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        va_quota_status = cur.fetchall()
        cur.close()

        return va_quota_status
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_quota_status: ' + str(error))


def get_va_quota_status_by_id(vertical_application_quota_id: str):
    # Retrieve va_quota_status entry by vertical_application_quota_id (PRIMARY KEY)
    command = """SELECT * FROM vertical_application_quota_status WHERE vertical_application_quota_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_quota_id,))
        va_quota_status = cur.fetchone()
        cur.close()

        if va_quota_status is None:
            raise NotExistingEntityException('va_quota_status with ID ' +
                                             vertical_application_quota_id + ' not found.')

        return va_quota_status
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_quota_status: ' + str(error))


def get_va_quota_status_by_vas_id(vertical_application_slice_id: str):
    # Retrieve all va_quota_status linked to the given vertical_application_slice_id
    command = """SELECT * FROM vertical_application_quota_status WHERE vertical_application_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_id, ))
        va_quota_status = cur.fetchall()
        cur.close()

        return va_quota_status
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_quota_status: ' + str(error))


def delete_va_quota_by_vas_id(vertical_application_slice_id: str):
    # Delete all va_quota_status linked to the given vertical_application_slice_id
    command = """DELETE FROM vertical_application_quota_status WHERE vertical_application_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed vertical_application_quota_status for vertical_application_slice_id %s',
                    vertical_application_slice_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while removing vertical_application_quota_status: ' + str(error))


##################################################
# network_slice_status
##################################################
def insert_network_slice_status(network_slice_id: str, network_slice_status: str):
    # Create a new entry <network_slice_id, network_slice_status> in the DB for a network slice
    command = """INSERT INTO network_slice_status(network_slice_id, network_slice_status) VALUES (%s, %s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (network_slice_id, network_slice_status))
        cur.close()
        db_conn.commit()

        db_log.info('Created new network_slice_status with ID %s', network_slice_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating network_slice_status: ' + str(error))


def update_network_slice_status(network_slice_id: str, network_slice_status: str):
    # Update a network_slice_status status
    command = """UPDATE network_slice_status SET network_slice_status = %s WHERE network_slice_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (network_slice_status, network_slice_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated network_slice_status %s with status %s', network_slice_id, network_slice_status)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating network_slice_status: ' + str(error))


def get_network_slice_status():
    # Retrieve all network_slice_status entries from the DB
    command = """SELECT * FROM network_slice_status"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        network_slice_status = cur.fetchall()
        cur.close()

        return network_slice_status
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching network_slice_status: ' + str(error))


def get_network_slice_status_by_id(network_slice_id: str):
    # Retrieve network_slice_status entry by network_slice_id (PRIMARY KEY)
    command = """SELECT * FROM network_slice_status WHERE network_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (network_slice_id,))
        network_slice_status = cur.fetchone()
        cur.close()

        if network_slice_status is None:
            raise NotExistingEntityException('network_slice_status with ID ' + network_slice_id + ' not found.')

        return network_slice_status
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching network_slice_status: ' + str(error))


def delete_network_slice_status_by_id(network_slice_id: str):
    # Delete network_slice_status entry by network_slice_id (PRIMARY KEY)
    command = """DELETE FROM network_slice_status WHERE network_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (network_slice_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed network_slice_status %s', network_slice_id)
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while removing network_slice_status: ' + str(error))

##################################################
# vertical_application_slice_status
##################################################
def insert_va_status(vertical_application_slice_status: str, intent):
    # Create a new entry <uuid, vertical_application_slice_status, intent> in the DB for a vertical application status
    command = """
    INSERT INTO vertical_application_slice_status(vertical_application_slice_status, intent) 
    VALUES (%s, %s) RETURNING vertical_application_slice_id
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_status, json.dumps(intent)))
        va_status_id = cur.fetchone()[0]
        cur.close()
        db_conn.commit()

        db_log.info('Created new va_status with ID %s', va_status_id)

        return va_status_id
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating vertical_application_slice_status: ' + str(error))


def execute_va_status_update(command: str, vertical_application_slice_id: str, update: str):
    try:
        cur = db_conn.cursor()
        cur.execute(command, (update, vertical_application_slice_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated va_status %s', vertical_application_slice_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating vertical_application_slice_status: ' + str(error))


def update_va_with_status(vertical_application_slice_id: str, vertical_application_slice_status: str):
    # Update the status of a va_status entry by ID
    command = """
    UPDATE vertical_application_slice_status SET vertical_application_slice_status = %s 
    WHERE vertical_application_slice_id = %s
    """
    execute_va_status_update(command, vertical_application_slice_id, vertical_application_slice_status)


def update_va_status_with_ns(vertical_application_slice_id: str, network_slice_status: str):
    # Update the network_slice_status of a va_status entry by ID
    command = """
    UPDATE vertical_application_slice_status SET network_slice_status = %s 
    WHERE vertical_application_slice_id = %s
    """
    execute_va_status_update(command, vertical_application_slice_id, network_slice_status)


def update_va_status_with_nest_id(vertical_application_slice_id: str, nest_id: str):
    # Update the nest_id of a va_status entry by ID
    command = """UPDATE vertical_application_slice_status SET nest_id = %s WHERE vertical_application_slice_id = %s"""
    execute_va_status_update(command, vertical_application_slice_id, nest_id)


def update_va_with_status_by_network_slice(network_slice_id: str, vertical_application_slice_status: str):
    # Update vertical application entry status by network_slice_id (FOREIGN KEY)
    command = """
    UPDATE vertical_application_slice_status SET vertical_application_slice_status = %s 
    WHERE network_slice_status = %s
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_status, network_slice_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated va_status with network_slice_status %s', network_slice_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating vertical_application_slice_status: ' + str(error))


def get_va_status():
    # Retrieve all va_status entries from the DB
    command = """SELECT * FROM vertical_application_slice_status"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        va_status = cur.fetchall()
        cur.close()

        return va_status
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_slice_status: ' + str(error))


def get_va_status_by_id(vertical_application_slice_id: str):
    # Retrieve va_status entry by vertical_application_slice_id (PRIMARY KEY)
    command = """SELECT * FROM vertical_application_slice_status WHERE vertical_application_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_id,))
        va_status = cur.fetchone()
        cur.close()

        if va_status is None:
            raise NotExistingEntityException('va_status with ID ' + vertical_application_slice_id + ' not found.')

        return va_status
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_slice_status: ' + str(error))


def get_va_status_by_network_slice(network_slice_id: str):
    # Retrieve va_status entry by network slice id
    command = """SELECT * FROM vertical_application_slice_status WHERE network_slice_status = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (network_slice_id,))
        va_status = cur.fetchone()
        cur.close()

        if va_status is None:
            raise NotExistingEntityException('va_status with network slice ID ' + network_slice_id + ' not found.')

        return va_status
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching vertical_application_slice_status: ' + str(error))


def delete_va_status_by_id(vertical_application_slice_id: str):
    # Delete va_status entry by vertical_application_slice_id (PRIMARY KEY)
    command = """DELETE FROM vertical_application_slice_status WHERE vertical_application_slice_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (vertical_application_slice_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed vertical_application_slice_status %s', vertical_application_slice_id)
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while removing vertical_application_slice_status: ' + str(error))

##################################################
# cluster_nodes
##################################################
def insert_cluster_node(cluster_node: dict, cluster_id: str):
    # Create a new entry <uuid, name, labels, cluster_id> in the DB
    command = """
    INSERT INTO cluster_nodes(cluster_node_id, name, labels, cluster_id)
    VALUES (%s, %s, %s, %s) RETURNING cluster_node_id
    """
    if not 'cluster_node_id' in cluster_node:
        cluster_node['cluster_node_id'] = str(uuid.uuid4())
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_node['cluster_node_id'], cluster_node['name'], json.dumps(cluster_node['labels']), cluster_id))
        cluster_node_id = cur.fetchone()[0]
        cur.close()
        db_conn.commit()

        db_log.info('Created new cluster_node with ID %s', cluster_node_id)

        return cluster_node_id
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating cluster_node: ' + str(error))


def get_cluster_nodes():
    # Retrieve all the cluster_nodes entries from the DB
    command = """SELECT * FROM cluster_nodes"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        cluster_nodes = cur.fetchall()
        cur.close()

        return cluster_nodes
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching cluster_nodes: ' + str(error))


def get_cluster_nodes_by_cluster_id(cluster_id: str):
    # Retrieve all cluster_nodes linked to the given cluster_id
    command = """SELECT * FROM cluster_nodes WHERE cluster_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_id,))
        cluster_nodes = cur.fetchall()
        cur.close()

        return cluster_nodes
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching cluster_nodes: ' + str(error))


def update_cluster_node(cluster_node_id: str, cluster_node: dict):
    # Update a cluster_node entry in the DB
    command = """UPDATE cluster_nodes SET name = %s, labels = %s WHERE cluster_node_id = %s
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_node['name'], json.dumps(cluster_node['labels']), cluster_node_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated cluster_node %s', cluster_node_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating cluster_node: ' + cluster_node_id)


def delete_cluster_node(cluster_node_id: str):
    # Delete cluster_node by cluster_node_id
    command = """DELETE FROM cluster_nodes WHERE cluster_node_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_node_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed cluster_node %s', cluster_node_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while removing cluster_node %s: ' + cluster_node_id)


def delete_cluster_node_by_cluster_id(cluster_id: str):
    # Delete cluster_node by cluster_id
    command = """DELETE FROM cluster_nodes WHERE cluster_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed cluster_nodes for cluster_id %s', cluster_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while removing cluster_nodes for cluster_id %s: ' + cluster_id)

##################################################
# clusters
##################################################
def insert_cluster(cluster: dict):
    # Create a new entry <uuid, name, type> in the DB
    command = """
    INSERT INTO clusters(cluster_id, name, type, kubeconfig) VALUES (%s, %s, %s, %s) RETURNING cluster_id
    """
    if not 'cluster_id' in cluster:
        cluster['cluster_id'] = str(uuid.uuid4())
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster['cluster_id'], cluster['name'], cluster['type'], json.dumps(cluster['kubeconfig'])))
        cluster_id = cur.fetchone()[0]
        cur.close()
        db_conn.commit()

        db_log.info('Created new cluster with ID %s', cluster_id)

        return cluster_id
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating cluster: ' + str(error))


def get_clusters():
    # Retrieve all the cluster entries from the DB
    command = """SELECT * FROM clusters"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        clusters = cur.fetchall()
        cur.close()

        return clusters
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching clusters: ' + str(error))


def get_cluster_by_id(cluster_id: str):
    # Retrieve cluster entry by cluster_id (PRIMARY KEY)
    command = """SELECT * FROM clusters WHERE cluster_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_id,))
        cluster = cur.fetchone()
        cur.close()

        if cluster is None:
            raise NotExistingEntityException('cluster with ID ' + cluster_id + ' not found.')

        return cluster
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching cluster: ' + str(error))
    
def get_cluster_by_name(cluster_name: str):
    # Retrieve cluster entry by cluster_id (PRIMARY KEY)
    command = """SELECT * FROM clusters WHERE name = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_name,))
        cluster = cur.fetchone()
        cur.close()

        if cluster is None:
            raise NotExistingEntityException('cluster with NAME ' + cluster_name + ' not found.')

        return cluster
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching cluster: ' + str(error))


def update_cluster(cluster_id: str, cluster: dict):
    # Update a cluster entry in the DB
    command = """UPDATE clusters SET name = %s, type = %s, kubeconfig = %s WHERE cluster_id = %s
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster['name'], cluster['type'], json.dumps(cluster['kubeconfig']), cluster_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated cluster %s', cluster_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating cluster: ' + cluster_id)


def delete_cluster(cluster_id: str):
    # Delete cluster by cluster_id
    command = """DELETE FROM clusters WHERE cluster_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed cluster %s', cluster_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while removing cluster %s: ' + cluster_id)

##################################################
# locations
##################################################
def insert_location(location: dict, cluster_id: str):
    # Create a new entry <uuid, location_name, cluster_id, latitude, longitude, coverage_radius, segment> in the DB
    command = """
    INSERT INTO locations(location_name, cluster_id, latitude, longitude, coverage_radius, segment)
    VALUES (%s, %s, %s, %s, %s, %s) RETURNING geographical_area_id
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (location['locationName'], cluster_id,
                              location['latitude'], location['longitude'],
                              location['coverageRadius'], location['segment']))
        geographical_area_id = cur.fetchone()[0]
        cur.close()
        db_conn.commit()

        db_log.info('Created new location with ID %s', geographical_area_id)

        return geographical_area_id
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while creating location: ' + str(error))


def get_locations():
    # Retrieve all the location entries from the DB
    command = """SELECT * FROM locations"""
    try:
        cur = db_conn.cursor()
        cur.execute(command)
        locations = cur.fetchall()
        cur.close()

        return locations
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while fetching locations: ' + str(error))


def get_location_by_id(geographical_area_id: str):
    # Retrieve location entry by geographical_area_id (PRIMARY KEY)
    command = """SELECT * FROM locations WHERE geographical_area_id = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (geographical_area_id,))
        location = cur.fetchone()
        cur.close()

        if location is None:
            raise NotExistingEntityException('location with ID ' + geographical_area_id + ' not found.')

        return location
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching location: ' + str(error))

def get_location_by_name(location_name: str):
    # Retrieve location entry by location_name 
    command = """SELECT * FROM locations WHERE location_name = (%s)"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (location_name,))
        location = cur.fetchone()
        cur.close()

        if location is None:
            raise NotExistingEntityException('location with name ' + location_name + ' not found.')

        return location
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching location: ' + str(error))


def update_location(geographical_area_id: str, location: dict):
    # Update a location entry in the DB
    command = """UPDATE locations SET location_name = %s, latitude = %s, longitude = %s,
    coverage_radius = %s, segment = %s WHERE geographical_area_id = %s
    """
    try:
        cur = db_conn.cursor()
        cur.execute(command, (location['locationName'], location['latitude'],
                              location['longitude'], location['coverageRadius'],
                              location['segment'], geographical_area_id))
        cur.close()
        db_conn.commit()

        db_log.info('Updated location %s', geographical_area_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while updating location: ' + geographical_area_id)


def delete_location(geographical_area_id: str):
    # Delete location by geographical_area_id
    command = """DELETE FROM locations WHERE geographical_area_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (geographical_area_id,))
        cur.close()
        db_conn.commit()

        db_log.info('Removed location geographical_area_id %s', geographical_area_id)
    except (Exception, DatabaseError) as error:
        db_log.error(str(error))
        raise DBException('Error while removing location %s: ' + geographical_area_id)

def get_locations_by_cluster_id(cluster_id: str):
    # Retrieve all locations linked to the given cluster_id
    command = """SELECT * FROM locations WHERE cluster_id = %s"""
    try:
        cur = db_conn.cursor()
        cur.execute(command, (cluster_id,))
        locations = cur.fetchall()
        cur.close()

        return locations
    except DatabaseError as error:
        db_log.error(str(error))
        raise DBException('Error while fetching locations: ' + str(error))