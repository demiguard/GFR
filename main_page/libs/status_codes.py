# Defines names for HTTP status codes, for details see:
# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

# 2xx Success
HTTP_STATUS_OK = 200
HTTP_STATUS_NO_CONTENT = 204

# 4xx Client errors
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_FORBIDDEN = 403

# 5xx Server errors
HTTP_STATUS_INTERNAL_ERROR = 500


# pynetdicom status codes
DATASET_AVAILABLE = 0xFF00
TRANSFER_COMPLETE = 0x0000