#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
# Time-stamp: <Last updated: ZHAO,Ya-Fan yafanzhao@163.com 2022-02-03 10:53:19>

import enum
import subprocess
import re
import json
import glob
import sys
import copy
import random
import math
import os
import logging
from configparser import ConfigParser, NoOptionError

"""
INT:
400.perlbench 	C 	PERL Programming Language
401.bzip2 	C 	Compression
403.gcc 	C 	C Compiler
429.mcf 	C 	Combinatorial Optimization
445.gobmk 	C 	Artificial Intelligence: go
456.hmmer 	C 	Search Gene Sequence
458.sjeng 	C 	Artificial Intelligence: chess
462.libquantum 	C 	Physics: Quantum Computing
464.h264ref 	C 	Video Compression
471.omnetpp 	C++ 	Discrete Event Simulation
473.astar 	C++ 	Path-finding Algorithms
483.xalancbmk 	C++ 	XML Processing 

FP:
410.bwaves 	Fortran 	Fluid Dynamics
416.gamess 	Fortran 	Quantum Chemistry
433.milc 	C 	Physics: Quantum Chromodynamics
434.zeusmp 	Fortran 	Physics / CFD
435.gromacs 	C/Fortran 	Biochemistry/Molecular Dynamics
436.cactusADM 	C/Fortran 	Physics / General Relativity
437.leslie3d 	Fortran 	Fluid Dynamics
444.namd 	C++ 	Biology / Molecular Dynamics
447.dealII 	C++ 	Finite Element Analysis
450.soplex 	C++ 	Linear Programming, Optimization
453.povray 	C++ 	Image Ray-tracing
454.calculix 	C/Fortran 	Structural Mechanics
459.GemsFDTD 	Fortran 	Computational Electromagnetics
465.tonto 	Fortran 	Quantum Chemistry
470.lbm 	C 	Fluid Dynamics
481.wrf 	C/Fortran 	Weather Prediction
482.sphinx3 	C 	Speech recognition 
"""
Benchmarks = {
    "int": {
        "400": {
            "name": "perlbench",
            "lang": ["C"],
            "desc": "PERL Programming Language"
        },
        "401": {
            "name": "bzip2",
            "lang": ["C"],
            "desc": "Compression"
        },
        "403": {
            "name": "gcc",
            "lang": ["C"],
            "desc": "C Compiler"
        },
        "429":  {
            "name": "mcf",
            "lang": ["C"],
            "desc": "Combinatorial Optimization"
        },
        "445":  {
            "name": "gobmk",
            "lang": ["C"],
            "desc": "Artificial Intelligence: go"
        },
        "456":  {
            "name": "hmmer",
            "lang": ["C"],
            "desc": "Search Gene Sequence"
        },
        "458":  {
            "name": "sjeng",
            "lang": ["C"],
            "desc": "Artificial Intelligence: chess"
        },
        "462":  {
            "name": "libquantum",
            "lang": ["C"],
            "desc":	"Physics: Quantum Computing"
        },
        "464":  {
            "name": "h264ref",
            "lang": ["C"],
            "desc": "Video Compression"
        },
        "471":  {
            "name": "omnetpp",
            "lang": ["C++"],
            "desc": "Discrete Event Simulation"
        },
        "473":  {
            "name": "astar",
            "lang": ["C++"],
            "desc": "Path-finding Algorithms"
        },
        "483":  {
            "name": "xalancbmk",
            "lang": ["C++"],
            "desc": "XML Processing"
        }
    },
    "fp": {
        "410": {
            "name": "bwaves",
            "lang": ["Fortran"],
            "desc": "Fluid Dynamics"
        },
        "416": {
            "name": "gamess",
            "lang": ["Fortran"],
            "desc": "Quantum Chemistry"
        },
        "433": {
            "name": "milc",
            "lang": ["C"],
            "desc": "Physics: Quantum Chromodynamics"
        },
        "434": {
            "name": "zeusmp",
            "lang": ["Fortran"],
            "desc": "Physics / CFD"
        },
        "435": {
            "name": "gromacs",
            "lang": ["C", "Fortran"],
            "desc": "Biochemistry/Molecular Dynamics"
        },
        "436": {
            "name": "cactusADM",
            "lang": ["C", "Fortran"],
            "desc": "Physics / General Relativity"
        },
        "437": {
            "name": "leslie3d",
            "lang": ["Fortran"],
            "desc": "Fluid Dynamics"
        },
        "444": {
            "name": "namd",
            "lang": ["C++"],
            "desc": "Biology / Molecular Dynamics"
        },
        "447": {
            "name": "dealII",
            "lang": ["C++"],
            "desc": "Finite Element Analysis"
        },
        "450": {
            "name": "soplex",
            "lang": ["C++"],
            "desc": "Linear Programming, Optimization"
        },
        "453": {
            "name": "povray",
            "lang": ["C++"],
            "desc": "Image Ray-tracing"
        },
        "454": {
            "name": "calculix",
            "lang": ["C", "Fortran"],
            "desc": "Structural Mechanics"
        },
        "459": {
            "name": "GemsFDTD",
            "lang": ["Fortran"],
            "desc": "Computational Electromagnetics"
        },
        "465": {
            "name": "tonto",
            "lang":  ["Fortran"],
            "desc": "Quantum Chemistry"
        },
        "470": {
            "name": "lbm",
            "lang": ["C"],
            "desc": "Fluid Dynamics"
        },
        "481": {
            "name": "wrf",
            "lang": ["C", "Fortran"],
            "desc":	"Weather Prediction"
        },
        "482": {
            "name": "sphinx3",
            "lang": ["C"],
            "desc": "Speech recognition"
        }
    }
}

