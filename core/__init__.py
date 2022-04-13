from configparser import ConfigParser
from pathlib import Path
import logging
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create loggers
quota_log = logging.getLogger('app-quota-manager')
db_log = logging.getLogger('db-manager')

# Load the config.ini file
parser = ConfigParser()
parser.read(Path(__file__).parent.resolve().joinpath('../config.ini'))

# Load PostgreSQL section from config.ini
db = {}
if parser.has_section('postgresql'):
    params = parser.items('postgresql')
    for param in params:
        db[param[0]] = param[1]
else:
    raise Exception('Section postgresql not found in the config.ini file')

# Open connection to the PostgreSQL instance
db_conn = None
cur = None
try:
    db_conn = psycopg2.connect(**db)
    cur = db_conn.cursor()
except (Exception, psycopg2.DatabaseError) as error:
    db_log.error(str(error))
    exit()

db_log.info('Successfully connected to %s:%s/%s', db['host'], db['port'], db['database'])

# Initialize PostgreSQL DBs, skip table creation if exists
commands = (
    """
    CREATE TABLE IF NOT EXISTS vertical_application_quota_statuses(
        vertical_application_quota_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        vertical_application_quota_kubeconfig JSON NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS network_slice_statuses(
        network_slice_id UUID PRIMARY KEY,
        network_slice_status VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vertical_application_statuses(
        vertical_application_slice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        vertical_application_slice_status VARCHAR(255) NOT NULL,
        vertical_application_quota_status UUID,
        network_slice_status UUID,
        intent JSON NOT NULL,
        nest_id VARCHAR(255) NOT NULL,
        FOREIGN KEY (vertical_application_quota_status) 
            REFERENCES vertical_application_quota_statuses (vertical_application_quota_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (network_slice_status)
            REFERENCES network_slice_statuses (network_slice_id)
            ON UPDATE CASCADE ON DELETE CASCADE
    )
    """
)
try:
    for command in commands:
        cur.execute(command)
    cur.close()
    db_conn.commit()
except (Exception, psycopg2.DatabaseError) as error:
    db_log.error(str(error))
    exit()
