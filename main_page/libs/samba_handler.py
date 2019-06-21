import glob, os, datetime, tempfile, logging
import pandas

from . import server_config
from smb.SMBConnection import SMBConnection

logger = logging.getLogger()


def move_to_backup(smbconn, temp_file, hospital,fullpath, filename):
  """
    smbconn : An Active SMBConnection
    temp_file : A File object with a write method


  """
  hospital_backup_folder = '{0}/{1}/'.format(server_config.samba_backup, hospital)
  store_path = hospital_backup_folder + filename 

  try:
    smbconn.createDirectory(server_config.samba_share, u'/backup')
  except:
    logger.info('Failed to create Directory /backup')

  try:
    smbconn.createDirectory(server_config.samba_share, u'backup/{0}'.format(hospital))
  except:
    logger.info('Failed to create Directory')

  Stored_bytes = smbconn.storeFileFromOffset(
    server_config.samba_share,
    store_path,
    temp_file,
    truncate=False
  )
  smbconn.deleteFiles(server_config.samba_share, fullpath) 

  logger.info('Moved File to back up')

def smb_get_csv(hospital, timeout = 5):
  """
    hospital: string 

  """

  now = datetime.datetime.now()

  returnarray = []

  conn = SMBConnection(
    server_config.samba_user, 
    server_config.samba_pass, 
    server_config.samba_pc, 
    server_config.samba_name,
    use_ntlm_v2=True
    )

  is_connected = conn.connect(server_config.samba_ip, timeout = timeout)

  logger.info(f'Samba Connection was succesful:{is_connected}')
  logger.debug(f'/{server_config.samba_Sample}/{hospital}/')

  hospital_sample_folder = f'/{server_config.samba_Sample}/{hospital}/'
  
  logger.debug(f'Searching Share: {server_config.samba_share}, at: {hospital_sample_folder}')
  samba_files = conn.listPath(server_config.samba_share, hospital_sample_folder)
  logger.debug(f'Got Files:{len(samba_files)}')

  for samba_file in samba_files:
    if samba_file.filename in ['.', '..']:
      continue  
    temp_file = tempfile.NamedTemporaryFile()

    fullpath =  hospital_sample_folder + samba_file.filename
    logger.info(f'Opening File:{samba_file.filename} at {fullpath}')
    file_attri, file_size = conn.retrieveFile(server_config.samba_share, fullpath, temp_file)
    temp_file.seek(0)
    
    pandas_ds = pandas.read_csv(temp_file.name)
    #File Cleanup
    logger.info(list(pandas_ds))
    
    datestring = pandas_ds['Measurement date & time'][0]
    protocol = pandas_ds['Protocol name'][0]
    
    logger.debug(datestring)
    logger.debug(protocol)

    correct_filename = (datestring + protocol + '.csv').replace(' ', '').replace(':','').replace('-','').replace('+','')

    if not samba_file.filename == correct_filename and not samba_file.isReadOnly:
      #Rename
      logger.info(f'Attempting to Rename {hospital_sample_folder + samba_file.filename} into {hospital_sample_folder + correct_filename}')
      try:
        conn.rename(server_config.samba_share, hospital_sample_folder + samba_file.filename, hospital_sample_folder + correct_filename)
        logger.info(f'succesfully moved {hospital_sample_folder + samba_file.filename} into {hospital_sample_folder + correct_filename}')
      except: 
        logger.info(f'Deleted File: {hospital_sample_folder + samba_file.filename}')
        conn.deleteFiles(server_config.samba_share, hospital_sample_folder + samba_file.filename)


    dt_examination = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
    if not ((now -  dt_examination).days <= 0):
      logger.debug(f'Moving File {hospital_sample_folder+correct_filename} to backup')
      move_to_backup(conn,temp_file, hospital, hospital_sample_folder + correct_filename, correct_filename)
    else:
      returnarray.append(pandas_ds)
      
    temp_file.close()

  conn.close()
  #sort return array
  sorted_array = sorted(returnarray, key=lambda x: x['Measurement date & time'][0],reverse=True)

  return sorted_array

def get_backup_file(date, hospital, timeout = 30):
  """

    input:
      date: a datetime object, a date object

  """
  return_pandas_list = []

  if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
    date = str(date)[:10].replace('-','')

  conn = SMBConnection(
    server_config.samba_user, 
    server_config.samba_pass, 
    server_config.samba_pc, 
    server_config.samba_name
    )

  conn.connect(server_config.samba_ip)

  hospital_backup_folder = '/{0}/{1}/'.format(server_config.samba_backup, hospital)

  samba_files = conn.listPath(server_config.samba_share, hospital_backup_folder)

  for samba_file in samba_files:
    temp_file = tempfile.NamedTemporaryFile()

    if date == samba_file.filename[:8]:

      fullpath = hospital_backup_folder + samba_file.filename
      file_attri, file_len = conn.retrieveFile(server_config.samba_share, fullpath, temp_file, timeout= 30)
      temp_file.seek(0)
      pandas_ds = pandas.read_csv(temp_file.name)
      return_pandas_list.append(pandas_ds)

  return return_pandas_list


  