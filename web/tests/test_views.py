from django.test import TestCase

from web.models import Activity
from web.models import SupervisorId
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.models import SupervisorIdService
from web.models import PersistenceService
from web.views import AdministrationService
from web.views import AdministrationView
from web.views import MonitoringService
from web.views import MonitoringView

# TODO: (IMS) Create your tests here.

# View Tests
class AdministrationViewTest(TestCase):
    pass


class MonitoringViewTest(TestCase):
    pass


class ViewerConnectionCallbackViewTest(TestCase):
    pass


# Business Service Tests
class AdministrationServiceTest(TestCase):
    def setUp(self):
        pass


class MonitoringServiceTest(TestCase):
    def setUp(self):
        pass
    
