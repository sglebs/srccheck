"""Source Code Stats Scatter Plot.

Usage:
  srcscatterplot    --in=<inputUDB> \r\n \
                    [--outputDir=<path to dir where to save files>] \r\n \
                    [--dllDir=<dllDir>]\r\n \
                    [--skipLibs=<skipLibs>]\r\n \
                    [--fileQuery=<fileQuery>]\r\n \
                    [--classQuery=<classQuery>]\r\n \
                    [--routineQuery=<routineQuery>]\r\n \
                    [--regexTraverseFiles=<regexTraverseFiles>] \r\n \
                    [--regexIgnoreFiles=<regexIgnoreFiles>] \r\n \
                    [--regexIgnoreClasses=<regexIgnoreClasses>] \r\n \
                    [--regexIgnoreRoutines=<regexIgnoreRoutines>] \r\n \
                    [--config=<jsonOrJsonFile>]\r\n \
                    [--verbose]

Options:
  --in=<inputUDB>                               Input UDB file path.
  --dllDir=<dllDir>                             Path to the dir with the Understand bin and DLLs.[default: C:/Program Files/SciTools/bin/pc-win64]
  --skipLibs=<skipLibs>                         false for full analysis. true if you want to skip libraries you import. [default: true]
  --fileQuery=<fileQuery>                       Kinds of files you want to traverse [default: file ~Unknown ~Unresolved]
  --classQuery=<classQuery>                     Kinds of classes your language has. [default: class ~Unknown ~Unresolved, interface ~Unknown ~Unresolved]
  --routineQuery=<routineQuery>                 Kinds of routines your language has. [default: function ~Unknown ~Unresolved ~Predeclared ~Abstract,method ~Unknown ~Unresolved ~Predeclared ~Abstract,procedure ~Unknown ~Unresolved ~Predeclared ~Abstract,routine ~Unknown ~Unresolved ~Predeclared ~Abstract,classmethod ~Unknown ~Unresolved ~Predeclared ~Abstract]
  --regexTraverseFiles=<regexTraverseFiles>     A regex to filter files in / traverse. Defaults to all [default: .*]
  --regexIgnoreFiles=<regexIgnoreFiles>         A regex to filter files out
  --regexIgnoreClasses=<regexIgnoreClasses>     A regex to filter classes out
  --regexIgnoreRoutines=<regexIgnoreRoutines>   A regex to filter routines out
  --config=<jsonOrJsonFile>                     A json which configures the plots for the supported scopes (File, Class, Routine). [default: {"File":[{"xMetric":"CountLineCode", "yMetric":"MaxCyclomaticModified", "ballMetric":"MaxNesting"}], "Class":[{"xMetric":"CountLineCode", "yMetric":"CountClassCoupled", "ballMetric":"PercentLackOfCohesion"}], "Routine":[{"xMetric":"CountLineCode", "yMetric":"CyclomaticModified", "ballMetric":"MaxNesting"}]}]
  -v, --verbose                                 If you want lots of messages printed. [default: false]
  -z, --skipZeroes                              If you want to skip datapoints which are zero [default: false]
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
from utilities.utils import stream_of_entity_with_metrics, save_scatter, load_json, insert_understand_in_path
from utilities import VERSION

def load_config(config_json_or_path):
    try:
        return load_json(config_json_or_path)
    except:
        return {}


def scatter_plot (db, cmdline_arguments,
                  entityQuery,
                  regex_str_ignore_item,
                  scope_name,
                  x_metric_name,
                  y_metric_name,
                  ball_metric_name,
                  ball_size_min,
                  ball_size_max,
                  ball_size_rate,
                  x_metric_min_value=0.0,
                  y_metric_min_value=0.0,
                  ball_metric_min_value=0.0):
    regex_str_traverse_files = cmdline_arguments.get("--regexTraverseFiles", "*")
    regex_ignore_files = cmdline_arguments.get("--regexIgnoreFiles", None)
    entities = db.ents(entityQuery)
    skipLibraries = cmdline_arguments["--skipLibs"] == "true"
    verbose = cmdline_arguments["--verbose"]

    annotations = []
    x_values = []
    y_values = []
    ball_values = []
    color_values = []
    metric_names = [x_metric_name, y_metric_name, ball_metric_name]
    for entity, container_file, metric_dict in stream_of_entity_with_metrics(entities, metric_names,
                                                                                     verbose, skipLibraries,
                                                                                     regex_str_ignore_item,
                                                                                     regex_str_traverse_files,
                                                                                     regex_ignore_files):
        entity_name = entity.relname() if scope_name == "File" else entity.longname()
        x_metric_value = metric_dict[x_metric_name]
        if x_metric_value is None:
            print("ERROR. Missing metric %s for X Axis (entity=%s (%s), file=%s)" % (x_metric_name, entity.kindname(), entity_name, container_file))
            return False
        y_metric_value = metric_dict[y_metric_name]
        if y_metric_value is None:
            print("ERROR. Missing metric %s for Y Axis (entity=%s (%s), file=%s)" % (y_metric_name, entity.kindname(), entity_name, container_file))
            return False
        ball_metric_value = metric_dict[ball_metric_name]
        if ball_metric_value is None:
            ball_metric_value = 0
        if x_metric_value < float(x_metric_min_value) and y_metric_value < float(y_metric_min_value) and ball_metric_value < float(ball_metric_min_value):
            continue # fix for #59 - able to toss uninteresting elements out
        entity_name += ": "  + str(ball_metric_value)
        annotations.append(entity_name)
        x_values.append(x_metric_value)
        y_values.append(y_metric_value)
        ball_values.append(min(ball_size_max,ball_size_rate * ball_metric_value + ball_size_min))
        color_values.append(0 if container_file is None else hash(os.path.dirname(container_file.longname())))
    output_dir = cmdline_arguments["--outputDir"]
    file_prefix = "%s%s%s" % (output_dir, os.sep, os.path.split(db.name())[-1])
    file_name = save_scatter(x_values, x_metric_name, y_values, y_metric_name, ball_values, ball_metric_name,
                             color_values, "directory", annotations, file_prefix, scope_name)
    print("Saved %s" % file_name)
    return True


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    insert_understand_in_path(arguments["--dllDir"])
    print ("\r\n====== srcscatterplot @ https://github.com/sglebs/srccheck ==========")
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
    end_time = datetime.datetime.now()
    config = load_config(arguments["--config"])
    if not isinstance(config, dict):
        print ("Malformed config value.")
        exit(1)
    query_by_scope_name = {"file": arguments["--fileQuery"], "class": arguments["--classQuery"], "routine": arguments["--routineQuery"]}
    regex_by_scope_name = {"file": arguments["--regexIgnoreFiles"], "class": arguments["--regexIgnoreClasses"], "routine": arguments["--regexIgnoreRoutines"]}
    for scope_name, scope_configs in config.items():
        if scope_name.lower() not in query_by_scope_name:
            print("WARNING/SKIPPING:Unsupported scope %s" % scope_name)
            continue
        if not isinstance(scope_configs, list):
            print("WARNING/SKIPPING: Malformed configs for scope %s" % scope_name)
            continue
        for scope_config in scope_configs:
            if not isinstance(scope_config, dict):
                print("WARNING/SKIPPING: Malformed config for scope %s" % scope_name)
                continue
            ok = scatter_plot(db,
                          arguments,
                          query_by_scope_name[scope_name.lower()],
                          regex_by_scope_name[scope_name.lower()],
                          scope_name,
                          scope_config.get("xMetric", "CountLineCode"),
                          scope_config.get("yMetric", "AvgCyclomaticModified"),
                          scope_config.get("ballMetric", "MaxNesting"),
                          float(scope_config.get("ballSizeMin", 40)),
                          float(scope_config.get("ballSizeMax", 4000)),
                          float(scope_config.get("ballSizeRate", 10)),
                          x_metric_min_value=float(scope_config.get("xMetricMinValue", 0.0)),
                          y_metric_min_value=float(scope_config.get("yMetricMinValue", 0.0)),
                          ball_metric_min_value=float(scope_config.get("ballMetricMinValue", 0.0))
                        )
            if not ok:
                print("WARNING/SKIPPING: Could not create plot for scope %s with config %s" % (scope_name, scope_config))
                continue
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")
    db.close()


if __name__ == '__main__':
    main()
