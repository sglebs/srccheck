srccheck: a utility to [KALOI](http://structure101.com/2006/10/complexity-debt-dont-fix-it-keep-a-lid-on-it/) (Keep a Lid On It) source code on various metrics supported by [SciTools Understand](https://scitools.com).

Pre-requisites
===============
* This utility is written in Python 3. You will need a Python 3 interpreter installed or you will have to package
this into a self contained executable. 
* This utility uses [SciTools Understand](https://scitools.com). You will need a valid license of Understand
in your machine so you can use this script. This script uses a UDB file as input.
* (optional) [Jenkins](https://jenkins-ci.org)
* (optional) [SONAR](http://www.sonarsource.com)

What It Does
=============
You can use srccheck to fail your build (say in Jenkins) if a specific metric goes beyond a threshold you define.
It could be routine cyclomatic complexity, it could be max number of methods in a class, and so on. Basically any
[Understand Metric](https://scitools.com/support/metrics_list/) can be used. And it supports many programming
languages (Java, C++, Python, etc).

NOTE: There is one extra metric that Understand does not have natively but we do support: CountParams, for routines/functions/methods.
It represents the number of parameters a routine/function/method takes.

Beyond that, you can keep a trend dashboard of your metrics over time. For that, you need to have Jenkins installed
and its [Plot Plugin](https://wiki.jenkins-ci.org/display/JENKINS/Plot+Plugin) installed as well. srccheck can
generate the CSV file that this plugin requires (see our --outputCSV= command-line parameter).

If you want to publish some metrics as a dashboard in SONAR, you can also do it. For that, you must first
register Manual Measures in SONAR, and srccheck will use this [Manual Measures API](http://docs.codehaus.org/pages/viewpage.action?pageId=229743270).
The steps are:

 * Login into SONAR as Administrator
 * Configuration/Manual Measures
 * Add Measure

Note that the exit code of this script is the number of violations found. This allows you to incorporate srccheck
into your workflow regardless of the build tool used.

How to Install It
=================

Make sure your Python has paver installed (pip3 install paver) and then run:
```
pip3 install git+https://github.com/sglebs/srccheck
```


How to Run It
=============
The source code includes a file comment that defines all command-line parameters and what they do. In order to avoid
duplication here, we recommend that you look at the top of the srccheck.py file. Or simply run the tool and have it
print the options.

But basically we take 4 different JSONs as input, which define:

 * --maxPrjMetrics , which defines the maximum allowed value for metrics that apply to the project as a whole.
 * --maxFileMetrics , which defines the maximum allowed value for metrics that apply to individual files.
 * --maxClassMetrics , which defines the maximum allowed value for metrics that apply to individual classes.
 * --maxRoutineMetrics , which defines the maximum allowed value for metrics that apply to individual routines (methods, functions, procedures, etc).
 
These JSONs are each a dictionary, where each key is the name of the metric and the value is the maximum value it can take.
Anything above is considered a violation. 

Examples
=========

Here is an example used to analyze Delphi code:

```
C:\>srccheck --in="C:\temp\PJ_DIARIO.udb" --maxFileMetrics={\"CountLineCode\":5000,\"CountDeclFunction\":40,\"CountDeclClass\":5} --maxClassMetrics={\"CountDeclMethod\":50,\"MaxInheritanceTree\":6}
--maxRoutineMetrics={\"CountLineCode\":1000,\"CountParams\":20,\"CyclomaticStrict\":24,\"CyclomaticModified\":12} --maxPrjMetrics={\"AvgCyclomatic\":2,\"MaxNesting\":5} --regexIgnoreFiles="tlb|[.]dfm" --regexIgnoreRoutines="ExecutaMetodoServidor|Invoke" --verbose
```

(Note that under the Windows shell you need to escape each " with a \ ).

If the command above fails, you may need to set PATH and PYTHONPATH if you have Understand installed in a non-default location:

```
C:\>set PYTHONPATH=C:\Program Files\SciTools-4.0.860-64b\bin\pc-win64\python

C:\>set PATH=%PATH%;C:\Program Files\SciTools-4.0.860-64b\bin\pc-win64

```


Here is an example that analyzes C++ code, using the defaults we provide:

```
srccheck --in=c:\temp\BlackJack.udb --sonarUser=admin --sonarPass=admin --sonarURL=http://localhost:9000/api/manual_measures --sonarPrj=BlackJack 
```

Here is a full example which gets the srccheck sources, gets understand, gets the source code for junit,
invokes understand on its sources and then our tool:

```
git clone https://github.com/sglebs/srccheck.git
cd srccheck
rm -rf tmp
mkdir tmp
cd tmp
wget http://latest.scitools.com/Understand/Understand-4.0.843-Linux-64bit.tgz
tar xvf Understand-4.0.843-Linux-64bit.tgz
# make sure und is in the PATH
export PATH=$PATH:./scitools/bin/linux64/
git clone https://github.com/junit-team/junit.git
# run Understand from the GUI to activate the trial
understand
# now we can automate
und create -languages java junit.udb
und add ./junit/src/main/java/junit junit.udb
und analyze junit.udb
virtualenv env -p /usr/bin/python3
source env/bin/activate
pip install paver
pip install -r ../requirements.txt
PYTHONPATH=./scitools/bin/linux64/python python3 ../srccheck.py --in=junit.udb --maxFileMetrics='{"CountLineCode":500,"CountDeclFunction":30,"CountDeclClass":1}' --maxClassMetrics='{"CountDeclMethod":20,"MaxInheritanceTree":4}' --maxRoutineMetrics='{"CountLineCode":80,"CountParams":7,"CyclomaticModified":7}' --maxPrjMetrics='{"AvgCyclomaticModified":3,"MaxNesting":5}' --verbose
```

(Note that under the Linux shell you need to single-quote the json values and there is no need to escape each " with a \ like you do under Windows)

Averages and variances
======================
Understand does provide some metrics for averages. The problem is that these do not take into account our whitelist or 
blacklist of files. Also, not all metrics have Stdev, Avg etc equivalents. In order to fix this we added support to
compute a few derived stats metrics on any existing metric, using prefixes. They are:

   * AVG (uses statistics.mean)
   * MEDIAN (uses statistics.median)
   * MEDIANGROUPED (uses statistics.median_grouped)
   * MEDIANHIGH (uses statistics.median_high)
   * MEDIANLOW (uses statistics.median_low)
   * MODE (uses statistics.mode)
   * STDEV (uses statistics.pstdev)
   * VARIANCE (uses statistics.pvariance)
   
Example:  {CyclomaticModified":10, "STDEV:CyclomaticModified":1.8, "AVG:CyclomaticModified":2.2} 

The example above will raise an issue if the maximum CyclomaticModified goes above 10, but also if 
the average goes above 2.2 or the standard deviation goes above 1.8. This allows you to control not
only maximum values of your outliers, but also averages and the spread (how far off they spread).
We use the stats functions in https://docs.python.org/3/library/statistics.html .

Histograms
==========
Sometimes metric values are very high and we want to visualize how the values are spread and their frequencies. With that in mind the *srcplot* tools was implemented and is bundled in - it plots histograms of the values found for the metric(s) you choose. It is similar to *srccheck* to run, with some minor differences. One of them is that you pass a comma-separated list of metric names for File, Class and Routine (and not max values as a json, as with *srccheck* itself). You can also choose to plot the histogram using a logarithmic scale for the y axis (-l flag). In cases you get too many occurrences of zero for the metric value and want to discard those, to focus on values > 0, you can pass a flag for that (-z). The tool will output PNG files in the current directory, one for each metric.

Here's how to plot histograms for some metrics for the Django project:

```
srcplot --dllDir=/Applications/Understand.app/Contents/MacOS/Python --in=/Users/mqm/Downloads/django.udb --fileMetrics=CountLineCode,CountDeclFunction,CountDeclClass --classMetrics=CountDeclMethod,MaxInheritanceTree --routineMetrics=CountLineCode,CountParams,CyclomaticStrict -l
```


