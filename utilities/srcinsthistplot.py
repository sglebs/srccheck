"""Source Code OO Instability X Abstractness Histogram Plot (Distance from Mean).

Usage:
  srcinsthistplot   --in=<inputCSV> \r\n \
                [--normalizedDistanceColumn=<columnName>] \r\n \
                [--showMeanMedian]


Options:
    --in=<inputCSV>                     Input CSV file path. [default: instability.csv]
    --normalizedDistanceColumn=<columnName>   Name of the column in the CSV with the Normalized Distance values. [default: Normalized Distance]
    -m, --showMeanMedian                If you want to show dotted lines for mean (blue) and median (red) [default: false]


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
    normalizedDistanceColumn = cmdline_arguments["--normalizedDistanceColumn"]
    distances_as_percentages = []
    with open(inputCSV, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            normalizedDistance = float(row.get(normalizedDistanceColumn,0))
            distance_as_percentage = int (math.trunc(100.0 * normalizedDistance))
            distances_as_percentages.append(distance_as_percentage)

    max_value = max(distances_as_percentages) if len(distances_as_percentages) > 0 else 0
    file_name, mean, median, pstdev = save_histogram(bool(cmdline_arguments["--showMeanMedian"]),
                                                     False, # not logarythmic
                                                     os.path.split(cmdline_arguments["--in"])[-1],
                                                     max_value,
                                                     "distance from AxI mean sequence",
                                                     distances_as_percentages,
                                                     "Components")
    print("Saved %s" % file_name)


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== srcinsthistplot by Marcio Marchini: marcio@BetterDeveloper.net ==========")
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
