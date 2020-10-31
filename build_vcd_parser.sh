#!/bin/bash

PWD=`pwd`

cd ${PWD}/src/vcd_parser
python setup.py build_ext --inplace
ln -s ${PWD}/vcd_parser/parse_timeframes.so
cd ${PWD}/RunTime
python ${PWD}/src/goldmine.py -h
