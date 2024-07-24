
import environ

from django.conf import settings

env = environ.Env()
environ.Env.read_env()

ENV_VAR_CONTROL_STUDIES_PATH = "GFR_CONTROL_STUDY_PATH"
ENV_VAR_DELETE_PATH          = "GFR_DELETE_PATH"
ENV_VAR_LOG_FILE_PATH        = "GFR_LOG_PATH"
ENV_VAR_FIND_RESPONSE_PATH   = "GFR_FIND_RESPONSE_PATH"
ENV_VAR_SEARCH_CACHE_PATH    = "GFR_SEARCH_CACHE_PATH"
ENV_VAR_SEARCH_DIR_PATH      = "GFR_SEARCH_PATH"
ENV_VAR_STATIC_DIR_PATH      = "GFR_STATIC_PATH"

# NOTE: All directories MUST end in a '/'
DAYS_THRESHOLD = 30                                # How long dicom files should be kept stored on the server


PACS_QUEUE_WAIT_TIME = 60 * 5 # Number of seconds to wait before attempting to send a file to PACS if failed
RECOVERED_FILENAME = "recovered" # Filename of recovery file containing timestamp of when a study was recovered

STATIC_DIR = f"{settings.STATIC_ROOT}/main_page/"
IMG_RESPONS_DIR = f"{STATIC_DIR}images/"
CSV_DIR = f"{STATIC_DIR}csv/"

# Private Dicom tag definitions
new_dict_items = {
  0x00231001 : ('LO', '1', 'GFR', '', 'GFR'), # Normal, Moderat Nedsat, Svært nedsat
  0x00231002 : ('LO', '1', 'GFR Version', '', 'GFRVersion'), # Version 1.
  0x00231010 : ('LO', '1', 'GFR Method', '', 'GFRMethod'),
  0x00231011 : ('LO', '1', 'Body Surface Method', '', 'BSAmethod'),
  0x00231012 : ('DS', '1', 'clearance', '', 'clearance'),
  0x00231014 : ('DS', '1', 'normalized clearance', '', 'normClear'),
  0x00231018 : ('DT', '1', 'Injection time', '', 'injTime'),     # Tags Added
  0x00231019 : ('US', '1', 'Vial number', '', 'VialNumber'),
  0x0023101A : ('DS', '1', 'Injection weight', '', 'injWeight'),
  0x0023101B : ('DS', '1', 'Vial weight before injection', '', 'injbefore'),
  0x0023101C : ('DS', '1', 'Vial weight after injection', '', 'injafter'),
  0x00231020 : ('SQ', '1', 'Clearance Tests', '', 'ClearTest'),
  0x00231021 : ('DT', '1', 'Sample Time', '', 'SampleTime'), # Sequence Item
  0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'), #Sequence Item
  0x00231023 : ('DS', '1', 'Deviation on Sample','','Deviation'), #Sequence Item
  0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
  0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor'),
  0x00231032 : ('US', '1', 'Examnation Status', '', 'ExamStatus'),
  0x0023103F : ('SQ', '1', 'Clearance History', '', 'clearancehistory'),
  0x00231040 : ('LT', '1', 'Clearence Comment', '', 'ClearenceComment')
}


# --- Plot specification --- #
PLOT_WIDTH = 19.2   # 1920 Pixels
PLOT_HEIGHT = 10.8  # 1080 Pixels

TITLE_FONT_SIZE = 28
AXIS_FONT_SIZE = 18
TEXT_FONT_SIZE = 18
LEGEND_SIZE = 18


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
#SERVER_AE_TITLE = 'HVHFBERGHK7'
#STATION_NAMES = ['RH_EDTA', 'GLO_EDTA', 'HEHKFARGHOTR05', 'HVHFBERGHK7', 'BFHKFNMGFR1', 'HIKFARGFR13']

SERVER_NAME    = 'GFRCalc'
SERVER_VERSION = 'v1.4'


# --- ris_thread --- #
# Minimum and maximum number of minutes to sleep ris_thread for
SLEEP_DELAY_MIN = 10
SLEEP_DELAY_MAX = 20
