from web.models import Activity
from web.models import ViewerConnection
from web.models import SupervisorId

AUTHORIZATION_URL = "https://www.example.com/stub_authorization_url"
CALLBACK_URL = "https://www.example.com/stub_callback_url"

ACTIVE = True
AUTHORIZATION_TOKEN = "stub_authorization_token"
CONNECTION = ViewerConnection(ACTIVE, AUTHORIZATION_TOKEN)

CONTENTS = b'stub_contents'
FILENAME = "stub_filename.txt"
CORE_FILENAME = "/stub_filename.txt"
ACTIVITY = Activity(FILENAME, CONTENTS)

CSRF_TOKEN_ATTRIBUTE_NAME = "dropbox-auth-csrf-token"
KEY = "stub key"
QUERY_PARAMS = {}
SECRET = "stub secret"
SESSION = {}

SUPERVISOR_ID_VALUE = "3oe2UAP"
SUPERVISOR_ID = SupervisorId(SUPERVISOR_ID_VALUE)