OptMap = {
    "C": "COPTIMIZE",
    "C++": "CXXOPTIMIZE",
    "Fortran": "FOPTIMIZE"
}

#Setup the logging, keep a jobs.log file and also print the log to stdout.
LogFile = "AutoSPEC.log"
LogFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s: %(message)s')
Logger = logging.getLogger('AutoSPEC')
Logger.setLevel(logging.INFO)
if not Logger.handlers:
    LoggerFH = logging.FileHandler(LogFile, mode='a')
    LoggerFH.setFormatter(LogFormatter)
    Logger.addHandler(LoggerFH)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(LogFormatter)
    Logger.addHandler(stdout_handler)
Logger.propagate = False

def SplitLog(LogLines):
    """
    a function to split the log file into several blocks.

    Args:
        LogLines (list): lines in the log file.
    """
    LineNum = len(LogLines)
    i = 0
    RunningBenchmarkLines = []
    while i < LineNum:
        Line = LogLines[i]
        m_Running = re.search("^Running Benchmarks$", Line)
        if m_Running:
            RunningBenchmarkLines.append(i)
    RunningBenchmarkLines.append(LineNum)
    return RunningBenchmarkLines

def ExtractResFromLog(LogLines):
    """
    get the result from the log.
    Args:
        LogLines (list): lines of the log file
    """
    SPEC_INT = Benchmarks["int"]
    SPEC_FP = Benchmarks["fp"]
    Res = []
    for Line in LogLines:
        m_ratio = re.search(r"^\s+Success (\d+).(\w+) (\w+) (\w+) ratio=(\S+), runtime=(\d+\.\d+)", Line)
        if m_ratio:
            MyDict = {}
            MyDict["BenchNO"] = m_ratio.group(1)
            MyDict["BenchName"] = m_ratio.group(2)
            MyDict["Tune"] = m_ratio.group(3)
            MyDict["BenchSize"] = m_ratio.group(4)
            MyDict["Ratio"] = float(m_ratio.group(5))
            MyDict["RunTime"] = float(m_ratio.group(6))
            if MyDict["BenchNO"] in SPEC_INT.keys():
                MyDict["PointType"] = "int"
            elif MyDict["BenchNO"] in SPEC_FP.keys():
                MyDict["PointType"] = "fp"
            else:
                MyDict["PointType"] = ""
            Res.append(MyDict)
    return Res

