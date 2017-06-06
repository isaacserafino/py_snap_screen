# Core Services
class PersistenceService:
    def __init__(self, model):
        self.model = model

    def save_viewer_connection(self, connection, supervisor_id):
        supervisor = self.model(active=connection.active, supervisor_id=supervisor_id.value, viewer_authentication_key=connection.authorization_token)
        supervisor.save()

    def retrieve_viewer_connection(self, supervisor_id):
        supervisor = self.model.objects.get(supervisor_id=supervisor_id.value)

        return ViewerConnection(supervisor.active, supervisor.viewer_authentication_key)


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
        authorization_token = flow_object.finish(callback_parameters)

        return ViewerConnection(True, authorization_token)
    

class ViewerService:
    def __init__(self, third_party):
        self.third_party = third_party

    def send_activity(self, activity, connection):
        if self.third_party is None or activity is None or connection is None or connection.authorization_token is None: return None

        api = self.third_party(connection.authorization_token)
        api.files_upload(activity.image, activity.filename)


# Business Model
class Activity:
    def __init__(self, filename, image):
        self.filename = filename
        self.image = image

class SupervisorId:
    def __init__(self, value):
        self.value = value

class ViewerConnection:
    def __init__(self, active, authorization_token):
        self.active = active
        self.authorization_token = authorization_token
