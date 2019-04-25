"""CSV KALOI (Keep a Lid On It).

Usage:
  csvkaloi      --in=<inputCSV> \r\n \
                [--maxMetrics=<maxMetrics>]\r\n \
                [--columnWithItemName=<aName>]\r\n \
                [--showHighest]  \r\n \
                [--adaptive]

Options:
  --in=<inputCSV>                     Input CSV file path. [default: instability.csv]
  --maxMetrics=<maxPrjMetrics>        A JSON dictionary containing max values for the CSV-contained metrics you want to limit. [default: {"MEDIAN:Distance Percentage":10}]
  --columnWithItemName=<aName>        The name of the CSV column where the element names are, for printing purposes. [default: Component]
  -s, --showHighest                   If you want to show (print) the highest valued elements (highest metric) even if not a violation. [default: false]
  -a, --adaptive                      If you want csvkaloi to be adaptive and update the input json files with current max values


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""


# Publishing in SONAR: http://docs.codehaus.org/pages/viewpage.action?pageId=229743270

import datetime
import json
import os.path
import statistics
import sys
import csv
from docopt import docopt

from utilities import VERSION

STATS_LAMBDAS = {"AVG": statistics.mean,
                 "MEDIAN": statistics.median,
                 "MEDIANHIGH": statistics.median_high,
                 "MEDIANLOW": statistics.median_low,
                 "MEDIANGROUPED": statistics.median_grouped,
                 "MODE": statistics.mode,
                 "STDEV": statistics.pstdev,
                 "VARIANCE": statistics.pvariance}

def metric_name_for_sorting(metric_name):
    if ":" not in metric_name:
        return metric_name
    else:
        parts = metric_name.split(":")
        return parts[-1] + parts[0]

def process_csv_metrics (cmdline_arguments, max_values_allowed_by_metric):
    violation_count = 0
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
        adjusted_metric = metric
        if metric.count(':') == 1: #fix for #42 - can have only 1 :
            lambda_name, adjusted_metric = metric.split(":")
            lambda_stats = STATS_LAMBDAS.get(lambda_name.upper().strip(), None)

        def metric_values(): # generator of a stream of float values, to be consumed by the stats functions
            with open(cmdline_arguments.get("--in", False)) as csvfile:
                reader = csv.DictReader(csvfile)
                column_with_name = cmdline_arguments.get("--columnWithItemName", False)
                for row in reader:
                    yield [row[column_with_name], float(row[adjusted_metric])]

        if lambda_stats is None:  # regular, not stats
            max_value_found = -1
            entity_with_max_value_found = None
            has_stats_counterpart = (":%s" % metric) in "".join(sorted_metrics)
            for entity, metric_value in metric_values():
                if has_stats_counterpart: # fix for #22 - cache values for stats
                    all_values.append(metric_value)
                if metric_value > highest_values_found_by_metric.get(metric, -1): # even a zero we want to tag as a max
                    highest_values_found_by_metric[metric] = metric_value
                max_allowed = max_values_allowed_by_metric[metric]
                if metric_value > max_allowed: # we found a violation
                    violation_count = violation_count + 1
                    print("'%s' violated '%s' threshold: %f > %f"% (entity, metric, metric_value, max_allowed))
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
                    print("'%s' violated '%s' threshold: %f > %f"% (entity_with_max_value_found, metric, max_value_found, max_allowed_value))
                    #lambda_to_print(entity_with_max_value_found, metric, max_value_found, container_file=container_file) # prints the max found, which may be a violator or not
                    print("...........................................")
            last_processed_metric = metric  # fix for #21, to reuse values
            last_all_values = all_values  # fix for #21, to reuse values
            last_max_value_found = max_value_found
        else: # stats, compute on the whole population
            if adjusted_metric == last_processed_metric: # fix for #21 - reuses values, thanks to sorting we know teh pure metric must have come just before
                all_values = last_all_values
                max_value_found = last_max_value_found
            else:
                all_values = [value for entity, value in metric_values()]
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
                print("STATS threshold violation for '%s': %f > %f" % (metric, stats_value, max_allowed_value))
            else:
                if bool(cmdline_arguments["--showHighest"]):
                    print("...........................................")
                    print("INFO(STATS): %s = %s (violation threshold is %s):" % (metric, stats_value, max_allowed_value))
                    print("...........................................")
            #if mean is not None:
            #    stats_cache[metric] = {"AVG": mean, "MEDIAN": median, "STDEV": pstdev} # fix for #22 - used cached value for stats
            #if verbose:
            #    print("Saved %s" % file_name)

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


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== csvkaloi @ https://github.com/sglebs/srccheck ==========")
    print(arguments)

    adaptive = arguments.get("--adaptive", False)
    print("\r\n====== CSV KALOI Metrics (%s) ==========" % arguments.get("--maxMetrics", False))
    max_metrics = load_metrics_thresholds(arguments.get("--maxMetrics", False))
    print(max_metrics)
    print("\r\n====== CSV Metrics that failed the filters  ===========")
    [total_violation_count , tracked_metrics ] = process_csv_metrics(arguments, max_metrics)
    if adaptive:
        write_metrics_thresholds(arguments.get("--maxMetrics", False), tracked_metrics)

    print ("")
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time-start_time))
    print("Violations: %i" % total_violation_count)
    print("--------------------------------------------------")
    sys.exit(total_violation_count)

if __name__ == '__main__':
    main()