"""Source Code Diff Plot

Usage:
  srcdiffplot   --before=<inputUDB> --after=<inputUDB> \r\n \
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
                [--ballSize=<ballSize>] \r\n \
                [--minChange=<minChange>] \r\n \
                [--showMeanMedian] \r\n \
                [--verbose]

Options:
  --before=<inputUDB>                           File path to a UDB with the "before" state of your sources
  --after=<inputUDB>                            File path to a UDB with the "after" state of your sources
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win64/python]
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
  --ballSize=<ballSize>                         Size of the ball (circles) in the plots [Default: 40]
  --minChange=<minChange>                       Minimum change in metric value to be considered for the plot [Default: 1]
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -m, --showMeanMedian                          If you want to show circles for mean (blue), median (yellow), stdev (cyan) [default: false]

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
from utilities.utils import stream_of_entity_with_metrics, save_scatter, save_kiviat


def plot_diff_file_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--fileMetrics"], cmdline_arguments["--fileQuery"], cmdline_arguments.get("--regexIgnoreFiles", None), "File")

def plot_diff_class_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--classMetrics"], cmdline_arguments["--classQuery"], cmdline_arguments.get("--regexIgnoreClasses", None), "Class")

def plot_diff_routine_metrics (db_before, db_after, cmdline_arguments):
    return plot_diff_generic_metrics(db_before, db_after, cmdline_arguments, cmdline_arguments["--routineMetrics"], cmdline_arguments["--routineQuery"], cmdline_arguments.get("--regexIgnoreRoutines", None), "Routine")


def prune_unchanged (before_after, diff_tag):
    return {name:metrics_by_before_after_tag for name, metrics_by_before_after_tag in before_after.items() if diff_tag in metrics_by_before_after_tag}

def _compute_dict_diff (dict_a, dict_b, skip_zeroes = False):
    result = {}
    for key_a, value_a in dict_a.items():
        value_b = dict_b.get(key_a, 0)
        delta = value_b - value_a
        if skip_zeroes and delta == 0:
            continue
        result[key_a] = delta
    for key_b, value_b in dict_b.items():
        if key_b not in dict_a: # new metric, was not present in the file
            result[key_b] = value_b
    return result

def populate_diffs(before_after_by_ent_name, tag_before, tag_after, tag_diff, prune_before_after = False):
    for file_path, dict_before_after in before_after_by_ent_name.items():
        metrics_before = dict_before_after.get(tag_before, None)
        if metrics_before is None: # new entity, no "before" state
            continue
        if prune_before_after:
            del dict_before_after[tag_before]
        metrics_after = dict_before_after.get(tag_after, None)
        if metrics_after is None: # deleted entity, no "after" state
            continue
        if prune_before_after:
            del dict_before_after[tag_after]
        if metrics_before == metrics_after: # no diff at all
            continue
        dict_before_after[tag_diff] = _compute_dict_diff(metrics_before, metrics_after, skip_zeroes=prune_before_after)

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

def compute_metrics_diff (db_before, db_after, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name, prune_before_after = True):
    before_after_by_entity_name = compute_metrics_before_after(db_before, db_after, cmdline_arguments, metrics_as_string, entityQuery, regex_str_ignore_item, scope_name)
    populate_diffs(before_after_by_entity_name, "before", "after", "diff", prune_before_after = prune_before_after)
    return prune_unchanged(before_after_by_entity_name,"diff")

def collect_values (before_after_by_entity_name, tag, metric_name):
    result = []
    for entity_name, entity_props in before_after_by_entity_name.items():
        result.append(entity_props.get(tag, {}).get(metric_name, 0))
    return result

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
    sum_of_diffs_per_metric = []
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
        sum_before = sum(all_before)
        sum_after = sum (all_after)
        sum_of_diffs_per_metric.append(sum_after - sum_before)

    return [metric_names, sum_of_diffs_per_metric]
    # fig1 = plt.figure(figsize=(6, 6))
    # max_range = (min(sum_of_diffs_per_metric), max(sum_of_diffs_per_metric))
    # radar = ComplexRadar(fig1, metric_names, [max_range for i in range(len(metric_names))])
    # radar.plot(sum_of_diffs_per_metric)
    # radar.fill(sum_of_diffs_per_metric, alpha=0.2)
    # plt.show()


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
    all_metric_names = []
    all_metric_values = []

    metric_names, metric_diffs = plot_diff_file_metrics(db_before, db_after, arguments)
    all_metric_names.extend(["File:" + name for name in metric_names])
    all_metric_values.extend(metric_diffs)

    metric_names, metric_diffs = plot_diff_class_metrics(db_before, db_after, arguments)
    all_metric_names.extend(["Class:" + name for name in metric_names])
    all_metric_values.extend(metric_diffs)

    metric_names, metric_diffs = plot_diff_routine_metrics(db_before, db_after, arguments)
    all_metric_names.extend(["Routine:" + name for name in metric_names])
    all_metric_values.extend(metric_diffs)

    file_name = os.path.split(db_before.name())[-1] + "-" + os.path.split(db_after.name())[-1] + "-kiviat.png"
    save_kiviat(all_metric_names, all_metric_values, file_name, "Sum of deltas of all metrics")

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