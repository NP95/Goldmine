module ibex_ex_block (
	clk_i,
	rst_ni,
	alu_operator_i,
	alu_operand_a_i,
	alu_operand_b_i,
	multdiv_operator_i,
	mult_en_i,
	div_en_i,
	multdiv_signed_mode_i,
	multdiv_operand_a_i,
	multdiv_operand_b_i,
	alu_adder_result_ex_o,
	regfile_wdata_ex_o,
	jump_target_o,
	branch_decision_o,
	ex_valid_o
);
	parameter RV32M = 1;
	parameter MultiplierImplementation = "fast";
	input wire clk_i;
	input wire rst_ni;
	input wire [4:0] alu_operator_i;
	input wire [31:0] alu_operand_a_i;
	input wire [31:0] alu_operand_b_i;
	input wire [1:0] multdiv_operator_i;
	input wire mult_en_i;
	input wire div_en_i;
	input wire [1:0] multdiv_signed_mode_i;
	input wire [31:0] multdiv_operand_a_i;
	input wire [31:0] multdiv_operand_b_i;
	output wire [31:0] alu_adder_result_ex_o;
	output wire [31:0] regfile_wdata_ex_o;
	output wire [31:0] jump_target_o;
	output wire branch_decision_o;
	output wire ex_valid_o;
	`include "ibex_pkg.v"
	wire [31:0] alu_result;
	wire [31:0] multdiv_result;
	wire [32:0] multdiv_alu_operand_b;
	wire [32:0] multdiv_alu_operand_a;
	wire [33:0] alu_adder_result_ext;
	wire alu_cmp_result;
	wire alu_is_equal_result;
	wire multdiv_valid;
	wire multdiv_en_sel;
	wire multdiv_en;
	generate
		if (RV32M) begin : gen_multdiv_m
			assign multdiv_en_sel = ((MultiplierImplementation == "fast") ? div_en_i : (mult_en_i | div_en_i));
			assign multdiv_en = (mult_en_i | div_en_i);
		end
		else begin : gen_multdiv_no_m
			assign multdiv_en_sel = 1'b0;
			assign multdiv_en = 1'b0;
		end
	endgenerate
	assign regfile_wdata_ex_o = (multdiv_en ? multdiv_result : alu_result);
	assign branch_decision_o = alu_cmp_result;
	assign jump_target_o = alu_adder_result_ex_o;
	ibex_alu alu_i(
		.operator_i(alu_operator_i),
		.operand_a_i(alu_operand_a_i),
		.operand_b_i(alu_operand_b_i),
		.multdiv_operand_a_i(multdiv_alu_operand_a),
		.multdiv_operand_b_i(multdiv_alu_operand_b),
		.multdiv_en_i(multdiv_en_sel),
		.adder_result_o(alu_adder_result_ex_o),
		.adder_result_ext_o(alu_adder_result_ext),
		.result_o(alu_result),
		.comparison_result_o(alu_cmp_result),
		.is_equal_result_o(alu_is_equal_result)
	);
	/*
	generate
		if ((MultiplierImplementation == "slow")) begin : gen_multdiv_slow
			ibex_multdiv_slow multdiv_i(
				.clk_i(clk_i),
				.rst_ni(rst_ni),
				.mult_en_i(mult_en_i),
				.div_en_i(div_en_i),
				.operator_i(multdiv_operator_i),
				.signed_mode_i(multdiv_signed_mode_i),
				.op_a_i(multdiv_operand_a_i),
				.op_b_i(multdiv_operand_b_i),
				.alu_adder_ext_i(alu_adder_result_ext),
				.alu_adder_i(alu_adder_result_ex_o),
				.equal_to_zero(alu_is_equal_result),
				.valid_o(multdiv_valid),
				.alu_operand_a_o(multdiv_alu_operand_a),
				.alu_operand_b_o(multdiv_alu_operand_b),
				.multdiv_result_o(multdiv_result)
			);
		end
		else if ((MultiplierImplementation == "fast")) begin : gen_multdiv_fast
	*/
			ibex_multdiv_fast multdiv_i(
				.clk_i(clk_i),
				.rst_ni(rst_ni),
				.mult_en_i(mult_en_i),
				.div_en_i(div_en_i),
				.operator_i(multdiv_operator_i),
				.signed_mode_i(multdiv_signed_mode_i),
				.op_a_i(multdiv_operand_a_i),
				.op_b_i(multdiv_operand_b_i),
				.alu_operand_a_o(multdiv_alu_operand_a),
				.alu_operand_b_o(multdiv_alu_operand_b),
				.alu_adder_ext_i(alu_adder_result_ext),
				.alu_adder_i(alu_adder_result_ex_o),
				.equal_to_zero(alu_is_equal_result),
				.valid_o(multdiv_valid),
				.multdiv_result_o(multdiv_result)
			);
	/*
		end
	endgenerate
	*/
	assign ex_valid_o = (multdiv_en ? multdiv_valid : 1'b1);
endmodule
