"""CSV Histogram Plot.

Usage:
  csvhistplot   --in=<inputCSV> \r\n \
                [--outputDir=<path to dir where to save files>] \r\n \
                [--histogramColumn=<columnName>] \r\n \
                [--logarithmic]  \r\n \
                [--showMeanMedian]


Options:
    --in=<inputCSV>                     Input CSV file path. [default: instability.csv]
    --histogramColumn=<columnName>      Name of the column in the CSV with the Normalized Distance values. [default: Distance Percentage]
    -m, --showMeanMedian                If you want to show dotted lines for mean (blue) and median (red) [default: false]
    -l, --logarithmic                   If you want logarithmic y scale. [default: false]
    --outputDir=<path>                  Where files should be generated. [default: .]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import os
import csv
from docopt import docopt
from utilities.utils import save_histogram
from utilities import VERSION
import math

SQRT2 = math.sqrt(2.0)

def hist_plot (cmdline_arguments):
    inputCSV = cmdline_arguments["--in"]
    histogram_column = cmdline_arguments["--histogramColumn"]
    data_values = []
    with open(inputCSV, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data_value = float(row.get(histogram_column,0))
            data_values.append(data_value)

    max_value = max(data_values) if len(data_values) > 0 else 0
    output_dir = cmdline_arguments["--outputDir"]
    file_prefix = "%s%s%s" % (output_dir, os.sep, os.path.split(cmdline_arguments["--in"])[-1])
    file_name, mean, median, pstdev = save_histogram(bool(cmdline_arguments["--showMeanMedian"]),
                                                     bool(cmdline_arguments["--logarithmic"]),
                                                     file_prefix,
                                                     max_value,
                                                     histogram_column,
                                                     data_values,
                                                     "")
    print("Saved %s" % file_name)


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== csvhistplot @ https://github.com/sglebs/srccheck ==========")
    print("Processing %s" % arguments["--in"])
    hist_plot(arguments)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")

if __name__ == '__main__':
    main()
