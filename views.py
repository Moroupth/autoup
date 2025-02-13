import os
import pathlib
import requests
from flask import Blueprint, render_template, abort, redirect, url_for, request, session
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

views = Blueprint(__name__, "views", static_folder="static", template_folder="templates")
request_session = requests.Session()

Google_Client_ID = "926083527735-ste8ur2scs0li21ajl5thfq8j0hcpufr.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://127.0.0.1:8000/views/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect(url_for("views.login"))  # abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@views.route("/")
def home():
    return render_template("default_scr.html")


@views.route("/uploadToYT")
def uploadToYT():
    return render_template("uploadToYT_scr.html")


@views.route("/personal")
def personal():
    return render_template("personal_scr.html")

@views.route("/home")
def mainhome():
    return render_template("home_scr.html")


@views.route("/uploadmedia")
@login_is_required
def upload():
    return render_template("uploadMedia_scr.html")


@views.route("/selectitems")
def select():
    return render_template("select_scr.html")


@views.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@views.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token= credentials._id_token,
        request=token_request,
        audience=flow.client_config.get("client_id")
    )

    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect(url_for("views.wrapper"))


@views.route("/logout")
def logout():
    session.clear()
    requests.post('https://oauth2.googleapis.com/revoke',
                  params={'token': id_token},
                  headers={'content-type': 'application/x-www-form-urlencoded'})
    return redirect(url_for("views.home"))


@views.route("/protected_area")
# @login_is_required
def protected_area():
    return render_template("main.html", name=session['name'])
