"""Source Code OO Instability X Abstractness Plot.

Usage:
  srcinstplot   --in=<inputCSV> \r\n \
                [--outputDir=<path to dir where to save files>] \r\n \
                [--nameColumn=<anInteger>] \r\n \
                [--sizeColumn=<columnName>] \r\n \
                [--complexityColumn=<columnName>] \r\n \
                [--abstractnessColumn=<columnName>] \r\n \
                [--instabilityColumn=<columnName>] \r\n \
                [--ballSizeMin=<ballSizeMin>] \r\n \
                [--ballSizeMax=<ballSizeMax>] \r\n \
                [--ballSizeRate=<ballSizeRate>]



Options:
    --in=<inputCSV>                     Input CSV file path.
    --abstractnessColumn=<columnName>   Name of the column in the CSV with the Abstractness values. [default: Abstractness]
    --instabilityColumn=<columnName>    Name of the column in the CSV with the Imstability values. [default: Instability]
    --nameColumn=<columnName>           Name of the column in the CSV with the component/package names. [default: Component]
    --sizeColumn=<columnName>           Name of the column in the CSV with the component/package sizes. [default: CountLineCode]
    --complexityColumn=<columnName>     Name of the column in the CSV with the component/package complexity. [default: SumCyclomaticModified]
    --ballSizeMin=<ballSizeMin>         Minimum size of the ball (when the metric is zero). [Default: 20]
    --ballSizeMax=<ballSizeMax>         Maximum size of the ball [Default: 5000]
    --ballSizeRate=<ballSizeRate>       Rate at which the ball size grows per unit of the metric. [Default: 0.1]
    --outputDir=<path>                  Where files should be generated. [default: .]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import datetime
import os
import csv
from docopt import docopt
from utilities.utils import save_abstractness_x_instability_scatter
from utilities import VERSION

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
            abstractness = float(row.get(abstractnessColumn,0))
            instability = float(row.get(instabilityColumn,0))
            x_values.append(abstractness)
            y_values.append(instability)
            annotations.append('<font color="DarkSlateBlue">%s<br />%s=%i <br /> %s=%i</font>' % (
                row[nameColumn], sizeColumn, int(row.get(sizeColumn, 0)),
                complexityColumn, int(row.get(complexityColumn, 0))))
            ball_values.append(min(ball_size_max, ball_size_rate * int(row.get(sizeColumn,0)) + ball_size_min))
            color_values.append(int(row.get(complexityColumn,0)))
    output_dir = cmdline_arguments["--outputDir"]
    file_prefix = "%s%s%s" % (output_dir, os.sep, os.path.split(inputCSV)[-1])
    file_name = save_abstractness_x_instability_scatter(x_values, abstractnessColumn, y_values, instabilityColumn, ball_values, sizeColumn,
                                                        color_values, complexityColumn, annotations, file_prefix, "Component")
    print("Saved %s" % file_name)


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
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
