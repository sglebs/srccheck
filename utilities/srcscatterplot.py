"""Source Code Stats Scatter Plot.

Usage:
  srcscatterplot    --in=<inputUDB> \r\n \
                    [--dllDir=<dllDir>]\r\n \
                    [--skipLibs=<skipLibs>]\r\n \
                    [--fileQuery=<fileQuery>]\r\n \
                    [--classQuery=<classQuery>]\r\n \
                    [--routineQuery=<routineQuery>]\r\n \
                    [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                    [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                    [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                    [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                    [--xMetric=<xMetric>] \r\n \
                    [--yMetric=<yMetric>] \r\n \
                    [--ballMetric=<ballMetric>] \r\n \
                    [--ballSizeMin=<ballSizeMin>] \r\n \
                    [--ballSizeMax=<ballSizeMax>] \r\n \
                    [--ballSizeRate=<ballSizeRate>] \r\n \
                    [--scope=<scope>] \r\n \
                    [--verbose]

Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK. [default: C:/Program Files/SciTools/bin/pc-win64/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse [default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  --xMetric=<xMetric>                           Name of metric to use in the x axis. [default: CountLineCode]
  --yMetric=<yMetric>                           Name of metric to use in the y axis. [default: CountDeclClass]
  --ballMetric=<ballMetric>                     Name of metric to use for ball sizes. [Default: AvgCyclomaticModified]
  --ballSizeMin=<ballSizeMin>                   Minimum size of the ball (when the metric is zero). [Default: 10]
  --ballSizeMax=<ballSizeMax>                   Maximum size of the ball [Default: 300]
  --ballSizeRate=<ballSizeRate>                 Rate at which the ball size grows per unit of the metric. [Default: 10]
  --scope=<scope>                               if the metric is applied to File|Class|Routine [default: File]
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -z, --skipZeroes                              If you want to skip datapoints which are zero [default: false]

Errors:
  DBAlreadyOpen        - only one database may be open at once
  DBCorrupt            - bad database file
  DBOldVersion         - database needs to be rebuilt
  DBUnknownVersion     - database needs to be rebuilt
  DBUnableOpen         - database is unreadable or does not exist
  NoApiLicense         - Understand license required

Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import sys
import os
from docopt import docopt
from utilities.utils import stream_of_entity_with_metrics, save_scatter

def scatter_plot (db, cmdline_arguments, entityQuery, regex_str_ignore_item, scope_name):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    entities = db.ents(entityQuery)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    verbose = cmdline_arguments["--verbose"]

    annotations = []
    x_values = []
    x_metric_name = cmdline_arguments["--xMetric"]
    y_values = []
    y_metric_name = cmdline_arguments["--yMetric"]
    ball_values = []
    color_values = []
    ball_size_min = float(cmdline_arguments["--ballSizeMin"])
    ball_size_max = float(cmdline_arguments["--ballSizeMax"])
    ball_size_rate = float(cmdline_arguments["--ballSizeRate"])
    ball_metric_name = cmdline_arguments["--ballMetric"]
    metric_names = [x_metric_name, y_metric_name, ball_metric_name]
    for entity, container_file, metric_dict in stream_of_entity_with_metrics(entities, metric_names,
                                                                                     verbose, skipLibraries,
                                                                                     regex_str_ignore_item,
                                                                                     regex_str_traverse_files,
                                                                                     regex_ignore_files):
        entity_name = entity.relname() if scope_name == "File" else entity.longname()
        annotations.append(entity_name)
        x_metric = metric_dict[x_metric_name]
        if x_metric is None:
            print("ERROR. Missing metric %s for X Axis" % x_metric)
            return
        x_values.append(x_metric)
        y_metric = metric_dict[y_metric_name]
        if y_metric is None:
            print("ERROR. Missing metric %s for Y Axis" % y_metric)
            return
        y_values.append(y_metric)
        ball_metric = metric_dict[ball_metric_name]
        if ball_metric is None:
            ball_metric = 0
        ball_values.append(min(ball_size_max,ball_size_rate * ball_metric + ball_size_min))
        color_values.append(hash(os.path.dirname(container_file.longname())))
    file_name = save_scatter(x_values, x_metric_name, y_values, y_metric_name, ball_values, ball_metric_name,
                             color_values, annotations, os.path.split(db.name())[-1], scope_name)
    print("Saved %s" % file_name)



def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version='Source Code Checker')
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srcscatter by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print(arguments)
    try:
        import understand
    except:
        print ("Can' find the Understand DLL. Use --dllDir=...")
        print ("Please set PYTHONPATH to point an Understand's C:/Program Files/SciTools/bin/pc-win64/python or equivalent")
        sys.exit(-1)
    try:
        db = understand.open(arguments["--in"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)

    scope_name = arguments["--scope"]
    if scope_name == "File":
        regex_str_ignore_item = arguments["--regexIgnoreFiles"]
        entityQuery = arguments["--fileQuery"]
    elif scope_name == "Class":
        regex_str_ignore_item = arguments["--regexIgnoreClasses"]
        entityQuery = arguments["--classQuery"]
    else:
        regex_str_ignore_item = arguments["--regexIgnoreRoutines"]
        entityQuery = arguments["--routineQuery"]

    print("Processing %s" % db.name())
    end_time = datetime.datetime.now()
    scatter_plot(db, arguments, entityQuery, regex_str_ignore_item, scope_name)
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")
    db.close()

if __name__ == '__main__':
    main()
