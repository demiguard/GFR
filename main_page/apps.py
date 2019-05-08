from django.apps import AppConfig
from .libs.query_wrappers import pacs_query_wrapper as pacs

class MainPageConfig(AppConfig):
    name = 'main_page'
    def ready(self):
        pacs.start_scp_server()