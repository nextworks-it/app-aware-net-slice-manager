import logging
from flask import Flask
from apis import api
from core.resource_manager_client import reload_config_from_resource_manager
from core.exceptions import  ResourceManagerNotReadyException
import time

# configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.url_map.strict_slashes = False
api.init_app(app)

while True:
    try:
        reload_config_from_resource_manager()
        break
    except ResourceManagerNotReadyException:
        logging.getLogger('main').info('Resource Manager Not ready, waiting 10s')
        time.sleep(10)

if __name__ == '__main__':
    app.run()
