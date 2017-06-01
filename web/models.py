from django.db import models, connection

# Core Services
class PersistenceService:
    def save_viewer_connection(self, connection, supervisor_id):
        pass

    def retrieve_viewer_connection(self, supervisor_id):
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

    def start_creating_connection(self):
        if self.flow is None: return None
        
        return self.flow.start()

    def finish_creating_connection(self, callback_parameters):
        if self.flow is None: return None
        
        # TODO: (IMS) Handle exceptions
        return self.flow.finish(callback_parameters)
    

class ViewerService:
    def __init__(self, third_party):
        self.third_party = third_party

    def send_activity(self, activity, connection):
        if self.third_party is None or activity is None or connection is None or connection.authorization_token is None: return None

        api = self.third_party(connection.authorization_token)
        api.files_upload(activity.image, activity.filename)


# Model
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
