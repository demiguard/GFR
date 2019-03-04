from django.urls import path

from . import views
from . import Startup

Startup.start_up()


# TODO: Clear the search history directory contaning query filter files: currently it's 'hist_tmp'
app_name = 'main_page'
urlpatterns = [
  path('', views.index, name='index'),
  path('list_studies/new_study', views.new_study, name='new_study'),
  path('list_studies', views.list_studies, name='list_studies'),
  path('fill_study/<str:rigs_nr>', views.fill_study, name='fill_study'),
  path('fetch_study', views.fetch_study, name='fetch_study'),
  path('present_study/<str:rigs_nr>', views.present_study, name='present_study'),
   path('present_old_study/<str:rigs_nr>', views.present_old_study, name='present_old_study'),
  path('logout', views.logout_page, name='logout'),
  path('settings', views.settings, name='settings'),
  path('documentation', views.documentation, name='documentation'),
  # Async ajax urls
  path('ajax/login', views.ajax_login, name='ajax_login'),
]