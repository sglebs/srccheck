"""Csv Stats Scatter Plot.

Usage:
  csvscatterplot    --in=<inputCSV> \r\n \
                   [--outputDir=<path to dir where to save files>] \r\n \
                   [--xMetric=<columnName>] \r\n \
                   [--yMetric=<columnName>] \r\n \
                   [--ballMetric=<columnName>] \r\n \
                   [--entityNames=<columnName>] \r\n \
                   [--colors=<columnName>] \r\n \
                   [--ballSizeMin=<aNumber>] \r\n \
                   [--ballSizeMax=<aNumber>] \r\n \
                   [--ballSizeRate=<aNumber>] \r\n \


Options:
  --in=<inputCSV>             Input CSV file path. [default: instability.csv]
  --xMetric=<columnName>      Name of the column in the CSV for the x axis [default: Efferent Coupling]
  --yMetric=<columnName>      Name of the column in the CSV for the y axis [default: Afferent Coupling]
  --ballMetric=<columnName>   Name of the column in the CSV for the ball sizes [default: CountLineCode]
  --ballSizeMin=<aNumber>     Minimum size of each ball drawn [default: 40]
  --ballSizeMax=<aNumber>     Maximum size of each ball drawn [default: 4000]
  --ballSizeRate=<aNumber>    Rate of growth of the ball for unit of growth of ballMetric [default: 10]
  --entityNames=<columnName>  Name of the column in the CSV for names in the circles [default: Component]
  --colors=<columnName>       Name of the column in the CSV for colors of the circles.
  --outputDir=<path>          Where files should be generated. [default: .]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import os
from docopt import docopt
from utilities.utils import stream_of_entity_with_metrics, save_scatter
from utilities import VERSION
import csv

def scatter_plot (cmdline_arguments,
                  x_metric_name,
                  y_metric_name,
                  ball_metric_name,
                  entity_column_name,
                  colors_column_name,
                  ball_size_min,
                  ball_size_max,
                  ball_size_rate):

    annotations = []
    x_values = []
    y_values = []
    ball_values = []
    color_values = []
    inputCSV = cmdline_arguments["--in"]
    with open(inputCSV, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            x_metric_value = float(row.get(x_metric_name,0))
            y_metric_value = float(row.get(y_metric_name,0))
            ball_metric_value = float(row.get(ball_metric_name,0))
            entity_name = row.get(entity_column_name,0)
            annotations.append(entity_name)
            x_values.append(x_metric_value)
            y_values.append(y_metric_value)
            ball_values.append(min(ball_size_max,ball_size_rate * ball_metric_value + ball_size_min))
            color_values.append(0 if colors_column_name == "" else hash(row.get(colors_column_name,0)))  # 0 for backwards compatibility
    output_dir = cmdline_arguments["--outputDir"]
    file_prefix = "%s%s%s" % (output_dir, os.sep, "csv")
    file_name = save_scatter(x_values, x_metric_name, y_values, y_metric_name, ball_values, ball_metric_name,
                             color_values, entity_column_name, annotations, file_prefix, "")
    print("Saved %s" % file_name)
    return True


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== csvscatterplot @ https://github.com/sglebs/srccheck ==========")
    print("Processing %s" % arguments["--in"])
    ok = scatter_plot(arguments,
                      arguments["--xMetric"],
                      arguments["--yMetric"],
                      arguments["--ballMetric"],
                      arguments["--entityNames"],
                      arguments.get("--colors", ""),  # for backwards compatibility on invocation
                      float(arguments["--ballSizeMin"]),
                      float(arguments["--ballSizeMax"]),
                      float(arguments["--ballSizeRate"]),
                      )
    if not ok:
        print("WARNING/SKIPPING: Could not create plot")
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")


if __name__ == '__main__':
    main()
