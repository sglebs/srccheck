"""Source Code Histogram Plot.

Usage:
  srchistplot   --in=<inputUDB> \r\n \
                [--outputDir=<path to dir where to save files>] \r\n \
                [--dllDir=<dllDir>]\r\n \
                [--skipLibs=<skipLibs>]\r\n \
                [--fileQuery=<fileQuery>]\r\n \
                [--classQuery=<classQuery>]\r\n \
                [--routineQuery=<routineQuery>]\r\n \
                [--fileMetrics=<fileMetrics>]\r\n \
                [--classMetrics=<classMetrics>]\r\n \
                [--routineMetrics=<routineMetrics>]\r\n \
                [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                [--verbose]  \r\n \
                [--logarithmic]  \r\n \
                [--skipZeroes]  \r\n \
                [--showMeanMedian]


Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the Understand bin and DLLs.[default: C:/Program Files/SciTools/bin/pc-win64]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse[default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --fileMetrics=<maxFileMetrics>                A CSV containing file metric names you want to plot [default: CountLineCode,CountDeclFunction,CountDeclClass]
  --classMetrics=<classMetrics>                 A CSV containing class metric names you want to plot [default: CountDeclMethod,PercentLackOfCohesion,MaxInheritanceTree,CountClassCoupled]
  --routineMetrics=<maxClassMetrics>            A CSV containing routine metric names you want to plot [default: CountLineCode,CountParams,CyclomaticStrict]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -l, --logarithmic                             If you want logarithmic y scale. [default: false]
  -z, --skipZeroes                              If you want to skip datapoints which are zero[default: false]
  -m, --showMeanMedian                          If you want to show dotted lines for mean (blue) and median (red) [default: false]
  --outputDir=<path>                            Where files should be generated. [default: .]

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
from utilities.utils import stream_of_entity_with_metric, save_histogram, insert_understand_in_path
from utilities import VERSION


def plot_hist_file_metrics (db, cmdline_arguments):
    plot_hist_generic_metrics(db, cmdline_arguments, cmdline_arguments["--fileMetrics"], cmdline_arguments["--fileQuery"], cmdline_arguments.get("--regexIgnoreFiles", None), "File")

def plot_hist_class_metrics (db, cmdline_arguments):
    plot_hist_generic_metrics(db, cmdline_arguments, cmdline_arguments["--classMetrics"], cmdline_arguments["--classQuery"], cmdline_arguments.get("--regexIgnoreClasses", None), "Class")

def plot_hist_routine_metrics (db, cmdline_arguments):
    plot_hist_generic_metrics(db, cmdline_arguments, cmdline_arguments["--routineMetrics"], cmdline_arguments["--routineQuery"], cmdline_arguments.get("--regexIgnoreRoutines", None), "Routine")

def plot_hist_generic_metrics (db, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    entities = db.ents(entityQuery)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    skip_zeroes = cmdline_arguments.get("--skipZeroes", False)
    verbose = cmdline_arguments["--verbose"]
    metrics = [metric.strip() for metric in metrics_as_string.split(",")]
    for metric in sorted(metrics):
        local_metric = metric
        def metric_values(): # generator of a stream of float values, to be consumed by the stats functions
            for entity, container_file, metric, metric_value in stream_of_entity_with_metric(entities, local_metric,
                                                                                             verbose, skipLibraries,
                                                                                             regex_str_ignore_item,
                                                                                             regex_str_traverse_files,
                                                                                             regex_ignore_files,
                                                                                             skip_zeroes=skip_zeroes):
                yield metric_value

        metric_values_as_list = [value for value in metric_values()]
        max_value = max(metric_values_as_list) if len(metric_values_as_list)>0 else 0
        #bin_count = max (10, int (20 * math.log(abs(1+max_value),10)))
        output_dir = cmdline_arguments["--outputDir"]
        file_prefix = "%s%s%s" % (output_dir, os.sep, os.path.split(db.name())[-1])
        file_name, mean, median, pstdev = save_histogram(bool(cmdline_arguments["--showMeanMedian"]),
                                   bool(cmdline_arguments["--logarithmic"]),
                                   file_prefix,
                                   max_value,
                                   metric,
                                   metric_values_as_list,
                                   scope_name)
        print("Saved %s" % file_name)


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    insert_understand_in_path(arguments["--dllDir"])
    print ("\r\n====== srchistplot @ https://github.com/sglebs/srccheck ==========")
    print(arguments)
    try:
        import understand
    except:
        print ("Can' find the Understand DLL. Use --dllDir=...")
        print ("Please set PYTHONPATH to point an Understand's C:/Program Files/SciTools/bin/pc-win64 or equivalent")
        sys.exit(-1)
    try:
        db = understand.open(arguments["--in"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)

    print("Processing %s" % db.name())
    plot_hist_file_metrics(db, arguments)
    plot_hist_class_metrics(db, arguments)
    plot_hist_routine_metrics(db, arguments)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")
    db.close()

if __name__ == '__main__':
    main()