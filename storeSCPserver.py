import django
from django.core.exceptions import ObjectDoesNotExist

import os
import logging
import time


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clairvoyance.settings')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'clairvoyance.settings'
    django.setup()


from pydicom import Dataset
from pynetdicom import AE, StoragePresentationContexts, evt

from config import server_log_file_path

from main_page.models import ServerConfiguration
from main_page.libs import server_config
from main_page.libs import dicomlib

logger = logging.getLogger(__name__)




def logEvent(event):
    logger.info(event)

def on_C_STORE(event):
    logger.info('Recieved C-Store Event')
    try:
      retrieved_dataset           = event.dataset
      retrieved_dataset.file_meta = event.file_meta
    except:
      return_dataset = Dataset()
      return_dataset.Status = 0xC123
      return_dataset.add_new(0x00000902, 'LO', 'Could not load retrieve Dataset')

      return return_dataset
    #logger.info(f'Dataset:\n {retrieved_dataset}')

    if 'AccessionNumber' in retrieved_dataset:
      if 0x00230010 in retrieved_dataset and retrieved_dataset.Modality == 'OT':
        filename = f'{retrieved_dataset.AccessionNumber}.dcm'
        fullpath = server_config.SEARCH_DIR + filename
        dicomlib.save_dicom(fullpath, retrieved_dataset)

      return 0x0000

    else:
      return_dataset = Dataset()
      return_dataset.Status = 0xCAFE
      return_dataset.add_new(0x00000902, 'LO', 'This service cannot store DICOM objects without AccessionNumber') 
      return return_dataset

def on_C_MOVE(event):
    """
      C-Move is not supportted by our service, since it's not connected any dicom network

      This function is where you need to update, if this is changing.
    """
    logger.info('Recieved C-Move event')
    try:
      logger.info(f'Move Data Recieved:\n{event.dataset}')
      logger.info(f'destination is:{event.move_destination}')
    except:
      logger.info(f'Could not log dataset or move_destination')
    response_dataset = Dataset()

    response_dataset.Status = 0xA801
    response_dataset.add_new(0x00000902, 'LO', 'This service cannot store DICOM objects without AccessionNumber')

    return response_dataset


event_handlers = [
    (evt.EVT_C_MOVE, on_C_MOVE),
    (evt.EVT_C_STORE, on_C_STORE),
]


if __name__ == "__main__":
    try:
        sc = ServerConfiguration.objects.get(pk=1)
    except ObjectDoesNotExist:
        logger.info("Server is not yet configured - Exiting1")
        exit(1)
    while True:
        server = AE(ae_title=sc.AE_title)
        server.supported_contexts = StoragePresentationContexts

        server.start_server(('', 104), evt_handlers=event_handlers)
        logger.error("Server Died!")
        #If the server dies, try and revive it after 5 min.
        time.sleep(300)
