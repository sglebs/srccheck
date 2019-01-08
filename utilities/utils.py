import os.path
import re
import statistics
import json
import requests
import urllib.request
from matplotlib import use as backend_use
backend_use('Agg') # fixes #32 - change backend to simple one, BEFORE any other import.
from matplotlib import pyplot as plt
plt.ioff()  # fixes #32 - no need for an interactive backend
import mpld3
from utilities.complex_radar import ComplexRadar

class ClickSendToBack(mpld3.plugins.PluginBase):
    """Plugin for sending element to the back. Combined https://mpld3.github.io/notebooks/custom_plugins.html and http://bl.ocks.org/eesur/4e0a69d57d3bfc8a82c2"""

    JAVASCRIPT = """
    d3.selection.prototype.moveToBack = function() {
        return this.each(function() {
            var firstChild = this.parentNode.firstChild;
            if (firstChild) {
                this.parentNode.insertBefore(this, firstChild);
            }
        });
    };
    mpld3.register_plugin("clicksendtoback", ClickSendToBackPlugin);
    ClickSendToBackPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    ClickSendToBackPlugin.prototype.constructor = ClickSendToBackPlugin;
    ClickSendToBackPlugin.prototype.requiredProps = ["id"];
    function ClickSendToBackPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    ClickSendToBackPlugin.prototype.draw = function(){
        var obj = mpld3.get_element(this.props.id);
        obj.elements().on("mousedown",
                          function(d, i){d3.select(this).moveToBack();});
    }
    """

    def __init__(self, points):
        self.dict_ = {"type": "clicksendtoback",
                      "id": mpld3.utils.get_id(points)}


def stream_of_entity_with_metrics (entities, metrics, verbose, skipLibraries,regex_str_ignore_item, regex_str_traverse_files, regex_ignore_files ):
    for entity in entities:
        library_name = entity.library()
        if library_name is not "" and skipLibraries:
            #            if verbose:
            #                print ("LIBRARY/SKIP: %s" % entity.longname())
            continue
        if matches_regex(entity, regex_str_ignore_item, verbose):
            if verbose:
                print("ENTITY REGEX/SKIP: %s" % entity.longname())
            continue
        ent_kind = entity.kindname()
        if str.find(ent_kind, "Unknown") >= 0 or str.find(ent_kind, "Unresolved") >= 0:
            continue
        container_file = None
        if str.find(ent_kind, "File") >= 0:
            container_file = entity
        else:
            container_ref = entity.ref("definein, declarein")
            container_file = container_ref.file() if container_ref is not None else None
        if container_file is None:
            if verbose:
                print("WARNING: no container file: %s. NOT SKIPPING to be safe" % entity.longname())
        else:
            if not matches_regex(container_file, regex_str_traverse_files, verbose):
                if verbose:
                    print("SKIP due to file traverse regex non-match: %s" % container_file.longname())
                continue
            if matches_regex(container_file, regex_ignore_files, verbose):
                if verbose:
                    print("SKIP due to file ignore regex match: %s" % container_file.longname())
                continue
        # real work
        metric_dict = entity.metric(metrics)
        if "CountParams" in metric_dict:
            metric_dict ["CountParams"] = len(entity.ents("Define", "Parameter ~Catch"))
        if "CountDeclMethodNonStub" in metric_dict:
            extra_metrics = entity.metric(["CountDeclMethod" , "CountDeclPropertyAuto"])
            metric_dict["CountDeclMethodNonStub"] = max(0,extra_metrics.get("CountDeclMethod",0) - (2 * extra_metrics.get("CountDeclPropertyAuto",0))) # note we can't always multiply by 2 (not always a getter and setter) but this is the best we can do
        yield [entity, container_file, metric_dict]



