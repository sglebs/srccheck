import re


def stream_of_entity_with_metric (entities, metric, verbose, skipLibraries,regex_str_ignore_item, regex_str_traverse_files, regex_ignore_files, cmdline_arguments, skip_zeroes = False ):
    for entity in entities:
        library_name = entity.library()
        if library_name is not "" and skipLibraries:
            #            if verbose:
            #                print ("LIBRARY/SKIP: %s" % entity.longname())
            continue
        if matches_regex(entity, regex_str_ignore_item, cmdline_arguments):
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
            if not matches_regex(container_file, regex_str_traverse_files, cmdline_arguments):
                if verbose:
                    print("SKIP due to file traverse regex non-match: %s" % container_file.longname())
                continue
            if matches_regex(container_file, regex_ignore_files, cmdline_arguments):
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
            metric_value = 0
        if metric_value == 0:
            if skip_zeroes:
                continue
            if verbose:
                print("WARNING: metric is zero for %s" % entity )
        yield [entity, container_file, metric, metric_value]


def matches_regex (entity, regex_filter, cmdline_arguments):
    if regex_filter is None:
        return False
    try:
        longname = entity.longname()
        regex_result = re.search(regex_filter, longname)
        return regex_result is not None
    except:
        verbose = cmdline_arguments["--verbose"]
        if verbose:
            print ("REGEX/EXCEPTION: %s" % regex_filter)
        return False