import logging

# NOTE: All directories MUST end in a '/'

# --- Dicom related configs ---
FINDSCU = "findscu"                               # Path to findscu application
STORESCU = "storescu"                             # Path to storescu application
GETSCU = "getscu"                                 # Path to getscu application
DCMCONV = "dcmconv"

DAYS_THRESHOLD = 30                                # How long dicom files should be kept stored on the server

BASE_QUERY_DIR      = "./base_queries/"              # Directory contaning all base query files
SEARCH_DIR          = "./search_dir/"                # Directory for temporarily storing search responses
FIND_RESPONS_DIR    = "./active_dicom_objects/"      # Directory for temporarily storing find responses
BLANK_DICOM_FILE    = "{0}blank_dicom.dcm".format(BASE_QUERY_DIR)
DELETED_STUDIES_DIR = "./deleted_studies/"            # Directory for temporarily storing deleted studies (i.e. the trashcan)

STATIC_DIR = "./main_page/static/main_page/"
IMG_RESPONS_DIR = "{0}/images/".format(STATIC_DIR)

BASE_FIND_QUERY = "{0}base_find_query.dcm".format(BASE_QUERY_DIR)                              # Used for the list studies page
BASE_IMG_QUERY_PATH = "{0}base_img_query.dcm".format(BASE_QUERY_DIR)                          # Used for retreiving images
BASE_SEARCH_FILE = "{0}base_search_query.dcm".format(BASE_QUERY_DIR)                            # Used for the searching page
BASE_RIGS_QUERY = "{0}base_rigs_query.dcm".format(BASE_QUERY_DIR)                             # Used for retreiving examinations from rigs booking system

DICOMDICT_UBUNTU = "/usr/share/libdcmtk12/dicom.dic"
DICOMDICT_CENTOS = "/usr/local/share/dcmtk/dicom.dic"

# Private Dicom tag definitions
new_dict_items = {
  0x00231001 : ('LO', '1', 'GFR', '', 'GFR'), # Normal, Moderat Nedsat, Svært nedsat
  0x00231002 : ('LO', '1', 'GFR Version', '', 'GFRVersion'), # Version 1.
  0x00231010 : ('LO', '1', 'GFR Method', '', 'GFRMethod'),
  0x00231011 : ('LO', '1', 'Body Surface Method', '', 'BSAmethod'),
  0x00231012 : ('DS', '1', 'clearance', '', 'clearance'),
  0x00231014 : ('DS', '1', 'normalized clearance', '', 'normClear'),
  0x00231018 : ('DT', '1', 'Injection time', '', 'injTime'),     # Tags Added
  0x0023101A : ('DS', '1', 'Injection weight', '', 'injWeight'),
  0x0023101B : ('DS', '1', 'Vial weight before injection', '', 'injbefore'),
  0x0023101C : ('DS', '1', 'Vial weight after injection', '', 'injafter'),
  0x00231020 : ('SQ', '1', 'Clearance Tests', '', 'ClearTest'),
  0x00231021 : ('DT', '1', 'Sample Time', '', 'SampleTime'), # Sequence Items
  0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'),
  0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
  0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor')
}

# --- Logging --- #

LOG_DIR = "./log/"
LOG_LEVEL = logging.INFO

# --- Samba Share --- #

#PYSMB Connection
samba_ip = '10.49.144.2'
samba_name = 'gfr'

samba_user = 'gfr'
samba_pass = 'gfr'
samba_pc   = 'gfr'
samba_share = 'data'

samba_Sample = 'Samples'
samba_backup = 'backup'


# -- Hospital Dictionary -- #

hospitals = {
    'RH': 'Rigshospitalet',
    'HEH': 'Herlev hospital',
    'HI': 'Hillerød hospital',
    'FH': 'Frederiksberg hospital',
    'BH': 'Bispebjerg hospital',
    'GLO': 'Glostrup hospital',
    'HVH': 'Hvidovre hospital',
}