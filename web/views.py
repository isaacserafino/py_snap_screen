from django.shortcuts import render
from django.views.generic import View

# Views
class AdministrationView(View):
    pass


class MonitoringView(View):
    pass


# Business Services
class AdministrationService:
    def __init__(self, persistence_service, supervisor_id_service, viewer_connection_service):
        self.persistence_service = persistence_service
        self.supervisor_id_service = supervisor_id_service
        self.viewer_connection_service = viewer_connection_service

    def finish_creating_supervisor_id(self, callback_parameters):
        connection = self.viewer_connection_service.finish_creating_connection(callback_parameters)
        if connection is None: return None

        supervisor_id = supervisor_id_service.generate()
        if supervisor_id is None: return None

        self.persistence_service.save_viewer_connection(connection, supervisor_id)

        return supervisor_id

    def start_creating_supervisor_id(self, callback_uri):
        self.viewer_connection_service.start_creating_connection(callback_uri)


class MonitoringService:
    def __init__(self, persistence_service, viewer_service):
        self.persistence_service = persistence_service
        self.viewer_service = viewer_service

    def track_activity(self, activity, supervisor_id):
        if supervisor_id is None or activity is None: return

        connection = self.persistence_service.retrieve_viewer_connection(supervisor_id)

        if connection is not None and connection.active:
            self.viewer_service.send_activity(activity, connection)