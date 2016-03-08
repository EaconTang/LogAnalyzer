"""
Inputs module
Including:
    1. default settings from file <settings.py>
    2. command line args
    3. configuration from conf/*.conf
    4. log files
Template Method Pattern
"""
import datetime
import json
import os
import re
from optparse import OptionParser

import settings
from Utils import MyConfigParser, convert_time_period, log_info


class BaseInputs(object):
    def __init__(self):
        self.vars_dict = {}

    @property
    def _vars(self):
        return self.vars_dict

    @_vars.setter
    def _vars(self, key_value):
        assert isinstance(key_value, dict)
        self._vars.update(key_value)

    def default_vars(self):
        raise NotImplementedError

    def command_args(self):
        raise NotImplementedError

    def read_conf(self, *args, **kwargs):
        raise NotImplementedError

    def read_log_file(self, *args, **kwargs):
        raise NotImplementedError


class DefaultSetting(BaseInputs):
    def __init__(self):
        super(DefaultSetting, self).__init__()
        self._default_vars_list = []
        self._default_vars = {}

    @property
    def default_var_list(self):
        self._default_vars_list = filter(lambda x: x == x.upper(), dir(settings))
        return self._default_vars_list

    @property
    def default_vars(self):
        var_list = self.default_var_list
        var_vals = vars(settings)
        for each in var_list:
            self._default_vars[each] = var_vals.get(each)
        return self._default_vars


class CommandArgs(BaseInputs):
    def __init__(self):
        super(CommandArgs, self).__init__()

    @property
    def arg_parser(self):
        """provide optional arguments from command lines
        """
        usage = "usage: python %prog [-h] [-f value] [-c value] [-T] [-t value] [-O] [-o value] [-Y]"
        usage += " [-R]"
        usage += " [--time value]"
        parser = OptionParser(usage)
        parser.add_option('-f', '--file', dest='FILE_PATH',
                          help='specify a log file to be scan, defaults to today\'s rmi_api.log')
        parser.add_option('-c', '--config', dest='CONFIG',
                          help='specify a config file to be load,defaults to conf/rmi_exceptions.cf')
        parser.add_option('-T', '--tabulate', dest='SAVE_TABULATE',
                          help='use this flag to add the results to the file',
                          action='store_true', default=self.vars_dict['SAVE_TABULATE'])
        parser.add_option('-t', '--tabulate-file', dest='TABULATE_FILE',
                          help='specify a file to save the tabulate results')
        parser.add_option('-O', '--omit', dest='SAVE_OMIT',
                          help='use this flag to save the omit info that were not matched and classified',
                          action='store_true', default=self.vars_dict['SAVE_OMIT'])
        parser.add_option('-o', '--omit-file', dest='OMIT_FILE',
                          help='specific a file to save the omit info')
        # parser.add_option('-Y', '--yesterday-log', dest='YESTERDAY',
        #                   help='use this flag to add yesterday\'s datetime to file specfied',
        #                   action='store_true', default=self.vars_dict['YESTERDAY'])
        parser.add_option('-R', '--regex', dest='USE_REGEX',
                          help='use this flag to turn regex-match on',
                          action='store_true', default=self.vars_dict['USE_REGEX'])
        parser.add_option('--time', dest='TIME_PERIOD',
                          help='specify a time period as format "YYYYMMDD:YYYYMMDD"')
        return parser

    @property
    def command_args(self):
        """return a dict contains args uesd from command line
        """
        parser = self.arg_parser
        # (options, args) = parser.parse_args()
        (options, args) = parser.parse_args(
            ['-c', 'conf/rmi_exceptions.cf', '-f', 'test_files/rmi_api.log.2016-01-01'])

        options_list = [('FILE_PATH', options.FILE_PATH),
                        ('CONFIG', options.CONFIG),
                        ('OMIT_FILE', options.OMIT_FILE),
                        ('SAVE_OMIT', options.SAVE_OMIT),
                        ('TABULATE_FILE', options.TABULATE_FILE),
                        ('SAVE_TABULATE', options.SAVE_TABULATE),
                        # ('YESTERDAY', options.YESTERDAY),
                        ('USE_REGEX', options.USE_REGEX),
                        ('TIME_PERIOD', options.TIME_PERIOD),
                        ]
        used_options = [option for option in options_list if option[1]]
        return dict(used_options)


class ConfFile(BaseInputs):
    def __init__(self):
        super(ConfFile, self).__init__()

    @log_info()
    def read_conf(self, conf_file):
        if conf_file.endswith('ini') or conf_file.endswith('conf') or conf_file.endswith('cf'):
            return self.read_ini(conf_file)
        elif conf_file.endswith('json'):
            return self.read_json(conf_file)
        elif conf_file.endswith('yaml'):
            return self.read_yaml(conf_file)
        else:
            exit('[Error]Unsupported config file format?')

    def read_ini(self, conf_file):
        ini_config = MyConfigParser()
        ini_config.read(conf_file)
        return {'INI': ini_config}

    def read_json(self, conf_file):
        with open(conf_file) as f:
            json_config = json.loads(f.read(), encoding='utf-8')
        return {'JSON': json_config}

    def read_yaml(self, cong_file):
        raise NotImplementedError


class LogFile(BaseInputs):
    def __init__(self):
        super(LogFile, self).__init__()

    @log_info()
    def read_log_file(self, log_file, yesterday=True, time_period=None):
        # read yesterday's logfile
        if yesterday:
            YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
            filename = '.'.join([log_file, str(YESTERDAY)])
            return {
                'FILE_DATE': str(YESTERDAY),
                'FILE_PATH': filename,
                'FILE_GEN': self.file_gen(filename),
            }
        # read log files specified by datetime
        if time_period:
            time_period, filenames = convert_time_period(time_period, log_file)
            return {
                'FILE_DATE': time_period,
                'FILE_PATH': filenames,
                'FILE_GEN': self.files_gen(filenames),
            }

        m = re.match(r'.+(\d{4}-\d{2}-\d{2})', log_file)
        if m:
            file_date = m.group(1)
        else:
            file_date = str(datetime.date.today())
        return {
            'FILE_DATE': file_date,
            'FILE_GEN': self.file_gen(log_file),
        }

    def file_gen(self, filename):
        """ a generator that each time gens lines from single file
        """
        if os.path.getsize(filename) > self.vars_dict.get('FILE_MAX'):
            with open(filename) as f:
                while 1:
                    lines = f.readlines(self.vars_dict.get('FILE_MAX'))
                    if not lines:
                        break
                    yield lines
        else:
            with open(filename) as f:
                yield f.readlines()

    def files_gen(self, filenames):
        """a generator that each time gens lines from multi files
        """
        def _gens(filename_list):
            # return a generator that gens generator(file_gen)
            for filename in filename_list:
                yield self.file_gen(filename)

        gs = _gens(filenames)
        for g in gs:
            for lines in g:
                yield lines


class Inputs(DefaultSetting, CommandArgs, ConfFile, LogFile):
    def __init__(self):
        super(Inputs, self).__init__()

    def process(self):
        """
        1. load default vars to vars dict
        2. update command args to vars dict
        3. load config instance to vars dict
        4. load file(s) to vars dict
        """
        self._vars = self.default_vars
        self._vars = self.command_args
        self._vars = self.read_conf(self.vars_dict['CONFIG'])
        self._vars = self.read_log_file(self.vars_dict['FILE_PATH'],
                                        self.vars_dict['YESTERDAY'],
                                        self.vars_dict['TIME_PERIOD'])
        return self._vars


if __name__ == '__main__':
    inputs = Inputs()
    res = inputs.process()
