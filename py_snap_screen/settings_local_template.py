# Developer instructions: Complete the information in this file locally, rename it to "settings_local.py", and *do
# not commit* it to version control. 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
#DEBUG = True

ALLOWED_HOSTS = [u'isaacserafino.pythonanywhere.com']
#ALLOWED_HOSTS = [u'127.0.0.1']

DROPBOX_CALLBACK_URL = "https://isaacserafino.pythonanywhere.com/viewer-connection-callback/"
#DROPBOX_CALLBACK_URL = "http://127.0.0.1:8000/viewer-connection-callback/"

# If you are a Snap Screen developer, please request these tokens from your administrator. If you are adapting code for
# use in your own project, you will need to obtain your own tokens. 

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

DROPBOX_API_KEY = ''
DROPBOX_API_SECRET = ''
TEST_AUTHORIZATION_TOKEN = ''

SOCIAL_AUTH_DROPBOX_OAUTH2_KEY = ''
SOCIAL_AUTH_DROPBOX_OAUTH2_SECRET = ''
