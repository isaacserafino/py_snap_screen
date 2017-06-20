from web.models import Snap
from web.models import ViewerConnection
from web.models import SupervisorId
from web.models import SupervisorStatus
from datetime import date

ACTIVITY_COUNT = 500

AUTHORIZATION_URL = "https://www.example.com/stub_authorization_url"
CALLBACK_URL = "https://www.example.com/stub_callback_url"

ACTIVE = True
AUTHORIZATION_TOKEN = "stub_authorization_token"
CONNECTION = ViewerConnection(ACTIVE, AUTHORIZATION_TOKEN)

CONTENTS = b'stub_contents'
FILENAME = "stub_filename.txt"
CORE_FILENAME = "/stub_filename.txt"
ACTIVITY = Snap(FILENAME, CONTENTS)

CSRF_TOKEN_ATTRIBUTE_NAME = "dropbox-auth-csrf-token"
KEY = "stub key"
QUERY_PARAMS = {}
SECRET = "stub secret"
SESSION = {}

INBOUND_IDENTITY_TOKEN = "johndoe"

MONTH = date(2012, 12, 1)
PREMIUM_EDITION_EXPIRATION_DATE = date(2012, 12, 31)
TODAY = date(2012, 12, 30)

SUPERVISOR_ID_VALUE = "3oe2UAP"
SUPERVISOR_ID = SupervisorId(SUPERVISOR_ID_VALUE)

SUPERVISOR = SupervisorStatus(ACTIVE, PREMIUM_EDITION_EXPIRATION_DATE, SUPERVISOR_ID, CONNECTION)