def filter_res(Res, Tune, BenchSize, PointType):
    """
    filter the result by the type and size of the benchmark.
    Args:
        Res (list): a list about the result
        Tune (str): the type of the benchmark, could be base or peak
        BenchSize (str): the size of the benchamrk, could be test, train or ref.
        PointType (str): the point type of the benchmark, could be int or fp.
    """
    FilteredRes = []
    for MyDict in Res:
        if MyDict["Tune"] == Tune and MyDict["BenchSize"] == BenchSize and MyDict["PointType"] == PointType:
            FilteredRes.append(MyDict)
    return FilteredRes

def print_res(res):
    """ 
    friendly print the result

    Args:
        res (list): list of result dict
    """
    out = "\n"
    for r in res:
        out += "%s\t%s.%s\t%s\n" %(r["Tune"], r["BenchNO"], r["BenchName"], r["Ratio"])
    Logger.info(out)

def GetScore(FilteredRes):
    """
    get the final score from the filtered result, which is the geometry mean of the ratio of each benchmark
    Args:
        FilteredRes (list): a list of the result
    """
    if len(FilteredRes) == 0:
        Logger.error("Cannot find any data in the current result.")
        return 0.0
    MyDict = FilteredRes[0]
    BenchSize = MyDict["BenchSize"]
    PointType = MyDict["PointType"]
    SPEC_ITEMS = Benchmarks[PointType]
    Scores = {}
    if BenchSize != "ref":
        Logger.warning("The final score is only calculated when the benchmark size is ref")
        return 0.0
    else:
        for MyDict in FilteredRes:
            BenchNO = MyDict["BenchName"]
            if BenchNO not in Scores.keys():
                Scores[BenchNO] = []
            Scores[BenchNO].append(MyDict["Ratio"])
        if len(Scores.keys()) == len(SPEC_ITEMS.keys()):
            FinalScore = 1.0
            for BenchNO, MyScore in Scores.items():
                FinalScore *= (sum(MyScore)/len(MyScore))
            FinalScore = FinalScore**(1.0/len(Scores.keys()))
            return FinalScore
        else:
            Errors = GetErrorItems(Scores, SPEC_ITEMS)
            Logger.error("There are %d items with errors: %s",len(Errors), Errors)
            return 0.0

def GetErrorItems(MyDict, SPEC_ITEMS):
    """
    find items with errors.
    """
    Errors = []
    for mykey in SPEC_ITEMS.keys():
        if mykey not in MyDict.keys():
            Errors.append(SPEC_ITEMS[mykey]["name"])
    return Errors

def load_json(JSONFile):
    """
    Read the content of a json file and convert it to a dict or a dict list.
    """
    f = open(JSONFile, "r")
    content = f.read()
    JSONDict = json.loads(content)
    f.close()
    return JSONDict

def dump_json(MyDict, JSONFile):
    """
    Dump a dict to a json file
    """
    with open(JSONFile, "w") as f:
        json.dump(MyDict, f, indent=4)
        f.close()

def GetBaseFlags(CFGLines, start, end):
    """
    A function to get the flags from the cfg file
    Args:
        CFGLines (list): list of lines
        start (int):  
    """
    Flags = {}
    OPTIMIZE = None
    COPTIMIZE = None
    CXXOPTIMIZE = None
    FOPTIMIZE = None
    EXTRA_LDFLAGS = None
    i = start
    while i < end:
        Line = CFGLines[i]
        m_OPTIMIZE = re.search(r"^OPTIMIZE\s+=", Line)
        m_COPTIMIZE = re.search(r"^COPTIMIZE\s+=", Line)
        m_CXXOPTIMIZE = re.search(r"^CXXOPTIMIZE\s+=", Line)
        m_FOPTIMIZE = re.search(r"^FOPTIMIZE\s+=", Line)
        m_EXTRA_LDFLAGS = re.search(r"^EXTRA_LDFLAGS\s+=", Line)
        if m_OPTIMIZE:
            OPTIMIZE = i
        elif m_COPTIMIZE:
            COPTIMIZE = i
        elif m_CXXOPTIMIZE:
            CXXOPTIMIZE = i
        elif m_FOPTIMIZE:
            FOPTIMIZE = i
        elif m_EXTRA_LDFLAGS:
            EXTRA_LDFLAGS = i
            break
        i += 1
    Flags["OPTIMIZE"] = OPTIMIZE
    Flags["COPTIMIZE"] = COPTIMIZE
    Flags["CXXOPTIMIZE"] = CXXOPTIMIZE
    Flags["FOPTIMIZE"] = FOPTIMIZE
    Flags["EXTRA_LDFLAGS"] = EXTRA_LDFLAGS
    return Flags

