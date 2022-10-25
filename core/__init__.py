from configparser import ConfigParser
from pathlib import Path
from json import loads
import logging
import psycopg2
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create loggers
quota_log = logging.getLogger('app-quota-manager')
db_log = logging.getLogger('db-manager')
nsmf_log = logging.getLogger('nsmf-manager')
vao_log = logging.getLogger('vao-manager')

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
    CREATE TABLE IF NOT EXISTS network_slice_status(
        network_slice_id UUID PRIMARY KEY,
        network_slice_status VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vertical_application_slice_status(
        vertical_application_slice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        vertical_application_slice_status VARCHAR(255) NOT NULL,
        network_slice_status UUID,
        intent JSON NOT NULL,
        nest_id VARCHAR(255),
        FOREIGN KEY (network_slice_status)
            REFERENCES network_slice_status (network_slice_id)
            ON UPDATE CASCADE ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vertical_application_quota_status(
        vertical_application_quota_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        vertical_application_quota_kubeconfig JSON NOT NULL,
        vertical_application_slice_id UUID NOT NULL,
        FOREIGN KEY (vertical_application_slice_id)
            REFERENCES vertical_application_slice_status (vertical_application_slice_id)
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

# Load nest_catalogue section from config.ini
nest_catalogue_url = None
if parser.has_section('nest_catalogue'):
    nest_catalogue_url = parser.get('nest_catalogue', 'url')
    if nest_catalogue_url is None:
        raise Exception('NEST Catalogue URL not found in nest_catalogue section of config.ini file')
else:
    raise Exception('Section nest_catalogue not found in the config.ini file')

# Load QI section from config.ini
qi = {}
if parser.has_section('qi'):
    params = parser.items('qi')
    for param in params:
        qi[param[0]] = loads(param[1])
else:
    raise Exception('Section qi not found in the config.ini file')

# Load nsmf section from config.ini
nsmf_url = None
if parser.has_section('nsmf'):
    nsmf_url = parser.get('nsmf', 'url')
    if nsmf_url is None:
        raise Exception('NSMF URL not found in nsmf section of config.ini file')
else:
    raise Exception('Section nsmf not found in the config.ini file')

# Load locations from locations.yaml config file
locations = {}
with open(Path(__file__).parent.resolve().joinpath('../locations.yaml'), 'r') as stream:
    try:
        locations = yaml.safe_load(stream)['locations']
    except yaml.YAMLError as exc:
        raise Exception(str(exc))
