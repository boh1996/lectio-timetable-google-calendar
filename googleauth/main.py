from flask import Flask
from flask import redirect
from flask import request
import config
import google_oauth
from flask.ext.sqlalchemy import SQLAlchemy

__author__ = "Bo Thomsen"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://lectio:'+config.db_password+'@127.0.0.1/lectio'
db = SQLAlchemy(app)

GoogleOAuth = google_oauth.GoogleOAuth()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True)
    refresh_token = db.Column(db.String(255))

    def __init__(self, user_id, refresh_token):
        self.user_id = user_id
        self.refresh_token = refresh_token

    def __repr__(self):
        return '<User %r>' % self.id

class AccessToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=False)
    access_token = db.Column(db.String(80), unique=True)
    expires_in = db.Column(db.String(45))

    def __init__(self, user_id, access_token, expires_in):
        self.access_token = access_token
        self.user_id = user_id
        self.expires_in = expires_in

    def __repr__(self):
        return '<AccessToken %r>' % self.id

db.create_all()

@app.route("/")
def index():
    db.create_all()
    db.session.commit()
    return "Sorry!"

@app.route('/auth', methods=['GET'])
def auth():
    return redirect(GoogleOAuth.auth(callback="/callback",state="auth"))

@app.route("/callback")
def callback():

    if request.args.get("error") != False :
        data = GoogleOAuth.callback(code=request.args.get("code"))
        if data != False:
            userdata = GoogleOAuth.userinfo(data.access_token)
            if userdata != False:
                if data.refresh_token != "NULL":
                    db.session.add(User(userdata.id, data.refresh_token))
                    db.session.commit()
                    db.session.add(AccessToken(userdata.id, data.access_token))
                    db.session.commit()
                    return "Success:"
                else:
                    db.session.add(AccessToken(userdata.id, data.access_token, data.expires_in))
                    db.session.commit()
                    return "Success:"
            else:
                redirect(config.base_url)
        else:
            redirect(config.base_url)
    else:
        redirect(config.base_url)

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )