#!/bin/bash

iverilog -g2001 -osimv -s ibex_id_stage_bench /home/debjit/Work/GoldMine/dev_static_miner_integ/RunTime/goldmine.out/ibex_id_stage/ibex_id_stage_bench.v /home/debjit/Work/GoldMine/dev_static_miner_integ/verilog/IBex/ibex_id_stage.v /home/debjit/Work/GoldMine/dev_static_miner_integ/verilog/IBex/ibex_decoder.v /home/debjit/Work/GoldMine/dev_static_miner_integ/verilog/IBex/ibex_controller.v /home/debjit/Work/GoldMine/dev_static_miner_integ/verilog/IBex/ibex_register_file_ff.v  -I/home/debjit/Work/GoldMine/dev_static_miner_integ/verilog/IBex