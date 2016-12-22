"""Source Code Diff Plot

Usage:
  srcdiffplot   --before=<inputUDB> --after=<inputUDB> \r\n \
                [--dllDir=<dllDir>]\r\n \
                [--skipLibs=<skipLibs>]\r\n \
                [--fileQuery=<fileQuery>]\r\n \
                [--classQuery=<classQuery>]\r\n \
                [--routineQuery=<routineQuery>]\r\n \
                [--prjMetrics=<fileMetrics>]\r\n \
                [--fileMetrics=<fileMetrics>]\r\n \
                [--classMetrics=<classMetrics>]\r\n \
                [--routineMetrics=<routineMetrics>]\r\n \
                [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                [--ballSize=<ballSize>] \r\n \
                [--minChange=<minChange>] \r\n \
                [--showMeanMedian] \r\n \
                [--skipPrjMetrics=<skipPrjMetrics>]\r\n \
                [--verbose]

Options:
  --before=<inputUDB>                           File path to a UDB with the "before" state of your sources
  --after=<inputUDB>                            File path to a UDB with the "after" state of your sources
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win64/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse[default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --prjMetrics=<prjMetrics>                     A CSV containing project metric names you want to plot [default: CountDeclFile,CountDeclClass,CountLineCode,CountPath,CountStmt,AvgLineCode,Cyclomatic,AvgCyclomatic,MaxCyclomatic,SumCyclomatic,Essential,MaxEssential,CountDeclMethod,MaxNesting]
  --fileMetrics=<fileMetrics>                   A CSV containing file metric names you want to plot [default: CountLineCode,CountDeclFunction,CountDeclClass]
  --classMetrics=<classMetrics>                 A CSV containing class metric names you want to plot [default: CountDeclMethod,PercentLackOfCohesion,MaxInheritanceTree,CountClassCoupled]
  --routineMetrics=<routineMetrics>             A CSV containing routine metric names you want to plot [default: CountLineCode,CountParams,CyclomaticStrict]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  --ballSize=<ballSize>                         Size of the ball (circles) in the plots [Default: 40]
  --minChange=<minChange>                       Minimum change in metric value to be considered for the plot [Default: 1]
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -m, --showMeanMedian                          If you want to show circles for mean (blue), median (yellow), stdev (cyan) [default: false]
  --skipPrjMetrics=<skipPrjMetrics>             Skip these project metrics (CSV of values) when printing/processing all prj metrics (for speed) [default: CountDeclMethodAll,MaxInheritanceTree,Essential,MaxEssential,MaxEssentialKnots,MaxNesting]

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
import statistics
import sys

from docopt import docopt

from utilities import VERSION
from utilities.utils import stream_of_entity_with_metrics, save_scatter, save_kiviat_with_values_and_thresholds


def plot_diff_file_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--fileMetrics"], cmdline_arguments["--fileQuery"], cmdline_arguments.get("--regexIgnoreFiles", None), "File")

def plot_diff_class_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--classMetrics"], cmdline_arguments["--classQuery"], cmdline_arguments.get("--regexIgnoreClasses", None), "Class")

def plot_diff_routine_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--routineMetrics"], cmdline_arguments["--routineQuery"], cmdline_arguments.get("--regexIgnoreRoutines", None), "Routine")

def _name_of_entity(entity, scope):
    if scope == "File":
        return entity.relname()
    else:
        return entity.longname()

def compute_metrics_before_after (db_before, db_after, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    verbose = cmdline_arguments["--verbose"]
    metrics = [metric.strip() for metric in metrics_as_string.split(",")]
    before_after_by_entity_name = {}
    for entity, container_file, metric_dict in \
            stream_of_entity_with_metrics(db_before.ents(entityQuery), metrics,
                                          verbose, skipLibraries,
                                         regex_str_ignore_item,
                                         regex_str_traverse_files,
                                         regex_ignore_files):
        attribs = {}
        attribs["before"] = metric_dict
        before_after_by_entity_name[_name_of_entity(entity,scope_name)] = attribs
    for entity, container_file, metric_dict in \
            stream_of_entity_with_metrics(db_after.ents(entityQuery), metrics,
                                          verbose, skipLibraries,
                                         regex_str_ignore_item,
                                         regex_str_traverse_files,
                                         regex_ignore_files):
        attribs = before_after_by_entity_name.get(_name_of_entity(entity,scope_name),{}) # maybe it is already there... maybe not
        attribs["after"] = metric_dict
        before_after_by_entity_name[_name_of_entity(entity,scope_name)] = attribs
    return before_after_by_entity_name


def collect_values_that_changed (before_after_by_entity_name, tag_before, tag_after, metric_name, minimal_change):
    results_before = []
    results_after = []
    names = []
    for entity_name, entity_props in before_after_by_entity_name.items():
        value_before = entity_props.get(tag_before, {}).get(metric_name, 0)
        value_before = 0 if value_before is None else value_before
        value_after = entity_props.get(tag_after, {}).get(metric_name, 0)
        value_after = 0 if value_after is None else value_after
        if abs(value_before - value_after) >= minimal_change:
            results_before.append(value_before)
            results_after.append(value_after)
            names.append(entity_name)
    return results_before, results_after, names


def add_stats(all_before, all_after, entity_names, colors):
    avg_before = statistics.mean(all_before)
    avg_after = statistics.mean(all_after)
    all_before.append(avg_before)
    all_after.append(avg_after)
    entity_names.append("(AVG)")
    colors.append("b")
    median_before = statistics.median(all_before)
    median_after = statistics.median(all_after)
    all_before.append(median_before)
    all_after.append(median_after)
    entity_names.append("(MEDIAN)")
    colors.append("y")
    stdev_before = statistics.pstdev(all_before,avg_before)
    stdev_after = statistics.pstdev(all_after,avg_after)
    all_before.append(stdev_before)
    all_after.append(stdev_after)
    entity_names.append("(STDEV)")
    colors.append("c")


def plot_diff_generic_metrics (db_before, db_after, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name):
    before_after_by_entity_name = compute_metrics_before_after(db_before, db_after, cmdline_arguments,
                                                               metrics_as_string, entityQuery, regex_str_ignore_item,
                                                               scope_name)

    metric_names = [metric.strip() for metric in metrics_as_string.split(",")]
    for i, metric_name in enumerate(metric_names):
        all_before, all_after, entity_names = collect_values_that_changed(before_after_by_entity_name, "before", "after", metric_name, int(cmdline_arguments["--minChange"]))
        if len(all_before) > 0:
            colors = ["r" if y > x else "g" for x,y in zip(all_before,all_after)]
            if bool(cmdline_arguments["--showMeanMedian"]):
                add_stats(all_before, all_after, entity_names, colors)
            file_name = save_scatter(all_before, "Before",
                                     all_after, "After",
                                     int(cmdline_arguments["--ballSize"]), metric_name,
                                     colors, "Increased/Decreased",
                                     entity_names,
                                     os.path.split(db_before.name())[-1] + "-" + os.path.split(db_after.name())[-1] + "-" + metric_name,
                                     scope_name,
                                     show_diagonal=True,
                                     format="html")
            print("Saved %s" % file_name)
    return before_after_by_entity_name

def print_growth_rates(all_metric_names, all_growth_rates):
    print("\nMetric Growth Rate in Project")
    print ("--------------------------------------")
    for name, growth_rate in zip(all_metric_names, all_growth_rates):
        print("%s:\t%f" % (name.replace("\n", " "), growth_rate))


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srcdiffplot by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print(arguments)
    try:
        import understand
    except:
        print ("Can' find the Understand DLL. Use --dllDir=...")
        print ("Please set PYTHONPATH to point an Understand's C:/Program Files/SciTools/bin/pc-win64/python or equivalent")
        sys.exit(-1)
    try:
        db_before = understand.open(arguments["--before"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)
    try:
        db_after = understand.open(arguments["--after"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)

    print("Processing %s and %s" % (db_before.name(), db_after.name()))

    for plot_lambda in [plot_diff_file_metrics, plot_diff_class_metrics,plot_diff_routine_metrics]:
        plot_lambda(db_before, db_after, arguments)


    prj_metric_names = [metric.strip() for metric in arguments["--prjMetrics"].split(",")]
    prj_metrics_before = db_before.metric(prj_metric_names)
    prj_metrics_after = db_after.metric(prj_metric_names)
    all_metric_names = []
    all_metric_values_before = []
    all_metric_values_after = []
    all_growth_rates = []
    for prj_metric_name in sorted(prj_metric_names):
        all_metric_names.append(prj_metric_name)
        metric_value_before = prj_metrics_before.get(prj_metric_name,0)
        all_metric_values_before.append(metric_value_before)
        metric_value_after = prj_metrics_after.get(prj_metric_name,0)
        all_metric_values_after.append(metric_value_after)
        if metric_value_before == 0:
            all_growth_rates.append(float("inf"))
        else:
            all_growth_rates.append(metric_value_after/metric_value_before)
    file_name = os.path.split(db_before.name())[-1] + "-" + os.path.split(db_after.name())[-1] + "-diff-kiviat.png"
    saved_file_name = save_kiviat_with_values_and_thresholds(all_metric_names, all_metric_values_after, all_metric_values_before, file_name, "Prj Metrics", thresholdslabel="before", valueslabel="after")
    if saved_file_name is not None:
        print("Saved %s" % saved_file_name)
    print_growth_rates(all_metric_names, all_growth_rates)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")
    db_before.close()
    db_after.close()

if __name__ == '__main__':
    main()