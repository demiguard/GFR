from django.urls import path
from django.conf.urls import (handler400, handler403, handler404, handler500)

from main_page.views.api.api import UserEndpoint, HospitalEndpoint, DepartmentEndpoint, ConfigEndpoint, HandledExaminationsEndpoint, SambaBackupEndpoint
import main_page.views.views as views


app_name = 'main_page'

urlpatterns = [
  path('', views.IndexView.as_view(), name='index'),
  path('list_studies/new_study', views.NewStudyView.as_view(), name='new_study'),
  path('list_studies', views.ListStudiesView.as_view(), name='list_studies'),
  path('fill_study/<str:ris_nr>', views.FillStudyView.as_view(), name='fill_study'),
  path('search', views.SearchView.as_view(), name='search'),
  path('logout', views.LogoutView.as_view(), name='logout'),
  path('documentation', views.DocumentationView.as_view(), name='documentation'),
  path('userguide',views.UserGuideView.as_view(), name='userguide'),
  path('deleted_studies', views.DeletedStudiesView.as_view(), name='deleted_studies'),
  #Images
  path('present_study/<str:ris_nr>', views.PresentStudyView.as_view(), name='present_study'),
  path('present_old_study/<str:ris_nr>', views.PresentOldStudyView.as_view(), name='present_old_study'),
  path('QA/<str:accession_number>', views.QAView.as_view(), name='QA'),

  # Admin panel
  path('admin_panel', views.AdminPanelView.as_view(), name='admin_panel'),
  path('admin_panel/edit/<str:model_name>/<slug:obj_id>', views.AdminPanelEditView.as_view(), name='admin_panel_edit'),
  path('admin_panel/add/<str:model_name>', views.AdminPanelAddView.as_view(), name='admin_panel_add'),  
  
  # Async ajax urls
  # TODO: Make all these conform to the new RESTful api design
  path('ajax/login', views.AjaxLogin.as_view(), name='ajax_login'),
  path('ajax/search', views.AjaxSearch.as_view(), name='ajax_search'),
  path('ajax/update_thining_factor', views.AjaxUpdateThiningFactor.as_view(), name='ajax_update_thining_factor'),
  path('ajax/delete_study', views.AjaxDeleteStudy.as_view(), name='ajax_delete_study'),
  path('ajax/restore_study', views.AjaxRestoreStudy.as_view(), name='ajax_restore_study'),
  
  # New RESTful api design
  path('api/user', UserEndpoint.as_view(), name='user'),
  path('api/user/<int:obj_id>', UserEndpoint.as_view(), name='user'),
  path('api/hospital', HospitalEndpoint.as_view(), name='hospital'),
  path('api/hospital/<int:obj_id>', HospitalEndpoint.as_view(), name='hospital'),
  path('api/department', DepartmentEndpoint.as_view(), name='department'),
  path('api/department/<int:obj_id>', DepartmentEndpoint.as_view(), name='department'),
  path('api/handled_examination', HandledExaminationsEndpoint.as_view(), name='handled_examination'),
  path('api/handled_examination/<str:obj_id>', HandledExaminationsEndpoint.as_view(), name='handled_examination'),
  path('api/config', ConfigEndpoint.as_view(), name='config'),
  path('api/config/<int:obj_id>', ConfigEndpoint.as_view(), name='config'),
  path('api/get_backup/<str:date>', SambaBackupEndpoint.as_view(), name='get_backup'),
]
