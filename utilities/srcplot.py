"""Source Code Stats Plot.

Usage:
  srcplot       --in=<inputUDB> \r\n \
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
                [--skipZeroes]


Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win64/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse[default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --fileMetrics=<maxFileMetrics>                A CSV containing file metric names you want to plot [default: CountLineCode,CountDeclFunction,CountDeclClass]
  --classMetrics=<classMetrics>                 A CSV containing class metric names you want to plot [default: CountDeclMethod,PercentLackOfCohesion,MaxInheritanceTree]
  --routineMetrics=<maxClassMetrics>            A CSV containing routine metric names you want to plot [default: CountLineCode,CountParams,CyclomaticStrict]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -l, --logarithmic                             If you want logarithmic y scale. [default: false]
  -z, --skipZeroes                              If you want to skip datapoints which are zero[default: false]

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
import os
import sys

import matplotlib.pyplot as plt
from docopt import docopt
from utilities.utils import stream_of_entity_with_metric
import statistics

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
                                                                                             cmdline_arguments,
                                                                                             skip_zeroes=skip_zeroes):
                yield metric_value

        metric_values_as_list = [value for value in metric_values()]
        max_value = max(metric_values_as_list) if len(metric_values_as_list)>0 else 0
        #bin_count = max (10, int (20 * math.log(abs(1+max_value),10)))
        plt.figure() # new one, or they will be mixed
        n, bins, patches = plt.hist(metric_values_as_list, "doane", facecolor='green', alpha=0.75)
        plt.xlabel(metric)
        plt.ylabel('Value')
        plt.title("%s %s (total of %i in %i bins)" % (scope_name, metric, len(metric_values_as_list), len(bins)))
        plt.grid(True)
        try:
            plt.axvline(statistics.mean(metric_values_as_list), color='b', linestyle='dashed', linewidth=2)
            plt.axvline(statistics.median(metric_values_as_list), color='r', linestyle='dashed', linewidth=2)
        except statistics.StatisticsError as se:
            pass
        if bool(cmdline_arguments["--logarithmic"]):
            plt.yscale('symlog', basey=10, linthreshy=10, subsy=[2, 3, 4, 5, 6, 7, 8, 9]) # http://stackoverflow.com/questions/17952279/logarithmic-y-axis-bins-in-python
        filename = "%s-%s-%s.png" % (os.path.split(db.name())[-1], scope_name,metric)
        plt.savefig(filename, dpi=72)
        print ("Saved %s" % filename)
        #plt.show()


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version='Source Code Checker')
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srcplot by Marcio Marchini: marcio@BetterDeveloper.net ==========")
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