from core import db_conn, db_log
from psycopg2 import DatabaseError
from core.exceptions import DBException, NotExistingEntityException
import json


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
