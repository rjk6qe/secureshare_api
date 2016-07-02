from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

from rest_framework import routers
from rest_framework.authtoken import views

from report.views import ReportView, FolderView
from secureshare_messages.views import MessageInboxView, MessageSendView, MessageOutboxView, MessageDecryptView
from authentication.views import RegisterView, LoginView, LogoutView, SiteManagerView, GroupView

#router = routers.SimpleRouter()
#router.register(r'reports',ReportViewSet, base_name='Report')
#router.register(r'messages',MessageViewSet, base_name='Message')

urlpatterns = [
    # Examples:
    # url(r'^$', 'secureshare.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    #url(r'^api/v1/',include(router.urls)),

    url(r'^api/v1/users/register/',RegisterView.as_view()),
    url(r'^api/v1/users/login/',LoginView.as_view()),
    url(r'^api/v1/users/logout/',LogoutView.as_view()),
    url(r'api/v1/users/groups/',GroupView.as_view()),

    url(r'^api/v1/users/site_manager/',SiteManagerView.as_view()),
#    url(r'^api/v1/encrypt/generate/', GenerateView.as_view()),

    url(r'^api/v1/reports/$',ReportView.as_view()),
    url(r'^api/v1/reports/(?P<pk>[0-9]+)/$',ReportView.as_view()),
    url(r'^api/v1/reports/folders/$',FolderView.as_view()),
    url(r'^api/v1/reports/folders/(?P<pk>[0-9]+)/$',FolderView.as_view()),

    url(r'^api/v1/messages/inbox/$',MessageInboxView.as_view()),
    url(r'^api/v1/messages/inbox/(?P<pk>[0-9]+)/$',MessageInboxView.as_view()),
    url(r'^api/v1/messages/outbox/$',MessageOutboxView.as_view()),
    url(r'^api/v1/messages/outbox/(?P<pk>[0-9]+)/$',MessageOutboxView.as_view()),
    url(r'^api/v1/messages/send/$',MessageSendView.as_view()),
    url(r'^api/v1/messages/decrypt/(?P<pk>[0-9]+)/$', MessageDecryptView.as_view()),


#    url(r'^api-token/',views.obtain_auth_token), # This view doesn't do anything, it just queries the database and returns the Token where user = authenticate

    url(r'^admin/', include(admin.site.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)