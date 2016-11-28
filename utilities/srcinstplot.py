"""Source Code OO Instability X Abstractness Plot.

Usage:
  srcinstplot   --in=<inputCSV> \r\n \
                [--namesColumn=<anInteger>] \r\n \
                [--abstractnessColumn=<anInteger>] \r\n \
                [--instabilityColumn=<anInteger>]

Options:
    --in=<inputCSV>                     Input CSV file path.
    --abstractnessColumn=<columnName>   Name of the column in the CSV with the Abstractness values. [default: Abstractness]
    --instabilityColumn=<columnName>    Name of the column in the CSV with the Imstability values. [default: Instability]
    --namesColumn=<columnName>          Name of the column in the CSV with the component/package names. [default: Component]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import csv
from docopt import docopt
from utilities.utils import save_scatter

def scatter_plot (cmdline_arguments):
    inputCSV = cmdline_arguments["--in"]
    abstractnessColumn = cmdline_arguments["--abstractnessColumn"]
    instabilityColumn = cmdline_arguments["--instabilityColumn"]
    namesColumn = cmdline_arguments["--namesColumn"]
    annotations = []
    x_values = []
    y_values = []
    ball_values = []
    color_values = []
    with open(inputCSV, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            annotations.append(row[namesColumn])
            x_values.append(row[abstractnessColumn])
            y_values.append(row[instabilityColumn])
            ball_values.append(40)
            color_values.append (hash(row[namesColumn]))
    file_name = save_scatter(x_values, abstractnessColumn, y_values, instabilityColumn, ball_values, "Constant",
                             color_values, annotations, "OO", "Component")
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