def GetPeakFlags(CFGLines, start, end):
    """
    get the compiler flags for each peak benchmark.
    Args:
        CFGLines (list): content of the config file
        start (int): the start line number of the peak section
    """
    Flags = {}
    i = start
    while i < end:
        Line = CFGLines[i]
        m_benchmark = re.search(r"^(\d+)\.(\w+)=peak=default=default:", Line)
        if m_benchmark:
            BenchNO = m_benchmark.group(1)
            Flags[BenchNO] = {}
            while True:
                i += 1
                Line = CFGLines[i]
                m_OPTIMIZE = re.search(r"(\w+OPTIMIZE)\s+=", Line)
                m_FLAGS = re.search(r"(\S+FLAGS)\s+=", Line)
                m_Blank = re.search(r"^\s?$", Line)
                if m_OPTIMIZE:
                    FlagName = m_OPTIMIZE.group(1)
                    Flags[BenchNO][FlagName] = i
                elif m_FLAGS:
                    FlagName = m_FLAGS.group(1)
                    Flags[BenchNO][FlagName] = i
                elif m_Blank:
                    break
        i += 1
    return Flags

def get_compiler_options(CFGFile):
    """
    a function to parse the CFG files and return the line numbers for the options in each test case.
    The structure of a CFG file is like this:
    1. common: compiler, portability and other options.
    2. int base
    3. fp base
    4. peak: int peak and fp peak
    5. md5
    Args:
        CFGFile (str): the name of the cfg file
    """
    CFG = {}
    with open(CFGFile, "r") as fp:
        CFGLines = fp.readlines()
        fp.close()
    CFGLineNum = len(CFGLines)
    i = 0
    # find the key start and end line in the config file
    while i < CFGLineNum:
        Line = CFGLines[i]
        m_int_base = re.search(r"^\s?int=base=default=default:\s?$", Line)
        m_fp_base = re.search(r"^\s?fp=base=default=default:\s?$", Line)
        m_peak = re.search(r"^\s?default=peak=default=default:\s?$", Line)
        m_MD5 = re.search(r"__MD5__", Line)
        if m_int_base:
            int_base_start = i
        elif m_fp_base:
            fp_base_start = i
        elif m_peak:
            peak_start = i
        elif m_MD5:
            md5_start = i
            break
        i += 1
    CFG["int_base"] = GetBaseFlags(CFGLines, int_base_start, fp_base_start-1)
    CFG["fp_base"] = GetBaseFlags(CFGLines, fp_base_start, peak_start-1)
    CFG["peak"] = GetPeakFlags(CFGLines, peak_start, md5_start - 1)
    return CFG

def parse_benchmark_flags(opt_flag_names, cfg_lines, cfg_linenum):
    """parse the optimization flags for a certain benchmark
    Args:
        benchmark ([str]): the name or number of the benchmark
        cfg_lines ([list]): the current cfg file.
        cfg_linenum ([type]): the cfg containing the line number of each flag.
    """
    flags = []
    for flag_type in opt_flag_names:
        flags.append(cfg_lines[cfg_linenum[flag_type]].split("=")[1].strip().split())
    return flags

def UpdateCFG(CFGLines, CFG, NewFlags):
    """
    given the new gcc flags, generate a new CFG 
    """
    NewCFGLines = copy.deepcopy(CFGLines)
    for FlagType in ["int_base", "fp_base"]:
        if FlagType in NewFlags.keys():
            for FlagName, FlagValue in NewFlags[FlagType].keys():
                LineNum = CFG[FlagType][FlagName]
                MyLine = "%s = %s\n" % (FlagName, FlagValue)
                NewCFGLines[LineNum] = MyLine
    if "peak" in NewFlags.keys():
        for BenchNO, Flag in NewFlags["peak"].items():
            for FlagName, FlagValue in Flag.items():
                LineNum = CFG["peak"][BenchNO][FlagName]
                MyLine = "%s = %s" % (FlagName, FlagValue)
                NewCFGLines[LineNum] = MyLine
    return NewCFGLines

