import logging
from flask import Flask
from apis import api
from core.platform_manager_client import update_local_config
from core.exceptions import PlatformManagerNotReadyException
import time

# configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.url_map.strict_slashes = False
api.init_app(app)

while True:
    try:
        update_local_config()
        break
    except PlatformManagerNotReadyException:
        logging.getLogger('main').info('Platform Manager Not ready, waiting 10s')
        time.sleep(10)

if __name__ == '__main__':
    app.run()
