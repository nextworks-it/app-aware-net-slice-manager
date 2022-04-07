from app import app, api
import os
import json

app.config["SERVER_NAME"] = "localhost"
app.app_context().__enter__()

if not os.path.exists('docs/'):
    os.makedirs('docs/')

with open('docs/swagger.json', 'w') as f:
    json.dump(api.__schema__, f, indent=2)
