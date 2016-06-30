"""Source Code Checker.

Usage:
  srccheck       --in=<inputUDB> \r\n \
                [--dllDir=<dllDir>]\r\n \
                [--skipLibs=<skipLibs>]\r\n \
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
                [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                [--verbose]

Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the DLL to the Understand Python SDK.[default: C:/Program Files/SciTools/bin/pc-win32/python]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function,method,procedure,routine,classmethod]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  --maxPrjMetrics=<maxPrjMetrics>               A JSON dictionary containing max values for the Prj metrics you want to limit. These will also be output in the CSV. [default: {"AvgCyclomatic":4,"MaxNesting":5}]
  --maxFileMetrics=<maxFileMetrics>             A JSON dictionary containing max values for File metrics you want to limit. These will also be output in the CSV. [default: {"CountLineCode":3000,"CountDeclFunction":50,"CountDeclClass":10,"CountDeclModule":5}]
  --maxClassMetrics=<maxClassMetrics>           A JSON dictionary containing max values for Class metrics you want to limit. These will also be output in the CSV. [default: {"CountDeclMethod":30,"PercentLackOfCohesion":50, "MaxInheritanceTree":6}]
  --maxRoutineMetrics=<maxClassMetrics>         A JSON dictionary containing max values for Class metrics you want to limit. These will also be output in the CSV. [default: {"CountLineCode":100,"CountParams":20,"CyclomaticStrict":12}]
  --outputCSV=<outputCSV>                       Output CSV file path with the current metrics listed at --maxPrjMetrics. Useful with the Jenkins/Plot plugin [default: srcmetrics.csv]
  --sonarURL=<sonarURL>                         URL to post metrics into Sonar [default: http://localhost:9000/api/manual_measures]
  --sonarPrj=<sonarPrj>                         Name of Project in Sonar [default: #]
  --sonarUser=<sonarUser>                       User name for Sonar authentication [default: admin]
  --sonarPass=<sonarPass>                       Password for Sonar authentication [default: admin]
  --verbose                                     If you want lots of messages printed. [default: false]

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

import sys
import json
import datetime
import re

from docopt import docopt
import requests


def _print_routine_violation(func, metric_name, metric_value):
    print("%s\t%s\t%s" % (metric_name, metric_value, func.longname()))

def _print_file_violation(file, metric_name, metric_value):
    print("%s\t%s\t%s " % (metric_name, metric_value, file.longname()))

def _print_class_violation(a_class, metric_name, metric_value):
    print("%s\t%s\t%s " % (metric_name, metric_value, a_class.longname()))

def _print_metric_violation(metric_name, metric_value, max_value):
    print ("%s:\t%s>%s" % (metric_name, metric_value, max_value))

def print_prj_metrics (db, cmdline_arguments):
    metrics = db.metric(db.metrics())
    for k,v in sorted(metrics.items()):
        print (k,"=",v)


def process_prj_metrics (db, cmdline_arguments):
    max_metrics_json = cmdline_arguments["--maxPrjMetrics"]
    max_metrics = {}
    violation_count = 0
    verbose = cmdline_arguments["--verbose"]
    try:
        max_metrics = json.loads(max_metrics_json)
    except:
        max_metrics = {}
    if not isinstance(max_metrics, dict):
        max_metrics = {}
    if len(max_metrics) == 0: # No metrics passed in
        print ("*** EMPTY PRJ Max Metrics. JSON error? (%s)" % max_metrics_json)
        return [0, {}]
    metrics = db.metric(db.metrics())
    max_metrics_found = {}
    for metric,max_value in max_metrics.items():
        cur_value = metrics.get(metric,None)
        if cur_value is not None:
            max_metrics_found [metric] = cur_value
            if cur_value > max_value:
                _print_metric_violation (metric, cur_value, max_value)
                violation_count = violation_count + 1
    return [violation_count, max_metrics_found]


def passes_regex_filter (entity, regex_filter, cmdline_arguments):
    if regex_filter is None:
        return True
    try:
        return re.search(regex_filter, entity.longname()) is None
    except:
        verbose = cmdline_arguments["--verbose"]
        if verbose:
            print ("REGEX/EXCEPTION: %s" % regex_filter)
        return False

def process_generic_metrics (db, cmdline_arguments, jsonCmdLineParam, entityQuery, lambda_to_print, regex__str_ignore_item):
    max_metrics_json = cmdline_arguments[jsonCmdLineParam]
    max_metrics = {}
    violation_count = 0
    entities = db.ents(entityQuery)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    verbose = cmdline_arguments["--verbose"]
    try:
        max_metrics = json.loads(max_metrics_json)
    except:
        max_metrics = {}
    if not isinstance(max_metrics, dict):
        max_metrics = {}
    if len(max_metrics) == 0: # No metrics passed in
        print ("*** EMPTY Metrics. JSON error? (%s)" % max_metrics_json)
        return [0, {}]
    max_metrics_found = {}
    for entity in entities:
        library_name = entity.library()
        if library_name is not "" and skipLibraries:
        #            if verbose:
        #                print ("LIBRARY/SKIP: %s" % entity.longname())
            continue
        if not passes_regex_filter(entity, regex__str_ignore_item, cmdline_arguments):
            if verbose:
                print ("REGEX/SKIP: %s" % entity.longname())
            continue
        else:
            for metric,max_value in max_metrics.items():
                if metric == "CountParams":
                    metric_value = len (entity.ents("Define", "Parameter"))
                else:
                    metric_dict = entity.metric((metric,))
                    metric_value = metric_dict.get(metric,0) # the call returns a dict
                if metric_value is None:
                    metric_value = 0
                if metric_value > max_metrics_found.get(metric, -1): # even a zero we want to tag as a max
                    max_metrics_found[metric] = metric_value
                max_allowed = max_metrics[metric]
                if metric_value > max_allowed:
                    violation_count = violation_count + 1
                    lambda_to_print(entity, metric, metric_value)
    return [violation_count, max_metrics_found]

def process_file_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxFileMetrics", "files", _print_file_violation, cmdline_arguments.get("--regexIgnoreFiles", None))

def process_class_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxClassMetrics", cmdline_arguments["--classQuery"], _print_class_violation, cmdline_arguments.get("--regexIgnoreClasses", None))

def process_routine_metrics (db, cmdline_arguments):
    return process_generic_metrics(db,cmdline_arguments,"--maxRoutineMetrics", cmdline_arguments["--routineQuery"], _print_routine_violation, cmdline_arguments.get("--regexIgnoreRoutines", None))

def append_dict_with_key_prefix (dict_to_grow, dict_to_append, prefix):
    for k,v in dict_to_append.items():
        dict_to_grow["%s %s" % (prefix, k)] = v


def _generate_csv (cmdline_arguments, cur_tracked_metrics_for_csv):
    csv_path = cmdline_arguments["--outputCSV"]
    try:
        file = open(csv_path, "w")
        sep = ""
        for metric_name,metric_value in sorted(cur_tracked_metrics_for_csv.items()):
            file.write(sep)
            file.write(metric_name)
            sep = ","
        file.write("\n")
        sep = ""
        for metric_name,metric_value in sorted(cur_tracked_metrics_for_csv.items()):
            file.write(sep)
            file.write(str(metric_value))
            sep = ","
        file.write("\n")
        file.close()
        print ("+++ Metrics saved to %s" % csv_path)
    except:
        print ("\n*** Problems creating CSV file %s" % csv_path)


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
    arguments = docopt(__doc__, version='Source Code Checker')
    sys.path.append(arguments["--dllDir"]) # add the dir with the DLL to interop with understand
    print ("\r\n====== srccheck by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print(arguments)
    try:
        import understand
    except:
        print ("Can' find the Understand DLL. Use --dllDir=...")
        print ("Please set PYTHONPATH to point an Understand's C:/Program Files/SciTools/bin/pc-win32/python or equivalent")
        sys.exit(-1)
    try:
        db = understand.open(arguments["--in"])
    except understand.UnderstandError as exc:
        print ("Error opening input file: %s" % exc)
        sys.exit(-2)
    print ("\r\n====== PRJ Metrics (%s) ==========" % db.name())
    print_prj_metrics(db, arguments)
    print ("")
    print ("\r\n====== Prj Metrics that failed the filters  ===========")
    [total_violation_count , prj_tracked_metrics] = process_prj_metrics(db, arguments)
    print ("")
    print ("\r\n====== File Metrics that failed the filters  ===========")
    [violation_count, file_tracked_metrics] = process_file_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    print ("")
    print ("\r\n====== Class Metrics that failed the filters  ==========")
    [violation_count, class_tracked_metrics] = process_class_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    print ("")
    print ("\r\n====== Routine Metrics that failed the filters ==========")
    [violation_count, routine_tracked_metrics] = process_routine_metrics(db, arguments)
    total_violation_count = total_violation_count + violation_count
    print ("")
    print ("\r\n====== Publishing selected metrics  ===========")
    tracked_metrics = {}
    append_dict_with_key_prefix (tracked_metrics, prj_tracked_metrics, "Prj")
    append_dict_with_key_prefix (tracked_metrics, file_tracked_metrics, "File")
    append_dict_with_key_prefix (tracked_metrics, class_tracked_metrics, "Class")
    append_dict_with_key_prefix (tracked_metrics, routine_tracked_metrics, "Routine")
    _generate_csv(arguments, tracked_metrics)
    _post_to_sonar(arguments, tracked_metrics)
    print ("")
    end_time = datetime.datetime.now()
    print ("\r\n--------------------------------------------------")
    print ("Started : %s" % str(start_time))
    print ("Finished: %s" % str(end_time))
    print ("Violations: %i" % total_violation_count)
    print ("--------------------------------------------------")
    db.close()
    sys.exit(total_violation_count)

if __name__ == '__main__':
    main()