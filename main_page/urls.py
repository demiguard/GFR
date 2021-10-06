from django.urls import path
from django.conf.urls import (handler400, handler403, handler404, handler500)

#Sooo WhY do we not just import api at this point?
from main_page.views.api.api import UserEndpoint, HospitalEndpoint, DepartmentEndpoint, ConfigEndpoint, HandledExaminationsEndpoint, SambaBackupEndpoint, ProcedureEndpoint, ProcedureMappingsEndpoint, StudyEndpoint, CsvEndpoint, SearchEndpoint, ListEndpoint, AddressEndpoint, ServerConfigurationEndpoint
import main_page.views.views as views


app_name = 'main_page'

urlpatterns = [
  path('', views.IndexView.as_view(), name='index'),
  path('list_studies/new_study', views.NewStudyView.as_view(), name='new_study'),
  path('list_studies', views.ListStudiesView.as_view(), name='list_studies'),
  path('control_list_studies', views.ControlListView.as_view(), name='control_list_studies'),
  path('control_study/<str:AccessionNumber>', views.ControlView.as_view(), name='control_study'),
  path('fill_study/<str:accession_number>', views.FillStudyView.as_view(), name='fill_study'),
  path('search', views.SearchView.as_view(), name='search'),
  path('logout', views.LogoutView.as_view(), name='logout'),
  path('userguide',views.UserGuideView.as_view(), name='userguide'),
  path('deleted_studies', views.DeletedStudiesView.as_view(), name='deleted_studies'),
  path('filter', views.FilterView.as_view(), name="filter"),
  path('insufficient_permissions', views.InsufficientPermissionsView.as_view(), name="insufficient_permissions"),
  # Images
  path('present_study/<str:accession_number>', views.PresentStudyView.as_view(), name='present_study'),
  path('present_old_study/<str:accession_number>', views.PresentOldStudyView.as_view(), name='present_old_study'),
  path('QA/<str:accession_number>', views.QAView.as_view(), name='QA'),

  # Admin panel
  path('admin_panel', views.AdminPanelView.as_view(), name='admin_panel'),
  path('admin_panel/edit/<str:model_name>/<slug:obj_id>', views.AdminPanelEditView.as_view(), name='admin_panel_edit'),
  path('admin_panel/add/<str:model_name>', views.AdminPanelAddView.as_view(), name='admin_panel_add'),  
  
  # Async ajax urls
  # TODO: Make all these conform to the new RESTful api design
  path('ajax/login', views.AjaxLogin.as_view(), name='ajax_login'),
  path('ajax/update_thining_factor', views.AjaxUpdateThiningFactor.as_view(), name='ajax_update_thining_factor'),
  
  # New RESTful api design
  path('api/search', SearchEndpoint.as_view(), name='search_api'),

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
  path('api/proceduretype', ProcedureEndpoint.as_view(), name='procedure'),
  path('api/proceduretype/<int:obj_id>', ProcedureEndpoint.as_view(), name='procedure'),
  path('api/procedure_mapping', ProcedureMappingsEndpoint.as_view(), name='procedure_mapping'),
  path('api/procedure_mapping/<int:obj_id>', ProcedureMappingsEndpoint.as_view(), name='procedure_mapping'),
  path('api/study/<str:accession_number>', StudyEndpoint.as_view(), name='study'),
  path('api/csv/<str:accession_number>', CsvEndpoint.as_view(), name='csv'),
  path('api/list', ListEndpoint.as_view(), name='list_api'), # list_studies and deleted_studies
  path('api/address', AddressEndpoint.as_view(), name='address'),
  path('api/address/<int:obj_id>', AddressEndpoint.as_view(), name='address'),
  path('api/server_config', ServerConfigurationEndpoint.as_view(), name='server_config'),
  path('api/server_config/<int:obj_id>', ServerConfigurationEndpoint.as_view(), name='server_config'),
 
]
