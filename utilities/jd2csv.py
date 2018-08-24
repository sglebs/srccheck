"""Converts XMLs from JDepend to a CSV, to be used by srchistplot and srcinstplot".

Usage:
  jd2csv   [--in=<inputXML>] [--outputCSV=<outputCSV>]

Options:
  --in=<inputXML>               Input XML file path. [default: jdepend.xml]
  --outputCSV=<outputCSV>       Output CSV file path with the jdepend metrics [default: instability.csv]


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""

import xml.etree.ElementTree as ET
import datetime
import csv
from docopt import docopt
import math
from math import sqrt
from utilities import VERSION


def jdepend_to_csv (xml_path, csv_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    csv_file = open(csv_path, 'w')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Component", "Efferent Coupling", "Afferent Coupling", "Instability", "Classes", "Abstract Classes", "Distance", "Normalized Distance", "Distance Percentage"])
    sqrt2 = sqrt(2.0)
    for java_package in root.findall("Packages")[0].findall("Package"):
        name = java_package.attrib["name"]
        stats = java_package.findall("Stats")
        if len(stats) == 1:
            stats = stats[0]
            afferent_coupling = stats.find('Ca').text
            efferent_coupling = stats.find('Ce').text
            instability = float(stats.find('I').text)
            distance = float(stats.find('D').text)
            abstractness = float(stats.find('A').text)
            total_classes = stats.find('TotalClasses').text
            abstract_classes = stats.find('AbstractClasses').text
            normalized_distance = abs(abstractness + instability - 1)
            distance = normalized_distance / sqrt2
            distance_as_percentage = int(math.trunc(100.0 * normalized_distance))
            csv_writer.writerow([name, afferent_coupling, efferent_coupling, instability, total_classes, abstract_classes, distance, normalized_distance, distance_as_percentage])
    csv_file.close()

def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== jdepend to CSV by Marcio Marchini: marcio@BetterDeveloper.net ==========")
    print(arguments)
    jdepend_to_csv (arguments["--in"], arguments["--outputCSV"] )
    print("")
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("--------------------------------------------------")


if __name__ == '__main__':
    main()