#!/bin/bash

# NOTE: All command line paths are relative to the RunTime directory

python ../src/goldmine.py -m ibex_compressed_decoder -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_compressed_decoder
python ../src/goldmine.py -m ibex_controller -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_controller
python ../src/goldmine.py -m ibex_multdiv_slow -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_multdiv_slow

# Top-level only assertions for Ibex Id stage
python ../src/goldmine.py -m ibex_id_stage -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_id_stage
# Inter-modular assertions for Ibex Id stage (-N command line argument)
python ../src/goldmine.py -m ibex_id_stage -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -N -V -F ./vfiles/vfile_ibex_id_stage
