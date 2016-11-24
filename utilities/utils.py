import re
import statistics

from matplotlib import pyplot as plt
import mpld3

def stream_of_entity_with_metric (entities, metric, verbose, skipLibraries,regex_str_ignore_item, regex_str_traverse_files, regex_ignore_files, skip_zeroes = False ):
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
        if metric == "CountParams":
            metric_value = len(entity.ents("Define", "Parameter"))
        else:
            metric_dict = entity.metric((metric,))
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


def save_scatter(x_values, x_label, y_values, y_label, ball_values, ball_label, color_values, annotations, filename_prefix, scope_name):
    #plt.figure()  # new one, or they will be mixed
    fig, ax = plt.subplots()
    scatter = ax.scatter(x_values, y_values, ball_values, alpha=0.5, c=color_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("%i %s items. Circle sizes: %s" % (len(x_values), scope_name, ball_label))
    tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=annotations)
    mpld3.plugins.connect(fig, tooltip)
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