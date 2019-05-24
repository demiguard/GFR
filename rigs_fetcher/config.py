import logging

DB_FILEPATH = "/home/simon/Documents/clearance-stuff/GFR/db.sqlite3"

LOG_FILEPATH = "./log/fetcher.log"
LOG_LEVEL = logging.INFO

INTERVAL = 20              # Interval to to execute function
INTERVAL_VARIANCE = 0     # Max random interval variance of 1 min.

CALLING_AET = "RH_EDTA"           # Calling AET
RIGS_AET = "VIMCM"             # Rigs AET
RIGS_IP = "10.143.128.247"
RIGS_PORT = 3320
STORAGE_DIRECTORY = "/home/simon/Documents/clearance-stuff/GFR/active_dicom_objects/RH"
ACCEPTED_PROCEDURES = (
  'Clearance Fler-blodprøve', 
  'GFR, Cr-51-EDTA, one sampel',
  'GFR, Tc-99m-DTPA'
)