"""Source Code Checker.

Usage:
  srccheck       --in=<inputUDB> \r\n \
                [--dllDir=<dllDir>]\r\n \
                [--skipLibs=<skipLibs>]\r\n \
                [--fileQuery=<fileQuery>]\r\n \
                [--classQuery=<classQuery>]\r\n \
                [--routineQuery=<routineQuery>]\r\n \
                [--maxPrjMetrics=<maxPrjMetrics>]\r\n \
                [--maxFileMetrics=<maxFileMetrics>]\r\n \
                [--maxClassMetrics=<maxClassMetrics>]\r\n \
                [--maxRoutineMetrics=<maxRoutineMetrics>]\r\n \
                [--outputCSV=<outputCSV>] \r\n \
                [--sonarURL=<sonarURL>] \r\n \
                [--sonarPrj=<sonarPrj>] \r\n \
                [--sonarUser=<sonarUser>] \r\n \
                [--sonarPass=<sonarPass>] \r\n \
                [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                [--verbose] \r\n \
                [--skipPrjMetrics=<skipPrjMetrics>]\r\n \
                [--skipZeroes] \r\n \
                [--adaptive] \r\n \
                [--logarithmic]  \r\n \
                [--showMeanMedian]  \r\n \
                [--showHighest]  \r\n \
                [--histograms]


Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win64/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse[default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved,method ~Unknown ~Unresolved,procedure ~Unknown ~Unresolved,routine ~Unknown ~Unresolved,classmethod ~Unknown ~Unresolved]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  --maxPrjMetrics=<maxPrjMetrics>               A JSON dictionary containing max values for the Prj metrics you want to limit. These will also be output in the CSV. [default: {"AvgCyclomatic":4,"MaxNesting":5}]
  --maxFileMetrics=<maxFileMetrics>             A JSON dictionary containing max values for File metrics you want to limit. These will also be output in the CSV. [default: {"CountLineCode":3000,"CountDeclFunction":50,"CountDeclClass":10,"CountDeclModule":5}]
  --maxClassMetrics=<maxClassMetrics>           A JSON dictionary containing max values for Class metrics you want to limit. These will also be output in the CSV. [default: {"CountDeclMethod":30,"AVG:PercentLackOfCohesion":50, "MaxInheritanceTree":6, "CountClassCoupled": 250}]
  --maxRoutineMetrics=<maxClassMetrics>         A JSON dictionary containing max values for Class metrics you want to limit. These will also be output in the CSV. [default: {"CountLineCode":100,"CountParams":20,"CyclomaticStrict":12}]
  --outputCSV=<outputCSV>                       Output CSV file path with the current metrics listed at --maxPrjMetrics. Useful with the Jenkins/Plot plugin [default: srcmetrics.csv]
  --sonarURL=<sonarURL>                         URL to post metrics into Sonar [default: http://localhost:9000/api/manual_measures]
  --sonarPrj=<sonarPrj>                         Name of Project in Sonar [default: #]
  --sonarUser=<sonarUser>                       User name for Sonar authentication [default: admin]
  --sonarPass=<sonarPass>                       Password for Sonar authentication [default: admin]
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -z, --skipZeroes                              If you want to skip datapoints which are zero[default: false]
  -a, --adaptive                                If you want srccheck to be adaptive and update the input json files with current max values
  -H, --histograms                              If you want srccheck to save histograms, just like srchistplot does
  -l, --logarithmic                             If you want logarithmic y scale. [default: false]
  -m, --showMeanMedian                          If you want to show dotted lines for mean (blue) and median (red) [default: false]
  -s, --showHighest                             If you want to show (print) the highest valued elements (highest metric) even if not a violation. [default: false]
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


# https://github.com/docopt/docopt#readme
# http://www.py2exe.org/index.cgi/Tutorial
# For windows use py2exe http://www.logix4u.net/component/content/article/27-tutorials/44-how-to-create-windows-executable-exe-from-python-script
# For linux use pyinstaller http://www.pyinstaller.org
# For Mac use py2app http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html
# Multi-platform: http://cx-freeze.sourceforge.net
# Publishing in SONAR: http://docs.codehaus.org/pages/viewpage.action?pageId=229743270

import datetime
import json
import os.path
import statistics
import sys

import requests
from docopt import docopt
from utilities.utils import stream_of_entity_with_metric, save_histogram, save_csv
from utilities import VERSION

STATS_LAMBDAS = {"AVG": statistics.mean,
                 "MEDIAN": statistics.median,
                 "MEDIANHIGH": statistics.median_high,
                 "MEDIANLOW": statistics.median_low,
                 "MEDIANGROUPED": statistics.median_grouped,
                 "MODE": statistics.mode,
                 "STDEV": statistics.pstdev,
                 "VARIANCE": statistics.pvariance}

class DummyEntity:
    def longname(self):
        return ""

def _print_routine_violation(routine, metric_name, metric_value, container_file=None):
    print("%s\t%s\t%s%s" % (metric_name, metric_value, routine.longname(),
                            "" if container_file == None else "\t(in %s)" % container_file.longname()))

def _print_file_violation(file, metric_name, metric_value, container_file=None):
    print("%s\t%s\t%s " % (metric_name, metric_value, file.longname()))

def _print_class_violation(a_class, metric_name, metric_value, container_file=None):
    print("%s\t%s\t%s%s" % (metric_name, metric_value, a_class.longname(),
                            "" if container_file == None else "\t(in %s)" % container_file.longname()))

def _print_metric_violation(metric_name, metric_value, max_value):
    print ("%s:\t%s>%s" % (metric_name, metric_value, max_value))

def project_metrics(db, cmdline_arguments):
    skip_set = set(cmdline_arguments["--skipPrjMetrics"].split(","))
    all_metric_names = db.metrics()
    selected_metric_names = [metric for metric in all_metric_names if metric not in skip_set]
    return db.metric(selected_metric_names)

def print_prj_metrics (prj_metrics):
    for k,v in sorted(prj_metrics.items()):
        print(k,"=",v)


def process_prj_metrics (cmdline_arguments, prj_metrics):
    max_metrics_json = cmdline_arguments["--maxPrjMetrics"]
    max_metrics = {}
    violation_count = 0
    verbose = cmdline_arguments["--verbose"]
    try:
        max_metrics = load_metrics_thresholds(max_metrics_json)
    except Exception as ex:
        print("SEVERE WARNING loading json: %s" % ex)
        max_metrics = {}
    if not isinstance(max_metrics, dict):
        max_metrics = {}
    if len(max_metrics) == 0: # No metrics passed in
        print ("*** EMPTY PRJ Max Metrics. JSON error? (%s)" % max_metrics_json)
        return [0, {}]
    max_metrics_found = {}
    for metric,max_value in max_metrics.items():
        cur_value = prj_metrics.get(metric, None)
        if cur_value is not None:
            max_metrics_found [metric] = cur_value
            if cur_value > max_value:
                _print_metric_violation (metric, cur_value, max_value)
                violation_count = violation_count + 1
    return [violation_count, max_metrics_found]

def metric_name_for_sorting(metric_name):
    if ":" not in metric_name:
        return metric_name
    else:
        parts = metric_name.split(":")
        return parts[-1] + parts[0]

def process_generic_metrics (db, cmdline_arguments, jsonCmdLineParam, entityQuery, lambda_to_print, regex_str_ignore_item, scope_name):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    max_metrics_json = cmdline_arguments[jsonCmdLineParam]
    max_values_allowed_by_metric = {}
    violation_count = 0
    entities = db.ents(entityQuery)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    skip_zeroes = cmdline_arguments.get("--skipZeroes", False)
    verbose = cmdline_arguments["--verbose"]
    save_histograms = cmdline_arguments["--histograms"]
    try:
        max_values_allowed_by_metric = load_metrics_thresholds(max_metrics_json)
    except Exception as ex:
        print("SEVERE WARNING loading json: %s" % ex)
        max_values_allowed_by_metric = {}
    if not isinstance(max_values_allowed_by_metric, dict):
        max_values_allowed_by_metric = {}
    if len(max_values_allowed_by_metric) == 0: # No metrics passed in
        print ("*** EMPTY Metrics. JSON error? (%s)" % max_metrics_json)
        return [0, {}]
    highest_values_found_by_metric = {}
    last_processed_metric = "" # fix for #21, to reuse values
    last_all_values = [] # fix for #21, to reuse values
    last_max_value_found = -1
    stats_cache = {}  # fix for #22 - use cached value for stats
    sorted_metrics = sorted(max_values_allowed_by_metric.keys(), key=metric_name_for_sorting)
    for metric in sorted_metrics:
        max_allowed_value = max_values_allowed_by_metric[metric]
        all_values = [] # we may need to collect all values, if we are going to save a histogram
        lambda_stats = None
        if ":" in metric:
            lambda_name, adjusted_metric = metric.split(":")
            lambda_stats = STATS_LAMBDAS.get(lambda_name.upper().strip(), None)

        if lambda_stats is None:  # regular, not stats
            max_value_found = -1
            entity_with_max_value_found = None
            has_stats_counterpart = (":%s" % metric) in "".join(sorted_metrics)
            for entity, container_file, metric, metric_value in stream_of_entity_with_metric(entities, metric, verbose, skipLibraries, regex_str_ignore_item, regex_str_traverse_files, regex_ignore_files, skip_zeroes=skip_zeroes):
                if save_histograms or has_stats_counterpart: # fix for #22 - cache values for stats
                    all_values.append(metric_value)
                if metric_value > highest_values_found_by_metric.get(metric, -1): # even a zero we want to tag as a max
                    highest_values_found_by_metric[metric] = metric_value
                max_allowed = max_values_allowed_by_metric[metric]
                if metric_value > max_allowed: # we found a violation
                    violation_count = violation_count + 1
                    lambda_to_print(entity, metric, metric_value, container_file=container_file)
                if metric_value > max_value_found: # max found, which could be a violator or not
                    max_value_found = metric_value
                    entity_with_max_value_found = entity
            if entity_with_max_value_found is not None:
                if bool(cmdline_arguments["--showHighest"]):
                    print("...........................................")
                    kind = "violator"
                    if max_value_found <= max_allowed_value:
                        kind = "non violator"
                    print("INFO: HIGHEST %s %s found (violation threshold is %s):\t" % (metric, kind, max_allowed_value), end="")
                    lambda_to_print(entity_with_max_value_found, metric, max_value_found, container_file=container_file) # prints the max found, which may be a violator or not
                    print("...........................................")
            last_processed_metric = metric  # fix for #21, to reuse values
            last_all_values = all_values  # fix for #21, to reuse values
            last_max_value_found = max_value_found
        else: # stats, compute on the whole population
            def metric_values(): # generator of a stream of float values, to be consumed by the stats functions
                for entity, container_file, metric, metric_value in stream_of_entity_with_metric(entities, adjusted_metric,
                                                                                                 verbose, skipLibraries,
                                                                                                 regex_str_ignore_item,
                                                                                                 regex_str_traverse_files,
                                                                                                 regex_ignore_files,
                                                                                                 skip_zeroes=skip_zeroes):
                    yield metric_value

            if adjusted_metric == last_processed_metric: # fix for #21 - reuses values, thanks to sorting we know teh pure metric must have come just before
                all_values = last_all_values
                max_value_found = last_max_value_found
            else:
                all_values = [value for value in metric_values()]
                if save_histograms:
                    max_value_found = max(all_values) if len(all_values) > 0 else 0
                    last_max_value_found = max_value_found  # fix for #21, same as above
                last_processed_metric = adjusted_metric  # fix for 21. in case only stats functions are used, not the pure one.
                last_all_values = all_values  # fix for #21, same as above
            stats_value = stats_cache.get(adjusted_metric, {}).get(lambda_name, None) # fix for #22 - used cached value for stats
            if stats_value is None:
                try:
                    stats_value = lambda_stats(all_values)
                except statistics.StatisticsError as se:
                    print ("ERROR in %s: %s" % (metric, se))
                    continue

            highest_values_found_by_metric[metric] = stats_value
            if stats_value > max_allowed_value:  # we found a violation
                violation_count = violation_count + 1
                lambda_to_print(DummyEntity(), metric, stats_value)
            else:
                if bool(cmdline_arguments["--showHighest"]):
                    print("...........................................")
                    print("INFO(STATS): %s = %s (violation threshold is %s):" % (metric, stats_value, max_allowed_value))
                    print("...........................................")
        if save_histograms and len(all_values) > 0 and lambda_stats is None:
            file_name, mean, median, pstdev = save_histogram(bool(cmdline_arguments["--showMeanMedian"]),
                                       bool(cmdline_arguments["--logarithmic"]),
                                       os.path.split(db.name())[-1],
                                       max_value_found,
                                       metric,
                                       all_values,
                                       scope_name)
            if mean is not None:
                stats_cache[metric] = {"AVG": mean, "MEDIAN": median, "STDEV": pstdev} # fix for #22 - used cached value for stats
            if verbose:
                print("Saved %s" % file_name)

    return [violation_count, highest_values_found_by_metric]


def load_metrics_thresholds(max_metrics_json_or_path):
    if os.path.isfile(max_metrics_json_or_path):
        with open(max_metrics_json_or_path) as max_metrics_json:
            return json.load(max_metrics_json)
    else:
        return json.loads(max_metrics_json_or_path)

def write_metrics_thresholds(json_path, new_max_metrics):
    if os.path.isfile(json_path):
        original_thresholds = load_metrics_thresholds(json_path)
        for key, value in new_max_metrics.items():
            if value < original_thresholds[key]:
                original_thresholds[key] = value
        with open(json_path, "w") as json_file:
            json.dump(original_thresholds, json_file, sort_keys=True) # at this point, original_thresholds has been adapted

def process_file_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxFileMetrics", cmdline_arguments["--fileQuery"], _print_file_violation, cmdline_arguments.get("--regexIgnoreFiles", None), "File")

def process_class_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxClassMetrics", cmdline_arguments["--classQuery"], _print_class_violation, cmdline_arguments.get("--regexIgnoreClasses", None), "Class")

def process_routine_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxRoutineMetrics", cmdline_arguments["--routineQuery"], _print_routine_violation, cmdline_arguments.get("--regexIgnoreRoutines", None), "Routine")

def append_dict_with_key_prefix (dict_to_grow, dict_to_append, prefix):
    for k,v in dict_to_append.items():
        dict_to_grow["%s %s" % (prefix, k)] = v


def _post_to_sonar (cmdline_arguments, cur_tracked_metrics):
    TIMEOUT = 4
    sonar_url = cmdline_arguments["--sonarURL"]
    sonar_prj = cmdline_arguments["--sonarPrj"]
    sonar_user = cmdline_arguments["--sonarUser"]
    sonar_pass = cmdline_arguments["--sonarPass"]
    if sonar_prj == "#":
        print ("*** Skipping posting to Sonar (PRJ=%s)" % sonar_prj)
        return
    for metric, value in cur_tracked_metrics.items():
        rest_params = {}
        rest_params["resource"] = sonar_prj
        rest_params["metric"] = metric.lower().replace(" ", "_") # SONAR wants its key, which is lowercase
        rest_params["val"] = value
        try:
            response = requests.post(sonar_url, rest_params, timeout=TIMEOUT, auth=(sonar_user, sonar_pass))
            if response.status_code != 200:
                print ("*** Response error connecting to %s: %s" % (sonar_url, str(response.content)))
            else:
                print ("+++ Metric %s=%s posted to prj %s in %s (%s)" % (metric, value, sonar_prj, sonar_url, str(response.content)))
        except requests.exceptions.Timeout:
            print ("*** Timeout connecting to %s" % sonar_url)
            return
        except requests.exceptions.HTTPError:
            print ("*** HTTP Error connecting to %s" % sonar_url)
            return
        except requests.exceptions.ConnectionError:
            print ("*** Connection Error connecting to %s" % sonar_url)
            return

def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srccheck by Marcio Marchini: marcio@BetterDeveloper.net ==========")
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

    adaptive = arguments.get("--adaptive", False)
    print ("\r\n====== Project Metrics (%s) (%s) ==========" % (db.name(), db.language()[0]))
    prj_metrics = project_metrics(db, arguments)
    print_prj_metrics(prj_metrics)
    print ("")
    print ("\r\n====== Project Metrics that failed the filters  ===========")
    [total_violation_count , prj_tracked_metrics] = process_prj_metrics(arguments, prj_metrics)
    if adaptive:
        write_metrics_thresholds(arguments.get("--maxPrjMetrics", False), prj_tracked_metrics)
    print ("")
    print ("\r\n====== File Metrics that failed the filters  ===========")
    [violation_count, file_tracked_metrics] = process_file_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    if adaptive:
        write_metrics_thresholds(arguments.get("--maxFileMetrics"), file_tracked_metrics)
    print ("")
    print ("\r\n====== Class Metrics that failed the filters  ==========")
    [violation_count, class_tracked_metrics] = process_class_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    if adaptive:
        write_metrics_thresholds(arguments.get("--maxClassMetrics"), class_tracked_metrics)
    print ("")
    print ("\r\n====== Routine Metrics that failed the filters ==========")
    [violation_count, routine_tracked_metrics] = process_routine_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    if adaptive:
        write_metrics_thresholds(arguments.get("--maxRoutineMetrics"), routine_tracked_metrics)
    print ("")
    print ("\r\n====== Publishing selected metrics  ===========")
    tracked_metrics = {}
    append_dict_with_key_prefix (tracked_metrics, prj_tracked_metrics, "Prj")
    append_dict_with_key_prefix (tracked_metrics, file_tracked_metrics, "File")
    append_dict_with_key_prefix (tracked_metrics, class_tracked_metrics, "Class")
    append_dict_with_key_prefix (tracked_metrics, routine_tracked_metrics, "Routine")
    csv_ok = save_csv(arguments["--outputCSV"], tracked_metrics)
    if csv_ok:
        print("+++ Metrics saved to %s" % arguments["--outputCSV"])
    else:
        print ("\n*** Problems creating CSV file %s" % arguments["--outputCSV"])

    _post_to_sonar(arguments, tracked_metrics)
    print ("")
    end_time = datetime.datetime.now()
    print ("\r\n--------------------------------------------------")
    print ("Started : %s" % str(start_time))
    print ("Finished: %s" % str(end_time))
    print ("Total: %s" % str(end_time-start_time))
    print ("Violations: %i" % total_violation_count)
    print ("--------------------------------------------------")
    db.close()
    sys.exit(total_violation_count)

if __name__ == '__main__':
    main()