def KeepFlags(OldScore, NewScore, KBT):
    """
    using a Monte Carlo method to determine whether to keep the current flags or not.
    the basin hopping method.
    """
    deltaScore = NewScore - OldScore
    if deltaScore >= 0:
        return True
    if deltaScore < 0:
        P = random.random()
        if math.exp(deltaScore/KBT) > P:
            return True
        else:
            return False

def update_cfg_lines(old_cfg_lines, opt_flag_names, cfg_struct, flags):
    """generate the new config lines according to the new flags.

    Args:
        old_cfg_lines (list): a list of the original cfg lines
        benchmark (str): the name of the benchmark
        cfg_struct (dict)): a dict about the struct of the config file.
        flags (list): new optimization flags for spec cpu
    """
    Logger.info("Generating the new config file.")
    new_cfg_lines = copy.deepcopy(old_cfg_lines)
    for i, flag_type in enumerate(opt_flag_names):
        flag_line = "%s = %s\n" %(flag_type, " ".join(flags[i]))
        Logger.info(flag_line)
        line_num = cfg_struct[flag_type]
        new_cfg_lines[line_num] = flag_line
    return new_cfg_lines

def get_config_file(log_lines):
    """get the name of the config file according to the log_lines

    Args:
        log_lines ([list]): [a list of the log lines]
    """
    for line in log_lines:
        m = re.search(r"Reading config file '(.*)'", line)
        if m:
            return m.group(1)
    else:
        Logger.error("Failed to find the name of the config file.")
        return ""

def get_log_name(out_lines):
    """"get the name of logfile from the out put of spec 2006"

    Args:
        out ([list]): list of lines in the output
    """
    for line in out_lines:
        m1 = re.search(r"^logname\s+=\s+(.*)$", line)
        m2 = re.search(r"The log for this run is in (.*)$", line)
        if m1:
            return m1.group(1)
        elif m2:
            return m2.group(1)
    else:
        Logger.error("Cannot get the logname from the output")
        return ""

def parse_log_file(log_file):
    """main function of this program.
    """
    with open(log_file, "r") as fp:
        log_lines = fp.readlines()
        fp.close()
    Res = ExtractResFromLog(log_lines)
    base_int_res = filter_res(Res, "base", "ref", "int")
    base_fp_res = filter_res(Res, "base", "ref", "fp")
    peak_int_res = filter_res(Res, "peak", "ref", "int")
    peak_fp_res = filter_res(Res, "peak", "ref", "fp")
    print_res(base_int_res)
    print_res(base_fp_res)
    print_res(peak_int_res)
    print_res(peak_fp_res)
    BaseInt = GetScore(base_int_res)
    BaseFP = GetScore(base_fp_res)
    PeakInt = GetScore(peak_int_res)
    PeakFP = GetScore(peak_fp_res)
    Logger.info("\nBaseInt = %.2f\nBaseFP = %.2f\nPeakInt = %.2f\nPeakFP = %.2f",
                BaseInt, BaseFP, PeakInt, PeakFP)

