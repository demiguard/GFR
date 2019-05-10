from django.apps import AppConfig
from .libs.query_wrappers import pacs_query_wrapper as pacs
import Startup

import logging

class MainPageConfig(AppConfig):
    name = 'main_page'
    def ready(self):
        Startup.init_logger()
        Startup.init_dicom_env()
        logger = logging.getLogger(name='ServerLogger')
        logger.info('Started Logger')
        try:
            self.scp_server = pacs.start_scp_server()
            logger.info('Started SCP server')
        except Exception as e:
            logger.info('Failed to start SCP server because:{0}'.format(str(e)))