# 2XX
OK           = 200
OK_AVERAGE   = 201
OK_NO_DATA   = 202
OK_CREATING  = 203
OK_CREATED   = 204
OK_REMOVING  = 205
OK_REMOVED   = 206
# 4XX
ERROR        = 400
ERROR_CONFIG = 401
ERROR_CREATE = 402

CATALOG = {
    # OK
    OK          : None,
    OK_AVERAGE  : "Running. Average of usage: {average}.",
    OK_NO_DATA  : "Running. Please wait for collecting usage.",
    OK_CREATING : "Creating a new autoscaling vm: {name}. Please wait for a few minutes.",
    OK_CREATED  : "Created a new autoscaling vm: {name}. Reset and re-collect vm usage.",
    OK_REMOVING : "Removing the autoscaling vm: {name}. Please wait for a few minutes.",
    OK_REMOVED  : "Removed the autoscaling vm: {name}. Reset and re-collect vm usage.",
    # ERROR
    ERROR       : None,
    ERROR_CONFIG: "Stopped. Configuration is incorrect.",
    ERROR_CREATE: "Failed to create a new autoscaling vm: {name}.",
}
