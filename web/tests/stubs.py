from datetime import date

from django.contrib.auth.models import User

from web.models import Snap, PremiumEditionStatus, StandardEditionStatus, Dashboard
from web.models import SupervisorId
from web.models import SupervisorStatus
from web.models import ViewerConnection


ACTIVITY_COUNT = 500
INCREMENTED_ACTIVITY_COUNT = 501

AUTHORIZATION_URL = 'https://www.example.com/stub_authorization_url'
CALLBACK_URL = 'https://www.example.com/stub_callback_url'

ACTIVE = True
AUTHORIZATION_TOKEN = 'stub_authorization_token'
CONNECTION = ViewerConnection(ACTIVE, AUTHORIZATION_TOKEN)

CONTENTS = b'stub_contents'
FILENAME = 'next_123456.jpg'
CORE_FILENAME = '/next_123456.jpg'
ACTIVITY = Snap(FILENAME, CONTENTS)

CSRF_TOKEN_ATTRIBUTE_NAME = 'dropbox-auth-csrf-token'
KEY = 'stub key'
QUERY_PARAMS = {}
SECRET = 'stub secret'
SESSION = {}

INBOUND_IDENTITY_TOKEN = 'johndoe'
FRAMEWORK_USER_FUNCTION = lambda: User.objects.get_or_create(username=INBOUND_IDENTITY_TOKEN)[0]

MONTH = date(2012, 12, 1)
PREMIUM_EDITION_EXPIRATION_DATE = date(2012, 12, 31)
TODAY = date(2012, 12, 30)

PREMIUM_EDITON_STATUS = PremiumEditionStatus(MONTH, False)
STANDARD_EDITION_STATUS = StandardEditionStatus(ACTIVITY_COUNT, True)

SUPERVISOR_ID_VALUE = '3oe2UAP'
SUPERVISOR_ID = SupervisorId(SUPERVISOR_ID_VALUE)

SUPERVISOR = SupervisorStatus(ACTIVE, PREMIUM_EDITION_EXPIRATION_DATE, SUPERVISOR_ID, CONNECTION)

DASHBOARD = Dashboard(False, PREMIUM_EDITION_EXPIRATION_DATE, STANDARD_EDITION_STATUS, SUPERVISOR_ID)

PAYMENT_FORM = "<form></form>"
