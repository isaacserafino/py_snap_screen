# Developer instructions: Complete the information in this file locally, rename it to "settings_local.py", and *do not
# commit* it to version control.

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
# DEBUG = True

ALLOWED_HOSTS = [u'isaacserafino.pythonanywhere.com']
# ALLOWED_HOSTS = [u'127.0.0.1']

MEDIA_ROOT = u'/home/isaacserafino/py_snap_screen/media'
STATIC_ROOT = u'/home/isaacserafino/py_snap_screen/static'

DROPBOX_CALLBACK_URL = "https://isaacserafino.pythonanywhere.com/viewer-connection-callback/"
# DROPBOX_CALLBACK_URL = "http://127.0.0.1:8000/viewer-connection-callback/"

PAYPAL_PROFILE = {
    "business": "i@findmercy.com",
    "amount": "5.00",

    "a3": "5.00",                      # monthly price
    "p3": 1,                           # duration of each unit (depends on unit)
    "t3": "M",                         # duration unit ("M for Month")
    "src": "1",                        # make payments recur
    "sra": "1",                        # reattempt payment on payment error

    "item_name": "Snap Screen Premium Edition Monthly Subscription",
    # TODO: (IMS) Placeholder:
    "invoice": "unique-invoice-id",

    # Note: This is completed within code once available:
    "notify_url": "https://isaacserafino.pythonanywhere.com",

    "return_url": "https://isaacserafino.pythonanywhere.com/supervisor/",
    "cancel_return": "https://isaacserafino.pythonanywhere.com/supervisor/",
}

PAYPAL_TEST = True

CSRF_COOKIE_SECURE = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 60
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

# If you are a Snap Screen developer, please request these tokens from your administrator. If you are adapting code for
# use in your own project, you will need to obtain your own tokens.

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

DROPBOX_API_KEY = ''
DROPBOX_API_SECRET = ''
TEST_AUTHORIZATION_TOKEN = ''

SOCIAL_AUTH_DROPBOX_OAUTH2_KEY = ''
SOCIAL_AUTH_DROPBOX_OAUTH2_SECRET = ''
