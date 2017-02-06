# LogAnalyzer
一个日志分析工具

功能介绍： 

- 将需要统计的信息（不限于报错）配置为ini格式文件，支持细分错误类型（树形分类）
- 工具扫描配置文件，遍历日志文件统计出错次数（根据大多数log特点，将匹配到的一行出错记录记为1次出错）
- 配合crontab，就日志每天的出错信息汇总到一个表格文件（Excel友好的ascii表格）
- 保存没有配置统计但存在于日志中的错误信息（作去重），方便全面了解日志的出错情况
- 将配置文件转换为统一的数据结构，实现支持不同格式的配置文件（包括ini/json/yaml）
- 通过ini配置查找的样式（相当于linux命令行grep的内容），单个属性支持配置为正则、配置为多个样式（多个样式间可以是AND或OR逻辑）
- 支持通过指定日期时间段，同时分析多个日志文件
- 独立实现和开启域名信息统计
- 利用python的generator特性，实现文件生成器，不仅节约内存，而且加快了读取速度，同时也能支持读取超大日志文件了（G级别）


参数说明：

    $ python log_miner.py -h
    Usage: python log_miner.py [-f value] [-c value] [-t] [-T value] [-o] [-O value]

    Options:
      -h, --help            show this help message and exit
      -f FILE, --file=FILE  specify a log file to be scan, defaults to yesterday's
                            rmi_api.log
      -c CONFIG, --config=CONFIG
                            specify a config file to be load,defaults to
                            ~/LogMiner/conf/rmi_exceptions.cf
      -t, --tabulate        use this flag to save the results to the file,defaults
                            to under "~/LogMiner/results"
      -T TABULATE, --tabulate-file=TABULATE
                            specify a file to save the tabulate table,defaults to
                            "rmi_api_error.tabulate"
      -o, --omit            use this flag to save the omit info that were not
                            classified.It would be saved under
                            "~/LogMiner/results"
      -O OMIT, --omit-file=OMIT
                            specific a filename to save the omit info,defaults to
                            "rmi_api.omit.{Datetime}"
      -y, --yesterday-log   plus this flag to specify yesterday's log file, based
                            on the file specify by '-f'

    参数说明（全部为可选）：
    "-h"：显示帮助信息
    "-f"：指定需要分析的日志（文本文件），默认为今天的rmi_api日志
    "-c"：指定使用哪个配置文件，默认为”rmi_exceptions.cf“
    "-t"：使用此参数，程序会将统计结果保存到汇总文件表
    "-T"：指定将统计结果保存到哪个文件，默认为"/results/rmi_api_error.tabulate"
    "-o"：使用此参数，程序会将控制台输出和未统计的错误信息保存到文件
    "-O"：指定将未统计信息保存到哪个文件，默认为"/results/rmi_api.omit."+日志日期
    “-y”：使用此参数，表示分析昨天的日志；如先用“-f”参数指定了“wmsvr.log”，加上“-y”后，程序将分析昨天的wmsvr日志（适用于设置crontab定时任务）

运行示例：  

    $ python log_miner.py -t -c conf/rmi_exceptions_main.cf  
    正在处理log...
    处理完毕!
    以下是统计数目：
    +----------------------------+--------+
    | Type                       | Count  |
    +----------------------------+--------+
    | /All                       | 773722 |
    | /All/(OMIT)                | 754110 |
    | /All/Exception             | 19612  |
    | /All/Exception/(OMIT)      |  4548  |
    | /All/Exception/fail on     |  331   |
    | /All/Exception/msg e       |  9180  |
    | /All/Exception/rfof        |  260   |
    | /All/Exception/server fail |  5290  |
    | /All/Exception/skip msg    |   0    |
    | /All/Exception/sync        |   3    |
    +----------------------------+--------+
    +----------------------------+--------+
    | Type                       | Count  |
    +----------------------------+--------+
    | /All                       | 773722 |
    | /All/(OMIT)                | 754110 |
    | /All/Exception             | 19612  |
    | /All/Exception/msg e       |  9180  |
    | /All/Exception/server fail |  5290  |
    | /All/Exception/(OMIT)      |  4548  |
    | /All/Exception/fail on     |  331   |
    | /All/Exception/rfof        |  260   |
    | /All/Exception/sync        |   3    |
    | /All/Exception/skip msg    |   0    |
    +----------------------------+--------+
    本次统计已经写入汇总文件表：/home/coremail/logs/LogMiner/results/rmi_api_error.tabulate

查看汇总文件表：

    $ cat results/rmi_api_error.tabulate
    +------------+-----------+---------+-------+------+-------------+----------+------+---------------------+
    |  LogDate   | Exception | fail on | msg e | rfof | server fail | skip msg | sync |      WriteTime      |
    +------------+-----------+---------+-------+------+-------------+----------+------+---------------------+
    | 2015-11-16 |   13856   |   157   |  3684 | 136  |     5112    |    0     |  10  | 2015-11-19 09:44:49 |
    | 2015-11-17 |   19378   |   219   |  9068 | 195  |     5193    |    0     |  7   | 2015-11-19 09:44:54 |
    | 2015-11-18 |   19612   |   331   |  9180 | 260  |     5290    |    0     |  3   | 2015-11-19 09:45:09 |


配置文件说明：

    每个section下的属性，表示一种错误类型；属性值代表这种错误的日志样式，相当于linux下grep的样式（暂不支持正则或通配符，如有需要可开启支持正则）；
    每个section名下的错误类型，都是以section名为类型的子类型；
    属性值必须用双引号包围，如果某种错误类型有多个样式（相当于linux下的多个grep条件），用逗号”,“分隔，用方括号”[]“包围（如：["grep1","grep2"]）；
    section名里边用斜杠”/“分隔类型，section下的各个属性最好不要带有”/“；
    所有错误类型的父类为“/All/Exception”，所有新添加的类型的父类为“/All”；
    如果父类错误数目不等于所有子类错误数目之和，则将遗漏统计的信息和数目都统计到“/(OMIT)”中

配置文件示例：

    [/All/Exception]
    fail on = "Fail on"
    msg e= "MessagingException"

    [/All/Exception/fail on]
    getMessageByUID = "Fail on getMessageByUID"
    getReceivedDate = "Fail on getReceivedDate"

统计结果可视化：

- 提供了两种实现，一种是利用GoogleCharts的api，另一种是用D3.js；默认使用D3.js生成html结果文件
- 程序默认会在/result文件夹下生成两个文件（如已存在，会覆盖更新）：
    - pieChart.html ：本次分析数据的饼状图
    - lineChart.html ：过去30天，日志统计数据的走势图
- 上述两种视图，默认是显示所有统计分析的错误类型，但也可以单独点击查看某几个错误统计的饼状图和走势图。

![](http://qn.tangyingkang.com/image/loganalyzer/piechart.png)  

![](http://qn.tangyingkang.com/image/loganalyzer/linechart.png)
