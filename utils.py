import requests


def _post_to_sonar (cmdline_arguments, cur_tracked_metrics):
    TIMEOUT = 4
    sonar_url = cmdline_arguments["--sonarURL"]
    sonar_prj = cmdline_arguments["--sonarPrj"]
    sonar_user = cmdline_arguments["--sonarUser"]
    sonar_pass = cmdline_arguments["--sonarPass"]
    if sonar_prj == "#":
        print ("*** Skipping posting to Sonar (PRJ=%s)" % sonar_prj)
        return
    for metric, value in cur_tracked_metrics.items():
        rest_params = {}
        rest_params["resource"] = sonar_prj
        rest_params["metric"] = metric.lower() # SONAR wants its key, which is lowercase
        rest_params["val"] = value
        try:
            response = requests.post(sonar_url, rest_params, timeout=TIMEOUT, auth=(sonar_user, sonar_pass))
            if response.status_code != 200:
                print ("*** Response error connecting to %s: %s" % (sonar_url, str(response.content)))
            else:
                print ("+++ Metric %s=%s posted to prj %s in %s (%s)" % (metric, value, sonar_prj, sonar_url, str(response.content)))
        except requests.exceptions.Timeout:
            print ("*** Timeout connecting to %s" % sonar_url)
            return
        except requests.exceptions.HTTPError:
            print ("*** HTTP Error connecting to %s" % sonar_url)
            return
        except requests.exceptions.ConnectionError:
            print ("*** Connection Error connecting to %s" % sonar_url)
            return


def _generate_csv (cmdline_arguments, cur_tracked_metrics_for_csv):
    csv_path = cmdline_arguments["--outputCSV"]
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
        print ("+++ Metrics saved to %s" % csv_path)
    except:
        print ("\n*** Problems creating CSV file %s" % csv_path)