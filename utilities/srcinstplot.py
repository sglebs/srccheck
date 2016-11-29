"""Source Code OO Instability X Abstractness Plot.

Usage:
  srcinstplot   --in=<inputCSV> \r\n \
                [--nameColumn=<anInteger>] \r\n \
                [--sizeColumn=<anInteger>] \r\n \
                [--complexityColumn=<anInteger>] \r\n \
                [--abstractnessColumn=<anInteger>] \r\n \
                [--instabilityColumn=<anInteger>] \r\n \
                [--ballSizeMin=<ballSizeMin>] \r\n \
                [--ballSizeMax=<ballSizeMax>] \r\n \
                [--ballSizeRate=<ballSizeRate>]


Options:
    --in=<inputCSV>                     Input CSV file path.
    --abstractnessColumn=<columnName>   Name of the column in the CSV with the Abstractness values. [default: Abstractness]
    --instabilityColumn=<columnName>    Name of the column in the CSV with the Imstability values. [default: Instability]
    --nameColumn=<columnName>           Name of the column in the CSV with the component/package names. [default: Component]
    --sizeColumn=<columnName>           Name of the column in the CSV with the component/package sizes. [default: Size]
    --complexityColumn=<columnName>     Name of the column in the CSV with the component/package complexity. [default: Complexity]
    --ballSizeMin=<ballSizeMin>         Minimum size of the ball (when the metric is zero). [Default: 20]
    --ballSizeMax=<ballSizeMax>         Maximum size of the ball [Default: 5000]
    --ballSizeRate=<ballSizeRate>       Rate at which the ball size grows per unit of the metric. [Default: 0.1]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import os
import csv
from docopt import docopt
from utilities.utils import save_normalized_scatter

def scatter_plot (cmdline_arguments):
    inputCSV = cmdline_arguments["--in"]
    abstractnessColumn = cmdline_arguments["--abstractnessColumn"]
    instabilityColumn = cmdline_arguments["--instabilityColumn"]
    nameColumn = cmdline_arguments["--nameColumn"]
    sizeColumn = cmdline_arguments["--sizeColumn"]
    complexityColumn = cmdline_arguments["--complexityColumn"]
    ball_size_min = float(cmdline_arguments["--ballSizeMin"])
    ball_size_max = float(cmdline_arguments["--ballSizeMax"])
    ball_size_rate = float(cmdline_arguments["--ballSizeRate"])
    annotations = []
    x_values = []
    y_values = []
    ball_values = []
    color_values = []
    with open(inputCSV, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            annotations.append("%s (LOC=%i, McCabe=%i)" % (row[nameColumn],int(row[sizeColumn]),int(row[complexityColumn])))
            x_values.append(float(row[abstractnessColumn]))
            y_values.append(float(row[instabilityColumn]))
            ball_values.append(min(ball_size_max, ball_size_rate * int(row[sizeColumn]) + ball_size_min))

            color_values.append(int(row[complexityColumn]))
    file_name = save_normalized_scatter(x_values, abstractnessColumn, y_values, instabilityColumn, ball_values, "LOC",
                             color_values, annotations, os.path.split(inputCSV)[-1], "Component")
    print("Saved %s" % file_name)


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version='Source Code OO Instability Plot')
    print("\r\n====== srcinstplot by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print("Processing %s" % arguments["--in"])
    scatter_plot(arguments)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time - start_time))
    print("--------------------------------------------------")

if __name__ == '__main__':
    main()
