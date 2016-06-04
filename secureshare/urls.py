from django.conf.urls import include, url
from django.contrib import admin
from login import views as login_view

urlpatterns = [
    # Examples:
    # url(r'^$', 'secureshare.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^login/',login_view.test),
    url(r'^admin/', include(admin.site.urls)),
]
