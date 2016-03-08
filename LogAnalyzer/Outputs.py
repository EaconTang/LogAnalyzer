"""
Outputs module:
    1. outputs to console
    2. save outputs to file
    3. data visualization
        1) each result's pie-chart and bar-chart
        2) trends in line-chart in past days(defaults to 7)
"""
from datetime import datetime
from time import mktime
import os
from nvd3 import pieChart, lineChart
from Filters import CoreFilter
from Utils import list_to_json, MyTable, dict_to_json, google_charts_html
from Utils import log_info


class BaseOutputs(object):
    def __init__(self):
        self.vars_dict = {}

    @property
    def _vars(self):
        return self.vars_dict

    @_vars.setter
    def _vars(self, key_value):
        assert isinstance(key_value, dict)
        self.vars_dict.update(key_value)

    def to_file(self):
        raise NotImplementedError

    def to_console(self):
        raise NotImplementedError

    def to_visual_html(self):
        raise NotImplementedError


class PrettyTableOutputs(BaseOutputs):
    def __init__(self):
        super(PrettyTableOutputs, self).__init__()

    @staticmethod
    def dict_to_table(res, sortby_count=False):
        """ trans a dict to table; key->'Type', value->'Count'
        """
        assert isinstance(res, dict)
        table = MyTable(['Type', 'Count'])
        table.align['Type'] = "l"
        for k, v in res.iteritems():
            table.add_row([k, v])
        if not sortby_count:
            return table.get_string(sortby='Type')
        else:
            return table.get_string(sortby='Count', reversesort=True)

    def dict_to_table_horizontal(self, res):
        """ trans a dict to table horizontal
        """
        assert isinstance(res, dict)
        keys, values = zip(*[(k, v) for k, v in sorted(res.iteritems())])

        table_title = ['LogDate']
        table_title.extend(keys)
        table_title.append('WriteTime')
        table = MyTable(table_title)

        table_row = [self.vars_dict.get('FILE_DATE')]
        table_row.extend(values)
        table_row.append(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        table.add_row(table_row)

        return table


class FileOutputs(PrettyTableOutputs):
    def __init__(self):
        super(FileOutputs, self).__init__()

    def to_file(self, res):
        if self.vars_dict.get('SAVE_OMIT'):
            self.save_omit(res, self.vars_dict.get('OMIT_FILE'))
        if self.vars_dict.get('SAVE_TABULATE'):
            self.save_tabulate(res, self.vars_dict.get('TABULATE_FILE'))

    @log_info()
    def save_omit(self, res, filename):
        """ save omit info(errors not configured or not counted) to file
        """
        to_write = ''

        if not self.vars_dict.get('USE_PRETTYTABLE'):
            to_write += dict_to_json(res.get('RESULT_COUNTS')) + '\n'
        else:
            to_write += self.dict_to_table(res.get('RESULT_COUNTS')) + '\n'
            to_write += self.dict_to_table(res.get('RESULT_COUNTS'), True) + '\n'

        omit_key = '/'.join([self.vars_dict['ROOT_NAME'], 'Exception', self.vars_dict['OMIT_NAME']])
        to_write += '\nOmit exceptions lines info:\n\n'
        to_write += list_to_json(res.get('RESULT_LINES').get(omit_key))

        with open(filename, 'w') as f:
            f.write(to_write)

    @log_info()
    def save_tabulate(self, res, filename):
        """ add each time's result to tabulate file
        """
        section_name = self.vars_dict.get('TABULATE_SECTION')
        res_table = {}
        for k, v in res.get('RESULT_COUNTS').iteritems():
            if k == section_name:
                short_key = k
                res_table[short_key] = v
                continue
            if k.startswith(section_name) and not k.endswith(self.vars_dict.get('OMIT_NAME')):
                short_key = k[len(section_name) + 1:]
                res_table[short_key] = v

        table = self.dict_to_table_horizontal(res_table)

        try:
            tabulate_file_lines = open(filename).readlines()
        except IOError:
            tabulate_file_lines = []

        tabulate_file_titles = CoreFilter.grep_lines('LogDate', tabulate_file_lines, False)

        if not tabulate_file_lines:
            # means a new file
            to_write = table.get_title_with_bar() + '\n' + \
                       table.get_row_data(1) + '\n'
        elif tabulate_file_titles != [] and table.get_row_data(0) != tabulate_file_titles[-1]:
            # means config updated
            to_write = '\n###############config file is updated##############\n' + \
                       table.get_title_with_bar() + '\n' + \
                       table.get_row_data(1) + '\n'
        else:
            # just add it
            to_write = table.get_row_data(1) + '\n'

        with open(filename, 'a+') as f:
            f.write(to_write)


class ConsoleOutputs(PrettyTableOutputs):
    def __init__(self):
        super(ConsoleOutputs, self).__init__()

    def to_console(self, res):
        if not self.vars_dict.get('USE_PRETTYTABLE'):
            print dict_to_json(res.get('RESULT_COUNTS'))
        else:
            print self.dict_to_table(res.get('RESULT_COUNTS'))


class VisualizationOutputs(PrettyTableOutputs):
    def __init__(self):
        super(VisualizationOutputs, self).__init__()

    @property
    def res_counts(self):
        """ type-counts to be visualized('All' and 'All/Exception' are removed)
            trans to datastructs like:
                [
                    ['All/Exception/api fail', 0],
                    ['All/Exception/msg exception', 3900],
                    ...
                ]
        """
        result = self.vars_dict.get('RESULT')
        result_counts = result['RESULT_COUNTS']
        del result_counts['All']  # remove 'ALL'
        del result_counts['All/Exception']
        type_counts = []
        assert isinstance(result_counts, dict)
        for type, count in sorted(result_counts.iteritems()):
            type_counts.append([type, count])
        return type_counts

    def get_tabulate_data(self, lastdays=-1):
        """ read a tabulate file, trans to datastructs like:
            [
                ['LogDate','Exception','api fail',...],
                ['2016-01-01',41669,0,...],
                ...
            ]
        """
        try:
            with open(self.vars_dict.get('TABULATE_FILE')) as f:
                data_lines = f.readlines()
            data_lines = filter(lambda x: '|' in x, data_lines)
            data_lines = map(lambda x: x.strip().lstrip('|').rstrip('|').split('|'), data_lines)
            data_lines_new = []
            for n, data_line in enumerate(data_lines):
                if n == 0:
                    data_lines_new.append(data_line[:-1])
                else:
                    del data_line[-1]
                    tmp_list = []
                    for i, data in enumerate(data_line):
                        if i != 0:
                            data = int(data)
                        tmp_list.append(data)
                    data_lines_new.append(tmp_list)
            if 0 < lastdays <= len(data_lines_new) - 1:
                data_lines_lastdays = data_lines_new[-lastdays:]
                data_lines_lastdays.insert(0, data_lines_new[0])
                return data_lines_lastdays
            return data_lines_new
        except IOError, e:
            print e.message
            return None

    def google_api_htmls(self):
        """ visualize data using google-charts API;
            just replace some vars in html template in Utils.py
        """
        global html_lineChart, html_pieChart
        if self.vars_dict.get('LINE_CHART'):
            chart_type = 'line_chart'
            curve_datas = self.get_tabulate_data(self.vars_dict.get('LAST_DAYS'))
            title = self.vars_dict.get('TABULATE_FILE')
            height = 768
            width = 1366
            html_lineChart = google_charts_html(chart_type, curve_datas, title, width, height)
        if self.vars_dict.get('PIE_CHART'):
            chart_type = 'pie_chart'
            rows = self.res_counts
            title = self.vars_dict.get('FILE_PATH')
            height = 768
            width = 1366
            html_pieChart = google_charts_html(chart_type, rows, title, width, height)
        return html_lineChart, html_pieChart

    def d3js_htmls(self):
        """ visualize data using D3.js(wrapped by python-nvd3)
        """
        global html_lineChart, html_pieChart
        if self.vars_dict.get('LINE_CHART'):
            chart_name = self.vars_dict.get('TABULATE_FILE')
            height = 768
            width = 1366
            line_chart = lineChart(name='[line]'+chart_name,
                                   height=height,
                                   width=width)
            line_data = self.get_tabulate_data(self.vars_dict.get('LAST_DAYS'))
            # x_data = [each[0].strip() for each in line_data][1:]
            # x_data = map(lambda x: mktime(datetime.strptime(x, '%Y-%m-%d').timetuple()), x_data)
            x_data = list(range(-30, 0))
            name_list = line_data[0][1:]
            y_data_list = []
            for i in range(1, len(line_data[0])):
                y_data_list.append([each[i] for each in line_data[1:]])
            extra_serie = {
                'tooltip': {
                    'y_start': '',
                    'y_end': 'counts'
                }
            }
            for name, y_data in zip(name_list, y_data_list):
                line_chart.add_serie(y=y_data, x=x_data, name=name, extra=extra_serie)
            line_chart.buildhtml()
            html_lineChart = line_chart.htmlcontent
        if self.vars_dict.get('PIE_CHART'):
            rows = self.res_counts
            xdata, ydata = zip(*rows)
            extra_serie = {
                'tooltip': {
                    'y_start': '',
                    'y_end': 'counts'
                }
            }
            chart_name = self.vars_dict.get('FILE_PATH')
            height = 768
            width = 1366
            pie_chart = pieChart(name='[pie]'+chart_name, color_category='category20c', height=height, width=width)
            pie_chart.set_containerheader("\n\n<h2>" + chart_name + "</h2>\n\n")
            pie_chart.add_serie(y=ydata, x=xdata, extra=extra_serie)
            pie_chart.buildhtml()
            html_pieChart = pie_chart.htmlcontent
        return html_lineChart, html_pieChart

    @log_info()
    def to_visual_html(self):
        global html_pieChart, html_lineChart
        if self.vars_dict.get('USE_GOOGLE_CHART'):
            html_lineChart, html_pieChart = self.google_api_htmls()
        elif self.vars_dict.get('USE_D3JS'):
            html_lineChart, html_pieChart = self.d3js_htmls()
        html_lineChart_path = os.path.join(self.vars_dict.get('RESULT_FOLDER'), 'lineChart.html')
        html_pieChart_path = os.path.join(self.vars_dict.get('RESULT_FOLDER'), 'pieChart.html')
        with open(html_lineChart_path, 'w') as f:
            f.write(html_lineChart)
        with open(html_pieChart_path, 'w') as f:
            f.write(html_pieChart)


class Outputs(ConsoleOutputs, FileOutputs, VisualizationOutputs):
    def __init__(self, filters_res):
        super(Outputs, self).__init__()
        self._vars = filters_res
        self.res = self.vars_dict.get('RESULT')

    def process(self):
        if self.vars_dict.get('TO_CONSOLE'):
            self.to_console(self.res)
        if self.vars_dict.get('TO_FILE'):
            self.to_file(self.res)
        if self.vars_dict.get('DATA_VISUALIZATION'):
            self.to_visual_html()

    def process_line_chart(self):
        self.to_visual_html()


if __name__ == '__main__':
    from Inputs import Inputs
    from Filters import Filters

    filter_res = Filters(Inputs().process()).process()
    Outputs(filter_res).process()
