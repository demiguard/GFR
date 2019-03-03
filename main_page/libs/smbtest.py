from smb.SMBConnection import SMBConnection
from StringIO   import StringIO
import tempfile, pandas, datetime

user = 'gfr'
password = 'clearance'
clientName = 'cjen0668'
server_name = 'ubuntu'
server_ip = '176.16.83.176' #change this

hospital = 'RH'

conn = SMBConnection(user, password, clientName, server_name)
conn.connect(server_ip, 139)

shares = conn.listShares()
sharename = ''

for share in shares:
    if not share.isSpecial:
        sharename = share.name
        print('Name:', share.name, 'Comment:', share.comment )

paths = conn.listPath('data', '/')

for path in paths
    try: 
        print('No slash:\n','filepath', path.filename, '\n Is a directory', path.isDirectory)
    except:
        pass


paths = conn.listPath('/data', '/')

for path in paths
    try: 
        print('Slash:\n','filepath', path.filename, '\n Is a directory', path.isDirectory)
    except:
        pass


paths = conn.listPath('/data', '/Samples/')

for path in paths
    try: 
        print('Slash:\n','filepath', path.filename, '\n Is a directory', path.isDirectory)
    except:
        pass


#Change this line to fit correctly
base_path = '/Samples/{0}/'.format(hospital)
backup_path = '/backup/{0}/'.format(hospital)
paths = conn.listPath(sharename, base_path)
pandas_set = [] #tempfile list


for path in paths:
    new_temp_file = tempfile.NamedTemporaryFile()

    print(path.filename, 'is read only', path.isReadOnly)

    #Not sure what to do with this?
    security = conn.getSecurity(share, base_path + path.filename)

    #Could be '{0}'.format(path) , I have no fucking clue what else should
    file_attributes, file_size = conn.retrieveFile(share, path, new_temp_file)
    #I think I can do this!
    pandas_ds = pandas.read_csv(new_temp_file.name)
    pandas_set.append(pandas_ds)

    #This might need
    new_temp_file.seek(0)
    raw_data = f.read(file_size)
    print(type(raw_data)) #Check if string or binary

    header_list = pandas_ds.columns.values.tolist()

    print('Headers in:', path.filename )
    for header in header_list: 
        print(header)

    datestring = pandas_ds['Measurement date & time'][0]
    protocol = pandas_ds['Protocol'][0]

    #Method - Time of examination
    correct_filename = datestring + ' ' + protocol

    if path.filename == correct_filename and not path.isReadOnly:
        print('Should Rename ', path.filename ,' to ', correct_filename)
        #Rename
        #conn.rename(share, base_path + path.filename, base_path + correct_filename)


