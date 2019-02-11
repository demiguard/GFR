from django.urls import path
from . import views

app_name = 'main_page'
urlpatterns = [
  path('', views.index, name='index'),
  path('list_studies/new_study', views.new_study, name='new_study'),
  path('list_studies', views.list_studies, name='list_studies'),
  path('fill_study/<str:rigs_nr>', views.fill_study, name='fill_study'),
  path('fetch_study', views.fetch_study, name='fetch_study'),
  path('present_study/<str:rigs_nr>', views.present_study, name='present_study'),
  path('logout', views.logout_page, name='logout')
]