def stream_of_entity_with_metric (entities, metric, verbose, skipLibraries,regex_str_ignore_item, regex_str_traverse_files, regex_ignore_files, skip_zeroes = False ):
    for entity, container_file, metric_dict in stream_of_entity_with_metrics(entities,
                                                                                      (metric,),
                                                                                     verbose, skipLibraries,
                                                                                     regex_str_ignore_item,
                                                                                     regex_str_traverse_files,
                                                                                     regex_ignore_files):
        metric_value = metric_dict.get(metric, 0)  # the call returns a dict
        if metric_value is None:
            continue
        if metric_value == 0:
            if skip_zeroes:
                continue
            if verbose:
                print("WARNING: %s=0 for %s" % (metric, entity))
        if metric_value < 0:
            if verbose:
                print("WARNING: %s<0 for %s" % (metric, entity))
        yield [entity, container_file, metric, metric_value]



def matches_regex (entity, regex_filter, verbose=False):
    if regex_filter is None:
        return False
    if len(regex_filter) == 0:  # fixes #33 - empty string is the same as no parameter
        return False
    try:
        longname = entity.longname()
        regex_result = re.search(regex_filter, longname)
        return regex_result is not None
    except:
        if verbose:
            print ("REGEX/EXCEPTION: %s" % regex_filter)
        return False


def save_histogram(show_mean_median, use_logarithmic_scale, filename_prefix, max_value, metric, metric_values_as_list, scope_name, mean = None, median = None, pstdev = None):
    plt.figure()  # new one, or they will be mixed
    n, bins, patches = plt.hist(metric_values_as_list, "doane", facecolor='green', alpha=0.75)
    plt.xlabel("%s   (max=%3.2f)" % (metric, max_value))
    plt.ylabel('Value')
    plt.title("%s %s (%i values in %i bins)" % (scope_name, metric, len(metric_values_as_list), len(bins)))
    plt.grid(True)
    if show_mean_median:
        try:
            mean = statistics.mean(metric_values_as_list) if mean is None else mean
            plt.axvline(mean, color='b', linestyle='dashed', linewidth=3, alpha=0.8, dash_capstyle="round")
            median = statistics.median(metric_values_as_list) if median is None else median
            plt.axvline(median, color='y', linestyle='dashed', linewidth=3, alpha=0.8, dash_capstyle="butt")
            pstdev = statistics.pstdev(metric_values_as_list, mean) if pstdev is None else pstdev
            plt.xlabel(
                "%s   (avg=%3.2f, median=%3.2f, stdev=%3.2f, max=%3.2f)" % (metric, mean, median, pstdev, max_value))
        except statistics.StatisticsError as se:
            pass
    if use_logarithmic_scale:
        plt.yscale('symlog', basey=10, linthreshy=10, subsy=[2, 3, 4, 5, 6, 7, 8,
                                                             9])  # http://stackoverflow.com/questions/17952279/logarithmic-y-axis-bins-in-python
    filename = "%s-%s-%s.png" % (filename_prefix, scope_name, metric)
    plt.savefig(filename, dpi=72)
    return [filename, mean, median, pstdev]


def _save_figure_as_html(fig, filename):
    with open(filename, "w") as output_file:
        output_file.write("<html><head></head><body>")
        mpld3.save_html(fig, output_file)
        output_file.write("</body></html>")


def save_scatter(x_values, x_label, y_values, y_label, ball_values, ball_label, color_values, color_label, annotations, filename_prefix, scope_name, show_diagonal=False, format="html"):
    #plt.figure()  # new one, or they will be mixed
    fig, ax = plt.subplots()
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("%i %s items. Circles: %s & %s" % (len(x_values), scope_name, ball_label, color_label))
    if show_diagonal:
        max_max = max(max(x_values), max(y_values))
        ax.plot([0.0, max_max], [0.0, max_max], ls="--", lw=2, alpha=0.5,
                color='green')  # http://matplotlib.org/api/lines_api.html
    scatter = ax.scatter(x_values, y_values, ball_values, alpha=0.5, c=color_values)
    filename = "%s-scatter-%s-%s_%s_%s.%s" % (filename_prefix, scope_name, x_label, y_label, ball_label, format)
    if format == "html":
        tooltip = mpld3.plugins.PointHTMLTooltip(scatter, labels=annotations, hoffset=10, voffset=-25)
        mpld3.plugins.connect(fig, tooltip)
        mpld3.plugins.connect(fig, mpld3.plugins.MousePosition(fmt=".2f"))
        mpld3.plugins.connect(fig, ClickSendToBack(scatter))
        _save_figure_as_html(fig, filename)
    else:
        plt.savefig(filename, dpi=72)
    return filename

