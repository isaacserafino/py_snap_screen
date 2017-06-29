from datetime import date

from django.db.models import F
from dropbox import DropboxOAuth2Flow
from shortuuid import ShortUUID


# Business Model
class Snap:
    def __init__(self, filename: str, image: bytes):
        self.filename = filename
        self.image = image

class SupervisorId:
    def __init__(self, value: str):
        self.value = value

class ViewerConnection:
    def __init__(self, active: bool, authorization_token: str):
        self.active = active
        self.authorization_token = authorization_token

class SupervisorStatus:
    def __init__(self, active: bool, premium_expiration: date, supervisor_id: SupervisorId, viewer_connection: ViewerConnection):
        self.active = active
        self.premium_expiration = premium_expiration
        self.supervisor_id = supervisor_id
        self.viewer_connection = viewer_connection


# Core Services
class MonthlyLimitService:
    def __init__(self, date: date):
        self.date = date

    def retrieve_current_month(self) -> date:
        today = self.date.today()
        ': :type today: date'

        return today.replace(day=1)

    def determine_whether_current_date_before(self, expiration: date) -> bool:
        today = self.date.today()
        ': :type today: date'

        return today <= expiration


class PersistenceService:
    def __init__(self, activity_model, supervisor_model):
        self.activity_model = activity_model
        self.supervisor_model = supervisor_model

    def save_viewer_connection(self, connection: ViewerConnection, supervisor_id: SupervisorId) -> None:
        supervisor = self.supervisor_model(active=connection.active, supervisor_id=supervisor_id.value, viewer_authentication_key=connection.authorization_token)
        ': :type supervisor: Supervisor'

        supervisor.save()

    def retrieve_viewer_connection(self, supervisor_id: SupervisorId) -> ViewerConnection:
        supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)
        ': :type supervisor: Supervisor'

        return ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)

    def retrieve_supervisor_by_inbound_identity_token(self, inbound_identity_token) -> SupervisorStatus:
        supervisor = self.supervisor_model.objects.get(inbound_identity_token=inbound_identity_token)
        ': :type supervisor: Supervisor'

        supervisor_id = SupervisorId(supervisor.supervisor_id)
        viewer_connection = ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)
        return SupervisorStatus(supervisor.active, supervisor.premium_expiration, supervisor_id, viewer_connection)

    def retrieve_supervisor_status_by_supervisor_id(self, supervisor_id) -> SupervisorStatus:
        supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)
        ': :type supervisor: Supervisor'

        viewer_connection = ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)
        return SupervisorStatus(supervisor.active, supervisor.premium_expiration, supervisor_id, viewer_connection)

    def retrieve_activity_count(self, supervisor_id: SupervisorId, activity_month: date) -> int:
        try:
            activity = self.activity_model.objects.get(supervisor__supervisor_id=supervisor_id.value, activity_month=activity_month)
            ': :type activity: Activity'

            return activity.activity_count

        except self.activity_model.DoesNotExist:
            return 0

    def increment_activity_count(self, supervisor_id: SupervisorId, activity_month: date) -> None:
        activity = self.activity_model.objects.filter(supervisor__supervisor_id=supervisor_id.value, activity_month=activity_month)
        ': :type activity: QuerySet'
        
        if activity:
            activity.update(activity_count=F('activity_count') + 1)
        else:
            supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)
            ': :type supervisor: Supervisor'

            supervisor.activity_set.create(activity_month=activity_month, activity_count=1)


class SupervisorIdService:
    def __init__(self, id_generator: ShortUUID):
        self.id_generator = id_generator

    def generate(self) -> SupervisorId:
        value = self.id_generator.random(length=7)

        return SupervisorId(value)


class ViewerConnectionService:
    def __init__(self, flow):
        self.flow = flow

    def create_flow_object(self, viewer_key: str, viewer_secret: str, callback_url: str, session, csrf_token_attribute_name: str) -> DropboxOAuth2Flow:
        if self.flow is None: return None

        return self.flow(viewer_key, viewer_secret, callback_url, session, csrf_token_attribute_name)

    def start_creating_connection(self, flow_object: DropboxOAuth2Flow) -> str:
        if flow_object is None: return None

        return flow_object.start()

    def finish_creating_connection(self, callback_parameters, flow_object: DropboxOAuth2Flow) -> ViewerConnection:
        if flow_object is None: return None

        # TODO: (IMS) Handle exceptions
        result = flow_object.finish(callback_parameters)

        return ViewerConnection(True, result.access_token)


class ViewerService:
    def __init__(self, third_party):
        self.third_party = third_party

    def send_activity(self, activity: bool, connection):
        if self.third_party is None or activity is None or connection is None or connection.authorization_token is None: return

        api = self.third_party(connection.authorization_token)
        api.files_upload(activity.image, "/" + activity.filename)
