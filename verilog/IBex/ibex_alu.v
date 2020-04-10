module ibex_alu (
	operator_i,
	operand_a_i,
	operand_b_i,
	multdiv_operand_a_i,
	multdiv_operand_b_i,
	multdiv_en_i,
	adder_result_o,
	adder_result_ext_o,
	result_o,
	comparison_result_o,
	is_equal_result_o
);
	input wire [4:0] operator_i;
	input wire [31:0] operand_a_i;
	input wire [31:0] operand_b_i;
	input wire [32:0] multdiv_operand_a_i;
	input wire [32:0] multdiv_operand_b_i;
	input wire multdiv_en_i;
	output wire [31:0] adder_result_o;
	output wire [33:0] adder_result_ext_o;
	output reg [31:0] result_o;
	output wire comparison_result_o;
	output wire is_equal_result_o;
	`include "ibex_pkg.v"
	wire [31:0] operand_a_rev;
	wire [32:0] operand_b_neg;
	generate
		genvar gen_rev_operand_a_k;
		for (gen_rev_operand_a_k = 0; (gen_rev_operand_a_k < 32); gen_rev_operand_a_k = (gen_rev_operand_a_k + 1)) begin : gen_rev_operand_a
			assign operand_a_rev[gen_rev_operand_a_k] = operand_a_i[(31 - gen_rev_operand_a_k)];
		end
	endgenerate
	reg adder_op_b_negate;
	wire [32:0] adder_in_a;
	wire [32:0] adder_in_b;
	wire [31:0] adder_result;
	always @(*) begin
		adder_op_b_negate = 1'b0;
		case (operator_i)
			ALU_SUB, ALU_EQ, ALU_NE, ALU_GE, ALU_GEU, ALU_LT, ALU_LTU, ALU_SLT, ALU_SLTU: adder_op_b_negate = 1'b1;
			default: ;
		endcase
	end
	assign adder_in_a = (multdiv_en_i ? multdiv_operand_a_i : {operand_a_i, 1'b1});
	assign operand_b_neg = ({operand_b_i, 1'b0} ^ {33 {adder_op_b_negate}});
	assign adder_in_b = (multdiv_en_i ? multdiv_operand_b_i : operand_b_neg);
	assign adder_result_ext_o = ($unsigned(adder_in_a) + $unsigned(adder_in_b));
	assign adder_result = adder_result_ext_o[32:1];
	assign adder_result_o = adder_result;
	wire shift_left;
	wire shift_arithmetic;
	wire [4:0] shift_amt;
	wire [31:0] shift_op_a;
	wire [31:0] shift_result;
	wire [31:0] shift_right_result;
	wire [31:0] shift_left_result;
	assign shift_amt = operand_b_i[4:0];
	assign shift_left = (operator_i == ALU_SLL);
	assign shift_arithmetic = (operator_i == ALU_SRA);
	assign shift_op_a = (shift_left ? operand_a_rev : operand_a_i);
	wire [32:0] shift_op_a_32;
	assign shift_op_a_32 = {(shift_arithmetic & shift_op_a[31]), shift_op_a};
	wire signed [32:0] shift_right_result_signed;
	wire [32:0] shift_right_result_ext;
	assign shift_right_result_signed = ($signed(shift_op_a_32) >>> shift_amt[4:0]);
	assign shift_right_result_ext = $unsigned(shift_right_result_signed);
	assign shift_right_result = shift_right_result_ext[31:0];
	generate
		genvar gen_rev_shift_right_result_j;
		for (gen_rev_shift_right_result_j = 0; (gen_rev_shift_right_result_j < 32); gen_rev_shift_right_result_j = (gen_rev_shift_right_result_j + 1)) begin : gen_rev_shift_right_result
			assign shift_left_result[gen_rev_shift_right_result_j] = shift_right_result[(31 - gen_rev_shift_right_result_j)];
		end
	endgenerate
	assign shift_result = (shift_left ? shift_left_result : shift_right_result);
	wire is_equal;
	reg is_greater_equal;
	reg cmp_signed;
	always @(*) begin
		cmp_signed = 1'b0;
		case (operator_i)
			ALU_GE, ALU_LT, ALU_SLT: cmp_signed = 1'b1;
			default: ;
		endcase
	end
	assign is_equal = (adder_result == 32'b0);
	assign is_equal_result_o = is_equal;
	always @(*)
		if (((operand_a_i[31] ^ operand_b_i[31]) == 1'b0))
			is_greater_equal = (adder_result[31] == 1'b0);
		else
			is_greater_equal = (operand_a_i[31] ^ cmp_signed);
	reg cmp_result;
	always @(*) begin
		cmp_result = is_equal;
		case (operator_i)
			ALU_EQ: cmp_result = is_equal;
			ALU_NE: cmp_result = ~is_equal;
			ALU_GE, ALU_GEU: cmp_result = is_greater_equal;
			ALU_LT, ALU_LTU, ALU_SLT, ALU_SLTU: cmp_result = ~is_greater_equal;
			default: ;
		endcase
	end
	assign comparison_result_o = cmp_result;
	always @(*) begin
		result_o = 1'sb0;
		case (operator_i)
			ALU_AND: result_o = (operand_a_i & operand_b_i);
			ALU_OR: result_o = (operand_a_i | operand_b_i);
			ALU_XOR: result_o = (operand_a_i ^ operand_b_i);
			ALU_ADD, ALU_SUB: result_o = adder_result;
			ALU_SLL, ALU_SRL, ALU_SRA: result_o = shift_result;
			ALU_EQ, ALU_NE, ALU_GE, ALU_GEU, ALU_LT, ALU_LTU, ALU_SLT, ALU_SLTU: result_o = {31'h0, cmp_result};
			default: ;
		endcase
	end
endmodule
