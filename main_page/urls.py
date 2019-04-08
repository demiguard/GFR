from django.urls import path
from django.conf.urls import (handler400, handler403, handler404, handler500)

from . import views
from . import Startup

Startup.start_up()

app_name = 'main_page'
urlpatterns = [
  path('', views.index, name='index'),
  path('list_studies/new_study', views.NewStudy.as_view(), name='new_study'),
  path('list_studies', views.ListStudies.as_view(), name='list_studies'),
  path('fill_study/<str:rigs_nr>', views.fill_study, name='fill_study'),
  path('search', views.search, name='search'),
  path('present_study/<str:rigs_nr>', views.present_study, name='present_study'),
   path('present_old_study/<str:rigs_nr>', views.present_old_study, name='present_old_study'),
  path('logout', views.logout_page, name='logout'),
  path('settings', views.settings, name='settings'),
  path('documentation', views.documentation, name='documentation'),
  # Async ajax urls
  path('ajax/login', views.ajax_login, name='ajax_login'),
  path('ajax/search', views.ajax_search, name='ajax_search'),
]
