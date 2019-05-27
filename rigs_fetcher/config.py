import logging

DB_FILEPATH = "/home/gfr/GFR/db.sqlite3" # Filepath to sqlite database

LOG_FILEPATH = "/home/gfr/GFR/rigs_fetcher/log/fetcher.log" # Filepath to log file
LOG_LEVEL = logging.INFO  # Logging level

INTERVAL = 60 * 5              # Interval to to execute function
INTERVAL_VARIANCE = 0     # Max random interval variance of 1 min.

CALLING_AET = "RH_EDTA"           # Calling AET
RIGS_AET = "VIMCM"             # Rigs AET
RIGS_IP = "10.143.128.247"  # Rigs server ip
RIGS_PORT = 3320  # Port to rigs server
STORAGE_DIRECTORY = "/home/gfr/GFR/active_dicom_objects/RH" # Where fetched dicom objects should be stored
ACCEPTED_PROCEDURES = ( # Which procedures should be accepted by the fetcher
  'Clearance Fler-blodprøve', 
  'GFR, Cr-51-EDTA, one sampel',
  'GFR, Tc-99m-DTPA'
)