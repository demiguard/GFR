from django.apps import AppConfig

from main_page.libs import server_config

import threading
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
    from . import models

    # AET of the server (used as AET for SCP server for receiving studies 
    # i.e. we move to this AET)
    ae_title = models.ServerConfiguration.objects.get(id=1).AE_title


    # Setup SCP server logger
    logger = logging.getLogger()
    logger.info('Started Logger')
    try:
      self.scp_server = pacs.start_scp_server(ae_title)
      logger.info(f'Started SCP server with AE_title: {ae_title}')
    except Exception as e:
      logger.info('Failed to start SCP server because:{0}'.format(str(e)))

    from main_page.libs import ris_thread

    RT = ris_thread.RisFetcherThread(
      ae_title, 
      server_config.SLEEP_DELAY_MIN, 
      server_config.SLEEP_DELAY_MAX
    )
    RT.start()
    Startup.init_logger()
    # logger.info(f"Thread: is running with daemon={RT.daemon}")
    # logger.info(f"Thread: current number of threads={threading.active_count()}")
    
    # a_variable = True
    # for thread in threading.enumerate():
    #   logger.info(f"Thread: current thread with name: {thread.name}")
    #   if thread.name == 'Ris thread':
    #     a_variable = False
      
    # if a_variable:
    #   logger.info("Thread: starting next thread")
    #   RT = ris_thread.RisFetcherThread(ris_thread_config_gen.read_config())
    #   RT.start()
