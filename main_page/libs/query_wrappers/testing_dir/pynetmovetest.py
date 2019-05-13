import pynetdicom, pydicom, logging, time

from pydicom import Dataset
from pynetdicom import AE, StoragePresentationContexts

logging.basicConfig(level =logging.DEBUG, filename = 'movelogfile.log')
logger = logging.getLogger()

pacs_ip = '10.143.128.234'
pacs_port = 104
pacs_aet = 'VIPDICOM'
my_ae = 'HVHFBERGHK7'

ae = AE(ae_title=my_ae)

#ae.add_requested_context('1.2.840.10008.5.1.4.1.2.1.2')
ae.add_requested_context('1.2.840.10008.5.1.4.1.2.2.2')
#ae.add_requested_context('1.2.840.10008.5.1.4.1.2.3.2')

ds = Dataset()

ds.SpecificCharacterSet = 'ISO_IR 100' 
ds.add_new(0x00080018, 'UI', '1.2.276.0.7230010.3.1.4.279752782.5764.1554286136.933281')
ds.add_new(0x00080052, 'CS', 'STUDY')
ds.PatientID = 'QP-3849995'
ds.add_new(0x0020000D, 'UI', '1.3.51.0.1.1.10.143.20.159.13951884.6955968')
ds.add_new(0x0020000E, 'UI', '1.2.276.0.7230010.3.1.3.279752782.5764.1554286136.933279')
#ds.StudyTime = ''
#ds.StudyDate = ''
#ds.QueryRetrieveView = 'CLASSIC'

assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_aet)

if assoc.is_established:
  logger.info('Connection established')

  response = assoc.send_c_move(ds, my_ae, query_model='S')

  logger.info('Accepted Context')
  for context in assoc.accepted_contexts:
    logger.info(context)

  logger.info('Rejected Contexts')
  for context in assoc.rejected_contexts:
    logger.info(context)

  for (status, indentifyer) in response:
    logger.info('Status message:')
    logger.info(status)
    logger.info(hex(status.Status))
    logger.info( 'Indentifyer')
    logger.info(indentifyer)
    logger.info(type(indentifyer))

  assoc.release()
else:
  logger.info('Connection Rejected')

