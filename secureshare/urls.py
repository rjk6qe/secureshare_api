from django.conf.urls import include, url
from django.contrib import admin

from rest_framework import routers
from rest_framework.authtoken import views

from report.views import ReportViewSet
from secureshare_messages.views import MessageViewSet
from authentication.views import RegisterView, LoginView

router = routers.SimpleRouter()
router.register(r'reports',ReportViewSet, base_name='Report')
router.register(r'messages',MessageViewSet)

urlpatterns = [
    # Examples:
    # url(r'^$', 'secureshare.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^api/v1/',include(router.urls)),
    url(r'^api/v1/register/',RegisterView.as_view()),
    url(r'^api/v1/login/',LoginView.as_view()),

    url(r'^api-token/',views.obtain_auth_token), # This view doesn't do anything, it just queries the database and returns the Token where user = authenticate

    url(r'^admin/', include(admin.site.urls)),
]