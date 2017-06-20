# Core Services
class MonthlyLimitService:
    def __init__(self, date):
        self.date = date

    def retrieve_current_month(self):
        today = self.date.today()

        return today.replace(day=1)

    def determine_whether_current_date_before(self, expiration):
        today = self.date.today()

        return today <= expiration        


class PersistenceService:
    def __init__(self, activity_model, supervisor_model):
        self.activity_model = activity_model
        self.supervisor_model = supervisor_model

    def save_viewer_connection(self, connection, supervisor_id):
        supervisor = self.supervisor_model(active=connection.active, supervisor_id=supervisor_id.value, viewer_authentication_key=connection.authorization_token)
        supervisor.save()

    def retrieve_viewer_connection(self, supervisor_id):
        supervisor = self.supervisor_model.objects.get(supervisor_id=supervisor_id.value)

        return ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)

    def retrieve_supervisor_by_inbound_identity_token(self, inbound_identity_token):
        supervisor = self.supervisor_model.objects.get(inbound_identity_token=inbound_identity_token)

        supervisor_id = SupervisorId(supervisor.supervisor_id)
        viewer_connection = ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)
        return SupervisorStatus(supervisor.active, supervisor.premium_expiration, supervisor_id, viewer_connection)

    # TODO:
    def retrieve_activity_count(self, supervisor_id, activity_month):
        pass

    def increment_activity_count(self, supervisor_id, activity_month):
        pass


class SupervisorIdService:
    def __init__(self, id_generator):
        self.id_generator = id_generator

    def generate(self):
        value = self.id_generator.random(length=7)

        return SupervisorId(value)


class ViewerConnectionService:
    def __init__(self, flow):
        self.flow = flow

    def create_flow_object(self, viewer_key, viewer_secret, callback_url, session, csrf_token_attribute_name):
        if self.flow is None: return None

        return self.flow(viewer_key, viewer_secret, callback_url, session, csrf_token_attribute_name)

    def start_creating_connection(self, flow_object):
        if flow_object is None: return None

        return flow_object.start()

    def finish_creating_connection(self, callback_parameters, flow_object):
        if flow_object is None: return None
        
        # TODO: (IMS) Handle exceptions
        result = flow_object.finish(callback_parameters)

        return ViewerConnection(True, result.access_token)
    

class ViewerService:
    def __init__(self, third_party):
        self.third_party = third_party

    def send_activity(self, activity, connection):
        if self.third_party is None or activity is None or connection is None or connection.authorization_token is None: return None

        api = self.third_party(connection.authorization_token)
        api.files_upload(activity.image, "/" + activity.filename)


# Business Model
class Snap:
    def __init__(self, filename, image):
        self.filename = filename
        self.image = image

class SupervisorId:
    def __init__(self, value):
        self.value = value

class SupervisorStatus:
    def __init__(self, active, premium_expiration, supervisor_id, viewer_connection):
        self.active = active
        self.premium_expiration = premium_expiration
        self.supervisor_id = supervisor_id
        self.viewer_connection = viewer_connection

class ViewerConnection:
    def __init__(self, active, authorization_token):
        self.active = active
        self.authorization_token = authorization_token
