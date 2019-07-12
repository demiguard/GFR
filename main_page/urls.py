from django.urls import path
from django.conf.urls import (handler400, handler403, handler404, handler500)

from . import views
from . import Startup

Startup.start_up()

app_name = 'main_page'
urlpatterns = [
  path('', views.IndexView.as_view(), name='index'),
  path('list_studies/new_study', views.NewStudyView.as_view(), name='new_study'),
  path('list_studies', views.ListStudiesView.as_view(), name='list_studies'),
  path('fill_study/<str:rigs_nr>', views.fill_study, name='fill_study'),
  path('search', views.SearchView.as_view(), name='search'),
  path('logout', views.LogoutView.as_view(), name='logout'),
  path('documentation', views.documentation, name='documentation'),
  path('settings', views.SettingsView.as_view(), name='settings'),
  path('deleted_studies', views.DeletedStudiesView.as_view(), name='deleted_studies'),
  #Images
  path('present_study/<str:rigs_nr>', views.present_study, name='present_study'),
  path('present_old_study/<str:rigs_nr>', views.present_old_study, name='present_old_study'),
  path('QA/<str:accession_number>', views.QAView.as_view(), name='QA'),
  path('admin_panel', views.AdminPanelView.as_view(), name='admin_panel'),
  # Async ajax urls
  path('ajax/login', views.AjaxLogin.as_view(), name='ajax_login'),
  path('ajax/search', views.AjaxSearch.as_view(), name='ajax_search'),
  path('ajax/update_thining_factor', views.AjaxUpdateThiningFactor.as_view(), name='ajax_update_thining_factor'),
  path('ajax/delete_study', views.AjaxDeleteStudy.as_view(), name='ajax_delete_study'),
  path('ajax/restore_study', views.AjaxRestoreStudy.as_view(), name='ajax_restore_study'),
  path('ajax/get_backup/<str:date>', views.AjaxGetbackup.as_view(), name='ajax_getbackup'),
  path('ajax/handled_examination', views.AjaxHandledExaminationView.as_view(), name='ajax_handled_examination')
]
