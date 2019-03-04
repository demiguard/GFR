# TODO: Move everything in the BELOW-END to a seperate text file since they are basically notes (-simon)
# BEGIN
# This should be the same for all rigs queries, since they all use the same, but query with different calling AETs
# RIGS_AET = "VIMCM"
# RIGS_IP = "10.143.128.247"
# RIGS_PORT = "3320"

# NOTE: This is currently setup for storage on the local test server 
# (ONLY change this to the actual PACS server when in production)
# PACS_AET = 'TEST_DCM4CHEE'
# PACS_IP = '193.3.238.103'
# PACS_PORT = '11112' # Or 11112 if no port-forwarding

# CALLING_AET = "RH_EDTA"          # Rigshospitalet
# CALLING_AET = "GLO_EDTA"       # Glostrup
# CALLING_AET = "HEHKFARGHOTR05" # Herlev

# Herlev query example
# findscu -aet HEHKFARGHOTR05 -aec VIMCM 10.143.128.247 3320 edta_query_GLO.dcm -X -od test_rsp/

# Glostrup query example
# findscu -aet GLO_EDTA -aec VIMCM 10.143.128.247 3320 edta_query_GLO.dcm -X -od test_rsp/

# EDTA_GLO # TODO: Use the glostrup AET for their RIGS system to query for patients from them



# Get all patients with "Clearance blodprove 2. gang":
# findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0008,0020="20190215" -k 0010,0020

# Name wildcard example:
# findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0010,0010="*^mi*" -k 0010,0020

# Date range example (find all patients from 20180101 to 20190101):
# findscu -S 127.0.0.1 11112 -aet RH_EDTA -aec TEST_DCM4CHEE -k 0032,1060="Clearance blodprøve 2. gang" -k 0008,0052="STUDY" -k 0008,0020="20180101-20190101" -k 0010,0020 -k 0010,0010

# END





# TODO: Change ALL paths to absolute paths when deploying, to avoid alias attacks
# NOTE: All directories MUST end in a '/'

# --- Dicom related configs ---
DICOMDICT = "/usr/share/libdcmtk12/dicom.dic"     # DCMTK dicom specification path

FINDSCU = "findscu"                               # Path to findscu application
STORESCU = "storescu"                             # Path to storescu application
GETSCU = "getscu"                                 # Path to getscu application
DCMCONV = "dcmconv"

BASE_QUERY_DIR = "./base_queries/"                # Directory contaning all base query files
SEARCH_RESPONS_DIR = "./search_responses/"        # Directory for temporarily storing search responses
FIND_RESPONS_DIR = "./active_dicom_objects/"      # Directory for temporarily storing find responses

STATIC_DIR = "./main_page/static/main_page/"
IMG_RESPONS_DIR = "{0}/images/".format(STATIC_DIR)

BASE_FIND_QUERY = "{0}base_find_query.dcm".format(BASE_QUERY_DIR)                              # Used for the list studies page
BASE_IMG_QUERY_PATH = "{0}base_img_query.dcm".format(BASE_QUERY_DIR)                          # Used for retreiving images
BASE_SEARCH_QUERY = "{0}base_search_query.dcm".format(BASE_QUERY_DIR)                            # Used for the searching page

DCMDICTPATH = "/usr/share/libdcmtk12/dicom.dic:/usr/share/libdcmtk12/private.dic"         # Dicom standard and private tags

# --- Logging ---

LOG_DIR = "./logs/"
LOG_FILE = ""
LOG_LEVEL = "DEBUG"

# --- Samba Share --- #
samba_share_path = 'main_page/static/main_page/csv/Samples'
samba_share_base_path = '/data/Samples'

#PYSMB Connection
samba_ip = '172.16.78.176'  #Change to the correct ip
samba_name = 'ubuntu'

samba_user = 'gfr'
samba_pass = 'clearance'
samba_pc   = 'kylle'
samba_share = 'data'

samba_Sample = 'Samples'
samba_backup = 'backup'




