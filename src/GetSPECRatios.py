#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
# Time-stamp: <Last updated: ZHAO,Ya-Fan yafanzhao@163.com 2022-02-03 10:53:19>
# A simple script to print the ratios from the benchmark log file.
import sys
from AutoSPEC import parse_log_file

if __name__ == "__main__":
    log_file = sys.argv[1]
    parse_log_file(log_file)