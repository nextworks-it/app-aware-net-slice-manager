import logging
from flask import Flask
from apis import api

# configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.url_map.strict_slashes = False
api.init_app(app)

if __name__ == '__main__':
    app.run()
