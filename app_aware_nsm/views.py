from app_aware_nsm import app


@app.route("/")
def hello_world():
    return "<p>Dio</p>"