def save_abstractness_x_instability_scatter(x_values, x_label, y_values, y_label, ball_values, ball_label, color_values, color_label, annotations, filename_prefix, scope_name, show_diagonal=True):
    #plt.figure()  # new one, or they will be mixed
    fig, ax = plt.subplots()
    ax.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) # http://stackoverflow.com/questions/8209568/how-do-i-draw-a-grid-onto-a-plot-in-python
    ax.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    plt.grid()
    if show_diagonal:
        plt.plot([0.0, 1.0], [1.0, 0.0], 'k-', ls="--", lw=2, alpha=0.5, color='green') # http://matplotlib.org/api/lines_api.html

        plt.plot([0.0, 0.7], [0.7, 0.0], 'k-', ls="--", lw=1, alpha=0.7, color='orange')  # http://matplotlib.org/api/lines_api.html
        plt.plot([0.3, 1.0], [1.0, 0.3], 'k-', ls="--", lw=1, alpha=0.7, color='orange')  # http://matplotlib.org/api/lines_api.html

        plt.plot([0.0, 0.4], [0.4, 0.0], 'k-', ls="--", lw=1, alpha=0.9, color='red')  # http://matplotlib.org/api/lines_api.html
        plt.plot([0.6, 1.0], [1.0, 0.6], 'k-', ls="--", lw=1, alpha=0.9, color='red')  # http://matplotlib.org/api/lines_api.html

    scatter = ax.scatter(x_values, y_values, ball_values, alpha=0.5, c=color_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("%i %s items. Circles: %s & %s" % (len(x_values), scope_name, ball_label, color_label))
    tooltip = mpld3.plugins.PointHTMLTooltip(scatter, labels=annotations, hoffset=10, voffset=-25)
    mpld3.plugins.connect(fig, tooltip)
    mpld3.plugins.connect(fig, mpld3.plugins.MousePosition(fmt=".2f"))
    mpld3.plugins.connect(fig, ClickSendToBack(scatter))
    filename = "%s-scatter-%s-%s_%s_%s.html" % (filename_prefix, scope_name, x_label, y_label, ball_label)
    _save_figure_as_html(fig, filename)
    return filename

def save_csv (csv_path, cur_tracked_metrics_for_csv):
    try:
        file = open(csv_path, "w")
        sep = ""
        for metric_name,metric_value in sorted(cur_tracked_metrics_for_csv.items()):
            file.write(sep)
            file.write(metric_name)
            sep = ","
        file.write("\n")
        sep = ""
        for metric_name,metric_value in sorted(cur_tracked_metrics_for_csv.items()):
            file.write(sep)
            file.write(str(metric_value))
            sep = ","
        file.write("\n")
        file.close()
        return True
    except:
        return False


def save_kiviat_with_values_and_thresholds (labels, values, threshold_values, file_name, title=None, max_vals = None, min_vals = None, thresholdslabel="limits", valueslabel="current"):
    if min_vals is None:
        min_vals = [min(round(t/2), round(v/2)) for v, t in zip(values, threshold_values)] # /2 because we want to avoid having all min points in the origin, for looks
    if max_vals is None:
        max_vals = [max(v, t, m + 0.001) for v, t, m in zip(values, threshold_values, min_vals)] #minimum plus 0.001 to prevent DivideBy Zero when max=min, bug #53
    ranges = [(x,y) for x,y in zip (min_vals, max_vals)]
    fig1 = plt.figure(figsize=(12, 12))
    radar = ComplexRadar(fig1, labels, ranges, precision=1)
    radar.plot(threshold_values, color="green", label=thresholdslabel)
    radar.fill(threshold_values, color="green", alpha=0.5)
    radar = ComplexRadar(fig1, labels, ranges, precision=1)
    radar.plot(values, color="orangered", label=valueslabel)
    radar.fill(values, color="orangered", alpha=0.5)
    radar.ax.legend(loc='upper center', bbox_to_anchor=(0.9, 1.10),
                    fancybox=False, shadow=False, ncol=48)
    if title is not None:
        plt.title(title, y=1.08)
    plt.savefig(file_name, dpi=72)
    return file_name


def post_metrics_to_sonar (cmdline_arguments, cur_tracked_metrics):
    TIMEOUT = 4
    sonar_url = cmdline_arguments["--sonarURL"]
    sonar_prj = cmdline_arguments["--sonarPrj"]
    sonar_user = cmdline_arguments["--sonarUser"]
    sonar_pass = cmdline_arguments["--sonarPass"]
    if sonar_prj == "#":
        print("*** Skipping posting to Sonar (PRJ=%s)" % sonar_prj)
        return
    for metric, value in cur_tracked_metrics.items():
        metric_name = metric.lower().replace(" ", "_").replace(":", "_") # SONAR wants its key, which is lowercase. get rid of stats special char :
        try:
            url = "%s/api/manual_measures" % sonar_url
            params = {"resource": sonar_prj, "metric": metric_name, "val": value}
            response = requests.post(url, params, timeout=TIMEOUT, auth=(sonar_user, sonar_pass))
            if response.status_code != 200: # Fix for #57 - try newer SONAR API
                url = "%s/api/custom_measures/create" % sonar_url
                params = {"projectKey": sonar_prj, "metricKey": metric_name,"value": value}
                response = requests.post(url, params, timeout=TIMEOUT,
                                         auth=(sonar_user, sonar_pass))
                if response.status_code == 400: # metric already created, we need to update it. But we need the metric ID for that
                    url = "%s/api/custom_measures/search" % sonar_url
                    params = {"projectKey": sonar_prj}
                    response = requests.post(url, params, timeout=TIMEOUT,
                                         auth=(sonar_user, sonar_pass))
                    metric_id = extract_metric_id_from_sonar_metric_search(metric_name, json.loads(response.text))
                    if metric_id is not None:
                        url = "%s/api/custom_measures/update" % sonar_url
                        params = {"projectKey": sonar_prj, "id": metric_id,"value": value}
                        response = requests.post(url, params, timeout=TIMEOUT,
                                                 auth=(sonar_user, sonar_pass))
            if response.status_code != 200:
                print("*** Response error %s for metric '%s' when connecting to %s with params %s: \t%s" % (response.status_code, metric, url, params, str(response.content)))
            else:
                print("+++ Metric %s=%s posted to prj %s in %s (%s)" % (metric, value, sonar_prj, sonar_url, str(response.content)))
        except requests.exceptions.Timeout:
            print("*** Timeout connecting to %s" % sonar_url)
            return
        except requests.exceptions.HTTPError:
            print("*** HTTP Error connecting to %s" % sonar_url)
            return
        except requests.exceptions.ConnectionError:
            print("*** Connection Error connecting to %s" % sonar_url)
            return

def extract_metric_id_from_sonar_metric_search(metric_key_to_find, json_response):
    for entry_as_dict in json_response.get("customMeasures", []):
        metric_attribs = entry_as_dict.get("metric", {})
        metric_key = metric_attribs.get("key", None)
        if metric_key == metric_key_to_find:
            return entry_as_dict.get("id", None)
    return None

# Adapted (added file): https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
URL_REGEX = re.compile(
        r'^(?:http|ftp|file)s?://', re.IGNORECASE)


def is_url (a_string) :
    return URL_REGEX.match(a_string)


def load_json(max_metrics_json_or_path):
    if os.path.isfile(max_metrics_json_or_path):
        with open(max_metrics_json_or_path) as max_metrics_json:
            return json.load(max_metrics_json)
    elif is_url(max_metrics_json_or_path):
        with  urllib.request.urlopen(max_metrics_json_or_path) as url_connection:
        #with requests.get(max_metrics_json_or_path) as url_connection:
        #    return json.loads(url_connection.text)
            return json.loads(url_connection.read().decode('utf-8'))

    else:
        return json.loads(max_metrics_json_or_path)

def load_metrics_thresholds(max_metrics_json_or_path):
    return load_json(max_metrics_json_or_path)
