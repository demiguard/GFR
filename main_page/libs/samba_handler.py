import glob, os, datetime, tempfile
import pandas

from . import server_config
from smb.SMBConnection import SMBConnection


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
    pass

  try:
    smbconn.createDirectory(server_config.samba_share, u'backup/{0}'.format(hospital))
  except:
    pass

  Stored_bytes = smbconn.storeFileFromOffset(
    server_config.samba_share,
    store_path,
    temp_file,
    truncate=False
  )
  smbconn.deleteFiles(server_config.samba_share, fullpath) 

def smb_get_csv(hospital):
  """
    hospital: string 

  """

  now = datetime.datetime.now()

  returnarray = []

  conn = SMBConnection(
    server_config.samba_user, 
    server_config.samba_pass, 
    server_config.samba_pc, 
    server_config.samba_name
    )

  conn.connect(server_config.samba_ip)

  hospital_sample_folder = '/{0}/{1}/'.format(server_config.samba_Sample, hospital)
  

  samba_files = conn.listPath(server_config.samba_share, hospital_sample_folder)

  for samba_file in samba_files:
    if samba_file.filename in ['.', '..']:
      continue
    temp_file = tempfile.NamedTemporaryFile()

    fullpath =  hospital_sample_folder + samba_file.filename

    file_attri, file_size = conn.retrieveFile(server_config.samba_share,fullpath, temp_file)
    temp_file.seek(0)

    pandas_ds = pandas.read_csv(temp_file.name)
    returnarray.append(pandas_ds)
    #File Cleanup
    datestring = pandas_ds['Measurement date & time'][0]
    protocol = pandas_ds['Protocol name'][0]
    correct_filename = (datestring + protocol + '.csv').replace(' ', '').replace(':','').replace('-','').replace('+','')

    if not samba_file.filename == correct_filename and not samba_file.isReadOnly:
      #Rename
      conn.rename(server_config.samba_share, hospital_sample_folder + samba_file.filename, hospital_sample_folder + correct_filename)

    dt_examination = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
    if not ((now -  dt_examination).days == 0):
      move_to_backup(conn,temp_file, hospital, hospital_sample_folder + correct_filename, correct_filename)


    temp_file.close()


  conn.close()
  return returnarray







  