from django.apps import AppConfig

import logging



class MainPageConfig(AppConfig):
  name = 'main_page'

  def ready(self):
    """
    Override of function which is called once on server start up

    Remark:
      Any imports of custom code should happen here as certain sub modules of
      Django might not have been initialized yet, such as models.

      Importing models outside of this functions might also cause tests
      to interact with the production database, instead of the one
      created at run-time specifically for the tests.

      For more about these types of problems see:
      https://docs.djangoproject.com/en/2.2/ref/applications/
    """
    from .libs.query_wrappers import pacs_query_wrapper as pacs
    from . import Startup

    Startup.init_logger()
    logger = logging.getLogger(name='ServerLogger')
    logger.info('Started Logger')
    try:
      self.scp_server = pacs.start_scp_server()
      logger.info('Started SCP server')
    except Exception as e:
      logger.info('Failed to start SCP server because:{0}'.format(str(e)))

    from .libs import ris_thread_config_gen 
    from .libs import ris_thread
