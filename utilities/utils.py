import re
import statistics

from matplotlib import use as backend_use
backend_use('Agg') # fixes #32 - change backend to simple one, BEFORE any other import.
from matplotlib import pyplot as plt
plt.ioff()  # fixes #32 - no need for an interactive backend
import mpld3


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
    mpld3.register_plugin("clickinfo", ClickInfo);
    ClickInfo.prototype = Object.create(mpld3.Plugin.prototype);
    ClickInfo.prototype.constructor = ClickInfo;
    ClickInfo.prototype.requiredProps = ["id"];
    function ClickInfo(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    ClickInfo.prototype.draw = function(){
        var obj = mpld3.get_element(this.props.id);
        obj.elements().on("mousedown",
                          function(d, i){d3.select(this).moveToBack();});
    }
    """

    def __init__(self, points):
        self.dict_ = {"type": "clickinfo",
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
            metric_dict ["CountParams"] = len(entity.ents("Define", "Parameter"))
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
                print("WARNING: metric is zero for %s" % entity )
        if metric_value < 0:
            if verbose:
                print("WARNING: metric is negative %s" % entity)
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
            plt.axvline(median, color='r', linestyle='dashed', linewidth=3, alpha=0.8, dash_capstyle="butt")
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


def save_scatter(x_values, x_label, y_values, y_label, ball_values, ball_label, color_values, color_label, annotations, filename_prefix, scope_name):
    #plt.figure()  # new one, or they will be mixed
    fig, ax = plt.subplots()
    scatter = ax.scatter(x_values, y_values, ball_values, alpha=0.5, c=color_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("%i %s items. Circles: %s & %s" % (len(x_values), scope_name, ball_label, color_label))
    tooltip = mpld3.plugins.PointHTMLTooltip(scatter, labels=annotations)
    mpld3.plugins.connect(fig, tooltip)
    mpld3.plugins.connect(fig, mpld3.plugins.MousePosition())
    mpld3.plugins.connect(fig, ClickSendToBack(scatter))
    filename = "%s-scatter-%s-%s_%s_%s.html" % (filename_prefix, scope_name, x_label, y_label, ball_label)
    mpld3.save_html(fig, filename)
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
    tooltip = mpld3.plugins.PointHTMLTooltip(scatter, labels=annotations)
    mpld3.plugins.connect(fig, tooltip)
    mpld3.plugins.connect(fig, mpld3.plugins.MousePosition())
    mpld3.plugins.connect(fig, ClickSendToBack(scatter))
    filename = "%s-scatter-%s-%s_%s_%s.html" % (filename_prefix, scope_name, x_label, y_label, ball_label)
    mpld3.save_html(fig, filename)
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