def run_spec(config, bench_name):
    """[a function that call runspec program to run spec cpu]

    Args:
        config ([param]): [the configuration for spec 2006]
    """
    cmd = ["runspec", 
            "--config", config.config_file,
            "--tune", config.tune,
            "-C", "%d" %(config.copies),
            "--iterations", "%d" %(config.iterations),
            "-i", config.bench_size,
            "--noreportable",
            "--ignoreerror",
            bench_name
            ]
    Logger.info("Running with cmd %s", cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return out, err

def run_fake_spec(config, bench_name):
    """
    Just a fake function, pretending that run_spec function is called.
    Args:
        config (_type_): _description_
        bench_name (_type_): _description_
    """
    log_name = "CPU2006.113.log"
    cmd = ["cat", log_name]
    Logger.info("Running with cmd %s", cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return out, err

def find_best_job(jobs, tune, bench_name, bench_size):
    """find the job with the highest score in the jobs list
    Args:
        jobs_list (list): a list of the jobs
    Returns:
        idx(int):  the index of the job
    """
    idx = None
    if tune == "peak":
        if bench_size == "ref":# compare by final score.
            score = 0.0
            for i, job in enumerate(jobs):
                for r in job["result"]:
                    if job["benchmark_name"] == bench_name and r["Tune"] == tune and r["BenchSize"] == bench_size and job["final_score"] > score:
                        score = job["final_score"]
                        idx = i
            return idx
        elif bench_size in ["train", "test"]:
            run_time = 99999999.9
            for i, job in enumerate(jobs):
                for r in job["result"]:            
                    if job["benchmark_name"] == bench_name and r["Tune"] == tune and r["BenchSize"] == bench_size and r["RunTime"] < run_time:
                        run_time = r["RunTime"]
                        idx = i
            return idx
    elif tune == "base":
        if bench_size == "ref":
            score = 0.0
            for i, job in enumerate(jobs):
                if job["benchmark_name"] == bench_name and job["tune"] == tune and job["bench_size"] == bench_size and job["final_score"] > score:
                    score = job["final_score"]
                    idx = i
            return idx

def find_last_job(jobs, tune, bench_name, bench_size):
    """find the last job for given bench_name and bench_size

    Args:
        jobs (list): a list of the jobs.
        tune (str): peak or base
        bench_name (str): the name of the benchmark
        bench_size (str): the size of the benchmark
    """
    num_jobs = len(jobs)
    for i in range(num_jobs-1, 0, -1):
        job = jobs[i]
        if job["benchmark_name"] == bench_name and job["bench_size"] == bench_size and job["tune"] == tune:
            return i
    else:
        return None

def is_empty_flags(flags):
    """ if all the flags are empty, return true

    Args:
        flags (list): the gcc flags
    """
    for flag in flags:
        if len(flag) > 0:
            return False
    return True
    
def get_peak_flags(jobs, tune, bench_name, bench_size, langs):
    """get the peak flags in the jobs

    Args:
        jobs (list): a list of jobs. 
    """
    idx = find_best_job(jobs, tune, bench_name, bench_size)
    if idx is None:
        flags = []
        for lang in langs:
            flags.append([])
        return flags
    else:
        return jobs[idx]["gcc_flags"]

def get_next_option(flags, options):
    """ get the next option according to current flags.
    Args:
        flags ([type]): [description]
        options ([type]): [description]
    Returns:
        (int, str): 
    """
    if len(flags[0]) == 0:
        return (0, options[0])
    else:
        last_option = options[-1]
        for i, flag in enumerate(flags):
            last_flag = flag[-1]
            if last_flag == last_option:
                continue
            else:
                for j, option in enumerate(options):
                    if last_flag == option:
                        return (i, options[j+1])
    return (None, None)

def get_bench_number_name(tune, mystr):
    """get the benchmark number and name from the given string

    Returns:
        point_type, benchmark number, benchmark name
    """
    if tune == "peak":
        for point_type, v in Benchmarks.items():
            if mystr in v.keys():
                return (point_type, mystr, v[mystr]["name"])
        for point_type, v in Benchmarks.items():
            for bench_no, bench in v.items():
                if bench["name"] == mystr:
                    return (point_type, bench_no, mystr)
    elif tune == "base":
        if mystr in ["int", "fp"]:
            return (mystr, "base", mystr)
    return (None, None, None)

class param(object):
    """
    A class to read the config file.
    """
    def __init__(self, file_name):
        """
        Define some default value for parameters
        """
        # Set some necessary directories.
        self.home_dir = os.getcwd()
        self.jobs_file = os.path.join(self.home_dir, "jobs.json")
        self.result_dir = os.path.join(self.home_dir, "results")
        self.config_dir = os.path.join(self.home_dir, "config")
        self.program_dir = os.path.abspath(os.path.dirname(__file__))
        # set some config options.
        config = ConfigParser()
        config.read(file_name)
        # Set some common parameters for global minima search and TS calculations
        section = "common"
        self.config_file = config.get(section, "config_file")
        self.tune = config.get(section, "tune").strip().lower()
        self.copies = config.getint(section, "copies", fallback=1)
        self.iterations = config.getint(section, "iterations", fallback=1)
        self.bench_size = config.get(section, "bench_size", fallback="ref")
        benchmark_set = config.get(section, "benchmarks").strip().lower()
        if self.tune == "peak":
            #benchmark set could be int, fp, all, or a list of benchmarks.
            if benchmark_set == "int":
                self.benchmark_set = list(Benchmarks["int"].keys())
            elif benchmark_set == "fp":
                self.benchmark_set = list(Benchmarks["fp"].keys())
            elif benchmark_set == "all":
                self.benchmark_set = list(Benchmarks["int"].keys()) + list(Benchmarks["fp"].keys())
            else:
                self.benchmark_set = benchmark_set.split()
        elif self.tune == "base":
            #benchmark set could be int or fp
            self.benchmark_set = benchmark_set.split()
            Logger.info("The benchmark set is %s", self.benchmark_set)
            if self.bench_size != "ref":
                Logger.error("For base benchmark, the benchmark size must be \"ref\". Please modify the config file!")
                exit(1)
        self.compiler_option_file = config.get(section, "compiler_option_file")
        real_config_file = os.path.join(self.config_dir,self.config_file)
        with open(real_config_file, "r") as fp:
            self.config_lines = fp.readlines()
            fp.close()
        self.compiler_cfg = get_compiler_options(real_config_file)

    def to_dict(self):
        """convert the params to a python dict
        """
        my_dict = {}
        my_dict["tune"] = self.tune
        my_dict["copies"] = self.copies
        my_dict["iterations"] = self.iterations
        my_dict["benchmark_size"] = self.bench_size
        my_dict["benchmark"] = self.benchmark_set
        my_dict["config_file"] = self.config_file
        my_dict["compiler_option_file"] = self.compiler_option_file
        #my_dict["cfg_struct"] = self.cfg_struct
        return my_dict

class spec_job():
    """a class for descriping a SPEC 2006 benchmark
    """
    def __init__(self, spec_config:param, benchmark:str):
        """basic informtaion about a spec 2006 benchmark
        """
        self.spec_config = spec_config
        self.point_type, self.bench_no, self.bench_name = get_bench_number_name(spec_config.tune, benchmark)
        if spec_config.tune == "base":
            if self.bench_name == "int":
                self.langs = ["C", "C++"]
            elif self.bench_name == "fp":
                self.langs = ["C", "C++", "Fortran"]
            else:
                Logger.error("For tune == base, the benchmark name should be \"int\" or \"fp\"")
                exit(1)
        else:
            self.langs = Benchmarks[self.point_type][self.bench_no]["lang"]
        self.opt_flag_names = [OptMap[lang] for lang in self.langs]
        self.options = load_json(self.spec_config.compiler_option_file)
        if os.path.exists(self.spec_config.jobs_file):
            self.jobs = load_json(self.spec_config.jobs_file)
        else:
            self.jobs = []
        if self.spec_config.tune == "base" and benchmark in ["int", "fp"]:
            key = "%s_%s" % (benchmark, self.spec_config.tune)
            self.cfg_struct = self.spec_config.compiler_cfg[key]
        elif self.spec_config.tune == "peak":
            self.cfg_struct = self.spec_config.compiler_cfg[self.spec_config.tune][self.bench_no]
        self.spec_result = {}
        self.job_status = "Q"
        self.log_name = ""
        self.final_score = 0.0
        if len(self.jobs) > 0:
            last_job_idx = find_last_job(self.jobs, self.spec_config.tune, self.bench_name, self.spec_config.bench_size)
            if last_job_idx is not None:
                self.opt_flags = self.jobs[last_job_idx]["gcc_flags"]
            else:
                self.opt_flags = []
                for opt_flag in self.opt_flag_names:
                    self.opt_flags.append([])    
        else:
            self.opt_flags = []
            for opt_flag in self.opt_flag_names:
                self.opt_flags.append([])

    def run_spec(self):
        """run spec 2006 using current spec configuration and compiler configuration.
        """
        out, err = run_spec(self.spec_config, self.bench_name)
        #out, err = run_fake_spec(self.spec_config, self.bench_name)
        out_lines = out.split("\n")
        Logger.debug("Out Lines are\n%s", out_lines)
        self.log_name = get_log_name(out_lines)
        self.result = ExtractResFromLog(out_lines)
        self.final_score = self.get_final_score()
        Logger.info("The final score for benchmark %s is %f", self.bench_name, self.final_score)
        self.job_status = "C"
        self.jobs.append(self.to_dict())
        dump_json(self.jobs, self.spec_config.jobs_file)

    def get_final_score(self):
        """get the final score from the result, according to the benchmark configuration
        """
        res = self.result
        tune = self.spec_config.tune
        bench_size = self.spec_config.bench_size
        bench_no = self.bench_no
        bench_name = self.bench_name
        if tune == "base" and bench_name in ["fp", "int"]:
            return GetScore(filter_res(res, tune, bench_size, bench_name))
        else:
            ratios = []
            for r in res:
                if r["Tune"] == tune and r["BenchSize"] == bench_size and r["BenchNO"] == bench_no:
                    Logger.info("Current result is %s" ,r)
                    ratios.append(r["Ratio"])
            if len(ratios) == 0:
                Logger.warning("Benchmark of %s failed!" % (bench_name))
                return 0.0
            else:
                return sum(ratios)/len(ratios)

    def to_dict(self):
        """convert current info to db dict
        """
        db = {}
        db["job_status"] = self.job_status
        db["benchmark_number"] = self.bench_no
        db["bench_size"] = self.spec_config.bench_size
        db["tune"] = self.spec_config.tune
        db["benchmark_name"] = self.bench_name
        db["log_name"] = self.log_name
        db["result"] = self.result
        db["final_score"] = self.final_score
        db["gcc_flags"] = self.opt_flags
        return db
    
    def update_cfg(self):
        """ update current configuration and get a new cfg file.
        """
        if len(self.jobs) == 0:
            i, next_option = get_next_option(self.opt_flags, self.options)
            new_flags = copy.deepcopy(self.opt_flags)
            new_flags[i].append(next_option)
        else:
            Logger.info("Current optimization flags are %s", self.opt_flags)
            if is_empty_flags(self.opt_flags):
                new_flags = [[self.options[0]] for flag in self.opt_flags]
            else:
                i, next_option = get_next_option(self.opt_flags, self.options)
                if i is None:
                    Logger.info("No more options are available. Ending the optimization of %s", self.bench_name)
                    return False
                else:
                    peak_flags = get_peak_flags(self.jobs, self.spec_config.tune, self.bench_name, self.spec_config.bench_size, self.langs)
                    Logger.info("Current peak flags are %s", peak_flags)
                    new_flags = copy.deepcopy(peak_flags)
                    new_flags[i].append(next_option)
        Logger.info("New flags are %s", new_flags)
        self.opt_flags = new_flags
        new_cfg_lines = update_cfg_lines(self.spec_config.config_lines,
                                        self.opt_flag_names,
                                        self.cfg_struct, new_flags)
        real_config_file = os.path.join(self.spec_config.config_dir, self.spec_config.config_file )
        with open(real_config_file, "w") as fp:
            fp.writelines(new_cfg_lines)
            fp.close()
            return True

    def main(self):
        """
        main function of the auto spec program
        """
        while True:
            if not self.update_cfg():
                break
            self.run_spec()
        peak_flags = get_peak_flags(self.jobs, self.spec_config.tune, self.bench_name, self.spec_config.bench_size, self.langs)
        Logger.info("The best options for %s is: %s", self.bench_name, peak_flags)
        return True

if __name__ == "__main__":
    config = sys.argv[1]
    Logger.info("\n%s\nAutoSPEC started with pid %s \n%s", "#"*80, os.getpid(), "#"*80)
    Logger.info("Running AutoSPEC with configuration file %s", config)
    spec_config = param(config)
    tune = spec_config.tune
    for benchmark in spec_config.benchmark_set:
        point_type, bench_no, bench_name = get_bench_number_name(tune, benchmark)
        Logger.info("Optimizing the flags for %s benchmark %s.%s", point_type, bench_no, bench_name)
        job = spec_job(spec_config, benchmark)
        job.main()
        del job