import logging

# NOTE: All directories MUST end in a '/'
DAYS_THRESHOLD = 30                                # How long dicom files should be kept stored on the server

BASE_QUERY_DIR      = "./base_queries/"              # Directory contaning all base query files
SEARCH_DIR          = "./search_dir/"                # Directory for temporarily storing search responses
FIND_RESPONS_DIR    = "./active_dicom_objects/"      # Directory for temporarily storing find responses
BLANK_DICOM_FILE    = f"{BASE_QUERY_DIR}blank_dicom.dcm"
DELETED_STUDIES_DIR = "./deleted_studies/"            # Directory for temporarily storing deleted studies (i.e. the trashcan)
CONTROL_STUDIES_DIR = "./control_studies/"
PACS_QUEUE_DIR = "./pacs_study_queue/"
PACS_QUEUE_WAIT_TIME = 60 * 5 # Number of seconds to wait before attempting to send a file to PACS if failed

RECOVERED_FILENAME = "recovered" # Filename of recovery file containing timestamp of when a study was recovered

STATIC_DIR = "./main_page/static/main_page/"
IMG_RESPONS_DIR = f"{STATIC_DIR}images/"
CSV_DIR = f"{STATIC_DIR}csv/"

BASE_FIND_QUERY = f"{BASE_QUERY_DIR}base_find_query.dcm"                              # Used for the list studies page
BASE_IMG_QUERY_PATH = f"{BASE_QUERY_DIR}base_img_query.dcm"                          # Used for retreiving images
BASE_SEARCH_FILE = f"{BASE_QUERY_DIR}base_search_query.dcm"                            # Used for the searching page
BASE_RIGS_QUERY = f"{BASE_QUERY_DIR}base_rigs_query.dcm"                             # Used for retreiving examinations from rigs booking system

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
  0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'), #Sequnce Item
  0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
  0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor'),
  0x00231032 : ('US', '1', 'Examnation Status', '', 'ExamStatus'),
  0x0023103F : ('SQ', '1', 'Clearance History', '', 'clearancehistory')
}


# --- Plot specification --- #
PLOT_WIDTH = 19.2   # 1920 Pixels
PLOT_HEIGHT = 10.8  # 1080 Pixels

TITLE_FONT_SIZE = 28
AXIS_FONT_SIZE = 18
TEXT_FONT_SIZE = 18
LEGEND_SIZE = 18


# --- Logging --- #
LOG_FILENAME = "gfr.log"
LOG_DIR = "./log/"
LOG_LEVEL = logging.DEBUG #logging.INFO
THREAD_LOG_LEVEL = logging.DEBUG


# --- Samba Share --- #

samba_Sample = 'Samples'
samba_backup = 'backup'


# --- Hospital Dictionary --- #
HOSPITALS = {
  'TEST': 'Test Hospital',
  'RH': 'Rigshospitalet',
  'HEH': 'Herlev hospital',
  'HI': 'Hillerød hospital',
  'FH': 'Frederiksberg hospital',
  'BH': 'Bispebjerg hospital',
  'GLO': 'Glostrup hospital',
  'HVH': 'Hvidovre hospital',
}


# --- SCP Server --- #
SERVER_AE_TITLE = 'HVHFBERGHK7' 
STATION_NAMES = ['RH_EDTA', 'GLO_EDTA', 'HEHKFARGHOTR05', 'HVHFBERGHK7', 'BFHKFNMGFR1', 'HIKFARGFR13']

SERVER_NAME    = 'GFRCalc'
SERVER_VERSION = 'v1.1'



# --- ris_thread --- #
# Minimum and maximum number of minutes to sleep ris_thread for
SLEEP_DELAY_MIN = 10
SLEEP_DELAY_MAX = 20
