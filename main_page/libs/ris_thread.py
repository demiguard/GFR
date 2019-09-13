import pydicom, pynetdicom, logging, os, time, datetime, random
from . import dicomlib, dataset_creator
from .dirmanager import try_mkdir

from . import server_config, ris_thread_config_gen
from threading import Thread, Timer, Event

"""
    NOTE TO self and furture devs
    Because this thread is started at run time, it cannot access the django database as such it must be manually configured using this file.
    This includes the files:
      dicomlib.py
      dataset_creator.py

    This file describes a thread that pings ris every given time interval, retrieving 

"""

#Init mainly for logging
logger = logging.getLogger()
logger.info('Init Ris Thread')  

server_config.LOG_DIR + 'logging_thread_file_' + str(datetime.date.today()).replace(' ','').replace('.','') + '.log'
try_mkdir(server_config.LOG_DIR)
logging.basicConfig(filename=logfile, level=server_config.LOG_LEVEL, format='%(asctime)s (%(filename)s/%(funcName)s) - [%(levelname)s] : %(message)s')

logger = logging.getLogger()
logger.info('New logger Have been set up')

"""
  Config documentation

  KW : Data type, Data description

      Delay - minimum : int, The minimum amount of time (minutes) between each ping. Cannot be negative. Cannot be less than Delay - maximum. Must be part of config directory.
      Delay - maximum : int, The maximum amount of time (minutes) between each ping. Cannot be negative. Cannot be greater than Delay - minimum. Must be part of config directory.
      
"""

config = {

}
#Config[KW] = data
config['Delay_minimum'] = 12 #int
config['Delay_maximum'] = 17 #int 


class Ris_thread(Thread):
  def save_dicom(self, ds, hospital_shortname):
    #Okay so this function is in dicom lib, HOWEVER other parts of dicomlib imports something that depends. 
    #Please do not break everything by removing this function and replacing with it's counter part!
    if 'AccessionNumber' in ds:
      filepath = f'{server_config.FIND_RESPONS_DIR}{hospital_shortname}/{ds.AccessionNumber}.dcm'
      ds.fix_meta_info()
      logger.info(f'Thread saving Dicom file at: {filepath}')
      ds.save_as(filepath, write_like_original=False)

  def thread_target(self):
    """
      This is the main

      Args:
        AE_titles : List[Tuple(str,str)]
    """
    
    #init
    self.Running = True    
    
    SUCCESSFUL_FILE_TRANSFER = 0x0000
    DICOM_FILE_RECIEVED = 0xFF00
  
    logger.info('Ris Thread is starting!')
    
    while self.Running:
      logger.info("RIS thread sending response")
      try:
        ris_ip = self.config['ris_ip']
        ris_port = int(self.config['ris_port'])
        ris_AET = self.config['ris_AET']
        delay_min = int(self.config['Delay_minimum'])
        delay_max = int(self.config['Delay_maximum'])
        AE_titles = self.config['AE_items']

        assert delay_min <= delay_max
      except KeyError as KE:
        raise AttributeError(f'{KE} : {self.config}')

      ae = pynetdicom.AE(ae_title=server_config.SERVER_AE_TITLE)
      FINDStudyRootQueryRetrieveInformationModel = '1.2.840.10008.5.1.4.1.2.2.1'
      ae.add_requested_context(FINDStudyRootQueryRetrieveInformationModel)# This file generates the config for ris_thread

      association = ae.associate(
        ris_ip,
        ris_port,
        ae_title=ris_AET
      )
      
      if association.is_established:
        for AE_key in AE_titles.keys():
          AE = AE_key
          hospital_shortname = AE_titles[AE_key]

          response = association.send_c_find(
            dataset_creator.generate_ris_query_dataset(AE),
            query_model='S'
          )
          for status, dataset in response:
            
            if status.Status == DICOM_FILE_RECIEVED:
              try:
                filepath = f'{server_config.FIND_RESPONS_DIR}{hospital_shortname}/{dataset.AccessionNumber}.dcm'
                dicomlib.save_dicom(filepath,dataset)
              except:
                pass
      else:
        logger.info('Ris_thread could not connect to ris')

      #Association done 
      delay = random.uniform(delay_min, delay_max)
      logger.info(f'Ris thread going to sleep for {delay} min.')
      time.sleep(delay * 60)

      self.config = ris_thread_config_gen.read_config()
      #End of While loop

    logger.info('To die for the emperor is a glorious day - Ris_threads last words')

  # End thread_target

  def apply_kill_to_self(self):
    self.Running = False

  def __init__(self, config):
    """
      Inits a thread for ris


      Args:
        config: Directory - See other documentation for kw + values
    """
    #Init Thread
    #Thread is a daemon thread aka close on program termination
    Thread.__init__(
      self,
      name='Ris thread',
      target=self.thread_target,
      daemon=True,
    )
    self.config = config
    self.Running = False

  #End class

if not('RIS_THREAD' in globals()):
  logger.info('Creating RIS_THREAD var')
  global ris_thread
  ris_thread = Ris_thread(ris_thread_config_gen.read_config())
  ris_thread.start()


  