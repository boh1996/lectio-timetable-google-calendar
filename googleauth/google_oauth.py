import config
import urllib
import json
import access_token
import user

def object_decoder(obj):
    Token = access_token.AccessToken()
    if "refresh_token" in obj:
        Token.set(obj["access_token"], obj['expires_in'],obj["token_type"],obj["refresh_token"])
        return Token
    else:
        Token.set(obj["access_token"], obj['expires_in'],obj["token_type"])
        return Token

def user_object_decoder(obj):
        User = user.GoogleUser()
        User.set(obj["sub"])
        return User

class GoogleOAuth:

    def auth (self,callback = "/callback", state = "auth"):
        url = config.google_auth_endpoint + "?"
        url += "scope=" + ' '.join(config.scopes) + "&"
        url += "access_type=" + config.access_type + "&"
        url += "client_id=" + config.client_id + "&"
        url += "approval_promt=" + config.approval_promt + "&"
        url += "response_type=" + config.response_type + "&"
        url += "redirect_uri=" + config.redirect_uri + callback + "&"
        url += "state=" + state

        return url

    def callback (self,code, callback = "/callback"):
        params = urllib.urlencode({
            "code" : code,
            "client_id" : config.client_id,
            "client_secret" : config.client_secret,
            "redirect_uri" : config.redirect_uri + callback,
            "grant_type" : "authorization_code"
        })

        f = urllib.urlopen(config.google_token_endpoint, params)
        response = f.read()

        object = json.loads(response, object_hook=object_decoder)
        if object != "" and hasattr(object,"error") == False:
            return object
        else:
            return False

    def refresh (self,refresh_token):
        params = urllib.urlencode({
            "refresh_token" : refresh_token,
            "client_id" : config.client_id,
            "client_secret" : config.client_secret,
            "grant_type" : "refresh_token"
        })

        f = urllib.urlopen(config.google_token_endpoint, params)
        response = f.read()
        object = json.loads(response, object_hook=object_decoder)
        if object != "" and hasattr(object,"error") == False:
            return object
        else:
            return False

    def revoke (self,refresh_token):
        f = urllib.urlopen(config.google_revoke_endpont + "?token=" + refresh_token)
        f.read()

    def validate (self,token):
        f = urllib.urlopen(config.google_validate_url + "?id_token=" + token)
        f.read()

    def userinfo (self,access_token):
        f = urllib.urlopen(config.google_user_info_url + "?access_token=" + access_token)
        response = f.read()

        object = json.loads(response, object_hook=user_object_decoder)

        return object
