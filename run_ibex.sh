#!/bin/bash

python ../src/goldmine.py -m ibex_alu -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_alu
python ../src/goldmine.py -m ibex_compressed_decoder -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_compressed_decoder
python ../src/goldmine.py -m ibex_controller -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_controller
python ../src/goldmine.py -m ibex_decoder -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_decoder
python ../src/goldmine.py -m ibex_load_store_unit -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_load_store_unit
python ../src/goldmine.py -m ibex_multdiv_fast -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_multdiv_fast
python ../src/goldmine.py -m ibex_multdiv_slow -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_multdiv_slow
python ../src/goldmine.py -m ibex_id_stage -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_id_stage
python ../src/goldmine.py -m ibex_fetch_fifo -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_fetch_fifo
python ../src/goldmine.py -m ibex_pmp -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_pmp
python ../src/goldmine.py -m ibex_register_file -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_register_file_ff
python ../src/goldmine.py -m ibex_prefetch_buffer -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_prefetch_buffer
python ../src/goldmine.py -m ibex_ex_block -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_ex_block
python ../src/goldmine.py -m ibex_if_stage -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_if_stage
python ../src/goldmine.py -m prim_clock_gating -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_prim_clock_gating
#python ../src/goldmine.py -m ibex_cs_registers -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_cs_registers
#python ../src/goldmine.py -m ibex_core -c clk_i:1 -r rst_ni:0 -u ../ -I ../verilog/IBex -S -V -F ./vfiles/vfile_ibex_core -t rvfi_rs1_addr,rvfi_rs2_addr,rvfi_rs1_rdata,rvfi_rs2_rdata,rvfi_rd_addr,rvfi_rd_wdata,rvfi_insn,rvfi_trap,rvfi_halt,rvfi_intr,rvfi_mode
