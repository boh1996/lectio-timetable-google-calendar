# Database password
db_password = ""
# Database uername
db_user     = ""
# Database host, 127.0.0.1 etc
db_host = ""
# Schema name
db_database = ""
# Database system string, mysql+mysqldb etc
database = "mysql+mysqldb"

# Authentication redirect URL
redirect_uri    = ""
# Google Client ID
client_id       = ""
# Google Client Secret
client_secret   = ""
# Google Access token type
access_type     = "offline"
# Google OAuth flow
approval_promt  = "force"
# Google OAuth Scopes
scopes          = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]
# Google Access token request type
response_type   = "code"
# Authentication base url
base_url        = ""

# The number of weeks to run
numberOfWeeks = 4

# Google Endpoint URLs
google_auth_endpoint   = "https://accounts.google.com/o/oauth2/auth"
google_token_endpoint   = "https://accounts.google.com/o/oauth2/token"
google_revoke_endpont   = "https://accounts.google.com/o/oauth2/revoke"
google_validate_url     = "https://www.googleapis.com/oauth2/v1/tokeninfo"
google_user_info_url    = "https://www.googleapis.com/oauth2/v3/userinfo"