class AccessToken:
    def set(self, access_token, expires_in, token_type, refresh_token = "NULL"):
        self.access_token = access_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.refresh_token = refresh_token
