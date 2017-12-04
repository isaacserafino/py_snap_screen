"""py_snap_screen URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
#from django.contrib import admin
from django.contrib.auth import views as auth_views

import web.views
import osm_web.views

urlpatterns = [
#    url(r'^admin/', admin.site.urls),
    url(r'^monitor/', web.views.MonitoringView.as_view()),
    url(r'^supervisor/', web.views.AdministrationView.as_view()),
    url(r'^viewer-connection-callback/', web.views.ViewerConnectionCallbackView.as_view()),

    url('', include('social_django.urls', namespace='social')),
    url(r'^accounts/login/$', web.views.LoginView.as_view()),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view()),

    # OSM path mappings
    url(r'^open_software_market/project/list/', osm_web.views.ProjectList.as_view(), name='project-list'),
    url(r'^open_software_market/project/update/(?P<slug>[-\w]+)', osm_web.views.ProjectUpdate.as_view(),
            name='project-update'),

    url(r'^open_software_market/project/view/(?P<slug>[-\w]+)', osm_web.views.ProjectDetail.as_view(),
            name='project-detail'),

    url(r'^open_software_market/project/add/', osm_web.views.ProjectCreate.as_view(), name='project-add'),

    url(r'^open_software_market/project/delete/(?P<slug>[-\w]+)', osm_web.views.ProjectDeactivate.as_view(),
            name='project-deactivate')

]
