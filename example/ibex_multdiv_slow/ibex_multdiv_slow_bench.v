`timescale 1ns/1ps

module ibex_multdiv_slow_bench();

reg rst_ni;
reg [33:0] alu_adder_ext_i;
reg div_en_i;
reg [31:0] op_a_i;
reg [1:0] operator_i;
reg mult_en_i;
reg [1:0] signed_mode_i;
reg clk_i;
reg [31:0] alu_adder_i;
reg equal_to_zero;
reg [31:0] op_b_i;

wire valid_o;
wire [32:0] alu_operand_a_o;
wire [32:0] alu_operand_b_o;
wire [31:0] multdiv_result_o;

ibex_multdiv_slow ibex_multdiv_slow_ (
	.rst_ni(rst_ni),
	.alu_adder_ext_i(alu_adder_ext_i),
	.div_en_i(div_en_i),
	.op_a_i(op_a_i),
	.operator_i(operator_i),
	.mult_en_i(mult_en_i),
	.signed_mode_i(signed_mode_i),
	.clk_i(clk_i),
	.alu_adder_i(alu_adder_i),
	.equal_to_zero(equal_to_zero),
	.op_b_i(op_b_i),
	.valid_o(valid_o),
	.alu_operand_a_o(alu_operand_a_o),
	.alu_operand_b_o(alu_operand_b_o),
	.multdiv_result_o(multdiv_result_o));

	initial begin
		$dumpfile("/scratch/users/dp638/Work/Important/gm_static_miner_integ/RunTime/goldmine.out/ibex_multdiv_slow/ibex_multdiv_slow.vcd");
		$dumpvars(0, ibex_multdiv_slow_bench.ibex_multdiv_slow_);
		clk_i = 1;
		rst_ni = 0;
		#26;
		rst_ni = 1;
		#50000 $finish;
	end

	always begin
		#25 clk_i = ~clk_i;
	end

	always begin
		#24;
		alu_adder_ext_i = $random;
		div_en_i = $random;
		op_a_i = $random;
		operator_i = $random;
		mult_en_i = $random;
		signed_mode_i = $random;
		alu_adder_i = $random;
		equal_to_zero = $random;
		op_b_i = $random;
		#26;
	end

endmodule