from abc import ABC, abstractmethod
from datetime import date

from django.db.models import F
from dropbox import DropboxOAuth2Flow
from shortuuid import ShortUUID


# Business Model
class SupervisorId:
    def __init__(self, value: str):
        self.value = value

class PaymentNotification(ABC):
    @abstractmethod
    def get_supervisor_id(self) -> SupervisorId:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass

class PaymentProfile(ABC):
    @abstractmethod
    def retrieve_form(self, supervisor_id: SupervisorId) -> str:
        pass

class Snap:
    def __init__(self, filename: str, image: bytes):
        self.filename = filename
        self.image = image

class ViewerConnection:
    def __init__(self, active: bool, authorization_token: str):
        self.active = active
        self.authorization_token = authorization_token

class SupervisorStatus:
    def __init__(self, active: bool, premium_expiration: date, supervisor_id: SupervisorId,
                 viewer_connection: ViewerConnection):

        self.active = active
        self.premium_expiration = premium_expiration
        self.supervisor_id = supervisor_id
        self.viewer_connection = viewer_connection

class InboundIdentityToken(ABC):
    @abstractmethod
    def create_supervisor(self, supervisor_model, supervisor_id: SupervisorId) -> None:
        pass

    @abstractmethod
    def retrieve_supervisor_status(self) -> SupervisorStatus:
        pass

    @abstractmethod
    def save_supervisor(self) -> None:
        pass

    @abstractmethod
    def update_viewer_connection(self, viewer_connection: ViewerConnection) -> None:
        pass

class PremiumEditionStatus:
    def __init__(self, activity_month: date, premium_edition_active: bool):
        self.activity_month = activity_month
        self.premium_edition_active = premium_edition_active

class StandardEditionStatus:
    def __init__(self, activity_count: int, activity_within_standard_edition_limit: bool):
        self.activity_count = activity_count
        self.activity_within_standard_edition_limit = activity_within_standard_edition_limit

class Dashboard:
    def __init__(self, premium_edition_active: bool, premium_edition_expiration: date,
                standard_edition_status: StandardEditionStatus, supervisor_id: SupervisorId):

        self.premium_edition_active = premium_edition_active
        self.premium_edition_expiration = premium_edition_expiration
        self.standard_edition_status = standard_edition_status
        self.supervisor_id = supervisor_id


# Core Services
class MonthlyLimitService:
    LIMIT = 1000

    def __init__(self, date: date):
        self.date = date

    def retrieve_premium_edition_status(self, supervisor_status: SupervisorStatus) -> PremiumEditionStatus:
        today = self.date.today()
        ': :type today: date'

        activity_month = today.replace(day=1)
        expiration = supervisor_status.premium_expiration
        
        premium_edition_active = (expiration is not None and today <= expiration)

        return PremiumEditionStatus(activity_month, premium_edition_active)

    def retrieve_standard_edition_status(self, activity_count: int) -> StandardEditionStatus:
        activity_within_standard_edition_limit = activity_count < self.LIMIT

        return StandardEditionStatus(activity_count, activity_within_standard_edition_limit)


class PersistenceService:
    def __init__(self, activity_model, supervisor_model):
        self.activity_model = activity_model
        self.supervisor_model = supervisor_model

    def save_viewer_connection(self, connection: ViewerConnection, supervisor_id: SupervisorId) -> None:
        supervisor = self.supervisor_model(active=connection.active, supervisor_id=supervisor_id.value,
                                           viewer_authentication_key=connection.authorization_token)
        ': :type supervisor: Supervisor'

        supervisor.save()

    # TODO: (IMS) Test, rename identifiers in these 3 methods:
    def create_supervisor(self, framework_user: InboundIdentityToken, supervisor_id: SupervisorId) -> None:
        framework_user.create_supervisor(self.supervisor_model, supervisor_id)

    def save_supervisor(self, framework_user: InboundIdentityToken) -> None:
        framework_user.save_supervisor()

    def update_connection(self, framework_user: InboundIdentityToken, viewer_authentication_key: ViewerConnection
                ) -> None:
        framework_user.update_viewer_connection(viewer_authentication_key)

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

    def retrieve_supervisor_status_by_supervisor_id(self, supervisor_id: SupervisorId) -> SupervisorStatus:
        supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)
        ': :type supervisor: Supervisor'

        viewer_connection = ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)
        return SupervisorStatus(supervisor.active, supervisor.premium_expiration, supervisor_id, viewer_connection)

    def retrieve_activity_count(self, supervisor_id: SupervisorId, activity_month: date) -> int:
        try:
            activity = self.activity_model.objects.get(supervisor__supervisor_id=supervisor_id.value,
                                                       activity_month=activity_month)
            ': :type activity: Activity'

            return activity.activity_count

        except self.activity_model.DoesNotExist:
            return 0

    def increment_activity_count(self, supervisor_id: SupervisorId, activity_month: date) -> None:
        activity = self.activity_model.objects.filter(supervisor__supervisor_id=supervisor_id.value,
                                                      activity_month=activity_month)
        ': :type activity: QuerySet'
        
        if activity:
            activity.update(activity_count=F('activity_count') + 1)
        else:
            supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)
            ': :type supervisor: Supervisor'

            supervisor.activity_set.create(activity_month=activity_month, activity_count=1)

    # TODO: Implement
    def update_premium_expiration(self, supervisor_id: SupervisorId, premium_expiration: date) -> None:
        pass


class SupervisorIdService:
    def __init__(self, id_generator: ShortUUID):
        self.id_generator = id_generator

    def generate(self) -> SupervisorId:
        value = self.id_generator.random(length=7)

        return SupervisorId(value)


class ViewerConnectionService:
    def __init__(self, flow):
        self.flow = flow

    def create_flow_object(self, viewer_key: str, viewer_secret: str, callback_url: str, session,
                           csrf_token_attribute_name: str) -> DropboxOAuth2Flow:
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
        if (self.third_party is None or activity is None or connection is None 
                or connection.authorization_token is None): return

        api = self.third_party(connection.authorization_token)
        api.files_upload(activity.image, "/" + activity.filename)
