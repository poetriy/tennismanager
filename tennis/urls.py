from django.conf.urls import url

from tennis import views

urlpatterns = [
    url(r'^$', views.standings, name='standings'),
    url(r'^report/$', views.report, name='report'),
    url(r'^report/singles/$', views.report_singles, name='report_singles'),
    url(r'^report/doubles/$', views.report_doubles, name='report_doubles'),
    url(r'^report/make_singles/$', views.make_singles, name='make_singles'),
    url(r'^report/make_doubles/$', views.make_doubles, name='make_doubles'),
    url(r'^history/$', views.history, name='history'),
    url(r'^history/(?P<match_id>\d+)/$', views.delete_history, name='delete_history'),
    url(r'^players/(?P<player_id>\d+)/$', views.player_details, name='player_details'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
]
