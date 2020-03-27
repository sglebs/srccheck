"""XML KALOI (Keep a Lid On It).

Usage:
  xmlkaloi      --in=<inputXML> [--maxMetrics=<maxPrjMetrics>] [--xpathForEachMetric=<xpaths>] [--adaptive]

Options:
  --in=<inputXML>                     Input XML file path. [default: summary.xml]
  --maxMetrics=<maxPrjMetrics>        A JSON dictionary containing max values for the metrics you want to limit. [default: {"XS":0.15, "FAT": 0.15, "TANGLE": 0.10}]
  --xpathForEachMetric=<xpaths>       xpaths to fetch each of the current values provided in maxMetrics. [default: {"XS":"model/hiview/xs-config/xs-summary/summary@average-xs","FAT":"model/hiview/stats/codemap_stats@complexity_percentage","TANGLE":"model/hiview/stats/codemap_stats@tanglicity_percentage"}]
  -a, --adaptive                      If you want xmlkaloi to be adaptive and update the input json files with current max values


Author:
  Marcio Marchini (marcio@BetterDeveloper.net)

"""


# Publishing in SONAR: http://docs.codehaus.org/pages/viewpage.action?pageId=229743270

import datetime
import json
import os.path
import sys
from docopt import docopt
from utilities import VERSION
import xml.etree.ElementTree as ET
import re

def load_xml(xml_path):
    xml_root = None
    if os.path.isfile(xml_path):
        with open(xml_path) as xml:
            file_contents = xml.read()
            file_contents_workaround = re.sub("<\\?xml.*\\?>", "", file_contents) # ET workaround. Must remove XML decl or nothing works
            xml_root = ET.fromstring(file_contents_workaround)
    return xml_root


def load_json(max_metrics_json_or_path):
    if os.path.isfile(max_metrics_json_or_path):
        with open(max_metrics_json_or_path) as max_metrics_json:
            return json.load(max_metrics_json)
    else:
        return json.loads(max_metrics_json_or_path)

def write_json(json_path, new_max_metrics):
    if os.path.isfile(json_path):
        with open(json_path, "w") as json_file:
            json.dump(new_max_metrics, json_file, sort_keys=True)

def process_xml_metrics(max_metrics, metrics_with_xpaths, xml):
    violation_count = 0
    current_metrics = dict()
    violators = list()
    for metric_name, xpath in metrics_with_xpaths.items():
        xpath_parts = xpath.split("@")  # ET workaround. No attrib support in xpath
        element_xpath = xpath_parts[0]
        current_element = xml.find(element_xpath)
        if current_element is None:
            violation_count += 1
            violators.append(metric_name)
            continue
        max_metric_value_allowed = max_metrics.get(metric_name, None)
        if max_metric_value_allowed is None:
            violation_count += 1
            violators.append(metric_name)
            continue
        #
        if len(xpath_parts)==1:
            current_metric_value = current_element.text
        else:
            xpath_attrib = xpath_parts[1]
            current_metric_value = current_element.attrib.get(xpath_attrib, "")
        current_metrics[metric_name] = current_metric_value
        try:
            if float(current_metric_value) > float(max_metric_value_allowed):
                violation_count += 1
                violators.append(metric_name)
        except ValueError:
            violation_count += 1
            violators.append(metric_name)
    return [violation_count, current_metrics, violators]


def main():
    start_time = datetime.datetime.now()
    arguments = docopt(__doc__, version=VERSION)
    print("\r\n====== xmlkaloi @ https://github.com/sglebs/srccheck ==========")
    print(arguments)

    adaptive = arguments.get("--adaptive", False)
    print("\r\n====== XML KALOI Metrics (%s) ==========" % arguments.get("--maxMetrics", False))
    max_metrics = load_json(arguments.get("--maxMetrics", False))
    xpaths = load_json(arguments.get("--xpathForEachMetric", False))
    xml = load_xml(arguments.get("--in", ""))
    print(xpaths)
    print("\r\n====== XML Metrics that failed the filters  ===========")
    [total_violation_count, current_values, violators] = process_xml_metrics(max_metrics, xpaths, xml)
    print ("%s  (Current values: %s)" % (violators, current_values))
    if adaptive:
        write_json(arguments.get("--maxMetrics", False), current_values)
    end_time = datetime.datetime.now()
    print("\r\n--------------------------------------------------")
    print("Started : %s" % str(start_time))
    print("Finished: %s" % str(end_time))
    print("Total: %s" % str(end_time-start_time))
    print("--------------------------------------------------")
    sys.exit(total_violation_count)

if __name__ == '__main__':
    main()