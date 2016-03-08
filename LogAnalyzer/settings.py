"""
default settings for programs;
all custom vars should be uppercase;
all could be cover by command line args;
"""
import os

# log file path
RMI_LOG = '/home/coremail/logs/rmi_api.log'
WMS_LOG = '/home/coremail/logs/wmsvr.log'

FILE_PATH = RMI_LOG

# config files folder
CONFIG_FOLDER = os.path.join(os.path.abspath(os.path.curdir), 'conf')

# config file names
RMI_EXCEPT = 'rmi_exceptions.cf'
WMS_EXCEPT = 'wms_exceptions.cf'

CONFIG = os.path.join(CONFIG_FOLDER, RMI_EXCEPT)  # default config is rmi_exceptions.cf

# config sections' root name(common parent)
ROOT_NAME = 'All'
# key name for omit parts
OMIT_NAME = '(OMIT)'

# results file folder
RESULT_FOLDER = os.path.join(os.path.abspath(os.path.curdir), 'result')

# omit file
SAVE_OMIT = False
OMIT_FILE = os.path.join(RESULT_FOLDER, 'omit.result')

# tabulate file
SAVE_TABULATE = False
TABULATE_FILE = os.path.join(RESULT_FOLDER, 'tabulate.result')

# specify the section in ini config that would add to tabulate file
TABULATE_SECTION = 'All/Exception'

# domain connect info
DOMAIN_CONNECT_INFO = False

# use regex to grep log?
USE_REGEX = False

# log time
YESTERDAY = True
TIME_PERIOD = None

# output result to ...
TO_CONSOLE = True
TO_FILE = True

# use prettytable outputs
USE_PRETTYTABLE = True

# single file's max size(MB); suggest less than 1/4 RAM size
# if file is bigger than it, program would use python generator to avoid out-of-mem(slower but save mem)
FILE_MAX_MB = 256
FILE_MAX = int(FILE_MAX_MB) * 1024 * 1024

# do data-visualization
DATA_VISUALIZATION = True
USE_GOOGLE_CHART = False
USE_D3JS = True
PIE_CHART = True
LINE_CHART = True
LAST_DAYS = 30
