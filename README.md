srccheck: a utility to [KALOI](http://structure101.com/2006/10/complexity-debt-dont-fix-it-keep-a-lid-on-it/) (Keep a Lid On It) source code on various metrics supported by [SciTools Understand](https://scitools.com).

Pre-requisites
===============
* This utility is written in Python. You will need a Python interpreter installed or you will have to package
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

How to Run It
=============
The source code includes a file comment that defines all command-line parameters and what they do. In order to avoid
duplication here, we recommend that you look at the top of the srccheck.py file. Or simply run the tool and have it
print the options.

But basically we take 4 different JSONs as input, which define:

 * --maxPrjMetrics
 * --maxFileMetrics
 * --maxClassMetrics
 * --maxRoutineMetrics
 
These JSONs are each a dictionary, where each key is the name of the metric and the value is the maximum value it can take.
Anything above is considered a violation. 

Examples
=========

Here is an example used to analyze Delphi code:

```
python srccheck.py --in="C:\temp\PJ_DIARIO.udb" --maxFileMetrics={"CountLineCode":5000,"CountDeclFunction":40,"CountDeclClass":5} --maxClassMetrics={"CountDeclMethod":50,"MaxInheritanceTree":6}
--maxRoutineMetrics={"CountLineCode":1000,"CountParams":20,"CyclomaticStrict":24,"CyclomaticModified":12} --maxPrjMetrics={"AvgCyclomatic":2,"MaxNesting":5} --regexIgnoreFiles="tlb|[.]dfm" --regexIgnoreRoutines="ExecutaMetodoServidor|Invoke" --verbose
```

Here is an example that analyzes C++ code, using the defaults we provide:

```
python srccheck.py --in=c:\temp\BlackJack.udb --sonarUser=admin --sonarPass=admin --sonarURL=http://localhost:9000/api/manual_measures --sonarPrj=BlackJack 
```

