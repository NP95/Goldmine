module ibex_multdiv_fast (
	clk_i,
	rst_ni,
	mult_en_i,
	div_en_i,
	operator_i,
	signed_mode_i,
	op_a_i,
	op_b_i,
	alu_adder_ext_i,
	alu_adder_i,
	equal_to_zero,
	alu_operand_a_o,
	alu_operand_b_o,
	multdiv_result_o,
	valid_o
);
	localparam [1:0] ALBL = 0;
	localparam [2:0] MD_IDLE = 0;
	localparam [1:0] ALBH = 1;
	localparam [2:0] MD_ABS_A = 1;
	localparam [1:0] AHBL = 2;
	localparam [2:0] MD_ABS_B = 2;
	localparam [1:0] AHBH = 3;
	localparam [2:0] MD_COMP = 3;
	localparam [2:0] MD_LAST = 4;
	localparam [2:0] MD_CHANGE_SIGN = 5;
	localparam [2:0] MD_FINISH = 6;
	input wire clk_i;
	input wire rst_ni;
	input wire mult_en_i;
	input wire div_en_i;
	input wire [1:0] operator_i;
	input wire [1:0] signed_mode_i;
	input wire [31:0] op_a_i;
	input wire [31:0] op_b_i;
	input wire [33:0] alu_adder_ext_i;
	input wire [31:0] alu_adder_i;
	input wire equal_to_zero;
	output reg [32:0] alu_operand_a_o;
	output reg [32:0] alu_operand_b_o;
	output wire [31:0] multdiv_result_o;
	output wire valid_o;
	`include "ibex_pkg.v"
	reg [4:0] div_counter_q;
	reg [4:0] div_counter_n;
	reg [1:0] mult_state_q;
	reg [1:0] mult_state_n;
	reg [2:0] md_state_q;
	reg [2:0] md_state_n;
	wire signed [34:0] mac_res_signed;
	wire [34:0] mac_res_ext;
	reg [33:0] mac_res_q;
	reg [33:0] mac_res_n;
	wire [33:0] mac_res;
	reg [33:0] op_remainder_n;
	reg [15:0] mult_op_a;
	reg [15:0] mult_op_b;
	reg [33:0] accum;
	reg sign_a;
	reg sign_b;
	wire div_sign_a;
	wire div_sign_b;
	wire signed_mult;
	reg is_greater_equal;
	wire div_change_sign;
	wire rem_change_sign;
	wire [31:0] one_shift;
	reg [31:0] op_denominator_q;
	reg [31:0] op_numerator_q;
	reg [31:0] op_quotient_q;
	reg [31:0] op_denominator_n;
	reg [31:0] op_numerator_n;
	reg [31:0] op_quotient_n;
	wire [31:0] next_remainder;
	wire [32:0] next_quotient;
	wire [32:0] res_adder_h;
	reg mult_valid;
	reg div_valid;
	always @(posedge clk_i or negedge rst_ni) begin : proc_mult_state_q
		if (!rst_ni) begin
			mult_state_q <= ALBL;
			mac_res_q <= 1'sb0;
			div_counter_q <= 1'sb0;
			md_state_q <= MD_IDLE;
			op_denominator_q <= 1'sb0;
			op_numerator_q <= 1'sb0;
			op_quotient_q <= 1'sb0;
		end
		else begin
			if (mult_en_i)
				mult_state_q <= mult_state_n;
			if (div_en_i) begin
				div_counter_q <= div_counter_n;
				op_denominator_q <= op_denominator_n;
				op_numerator_q <= op_numerator_n;
				op_quotient_q <= op_quotient_n;
				md_state_q <= md_state_n;
			end
			case (1'b1)
				mult_en_i: mac_res_q <= mac_res_n;
				div_en_i: mac_res_q <= op_remainder_n;
				default: mac_res_q <= mac_res_q;
			endcase
		end
	end
	assign signed_mult = (signed_mode_i != 2'b00);
	assign multdiv_result_o = (div_en_i ? mac_res_q[31:0] : mac_res_n[31:0]);
	assign mac_res_signed = (($signed({sign_a, mult_op_a}) * $signed({sign_b, mult_op_b})) + $signed(accum));
	assign mac_res_ext = $unsigned(mac_res_signed);
	assign mac_res = mac_res_ext[33:0];
	assign res_adder_h = alu_adder_ext_i[33:1];
	assign next_remainder = (is_greater_equal ? res_adder_h[31:0] : mac_res_q[31:0]);
	assign next_quotient = (is_greater_equal ? ({1'b0, op_quotient_q} | {1'b0, one_shift}) : {1'b0, op_quotient_q});
	assign one_shift = ({31'b0, 1'b1} << div_counter_q);
	always @(*)
		if (((mac_res_q[31] ^ op_denominator_q[31]) == 1'b0))
			is_greater_equal = (res_adder_h[31] == 1'b0);
		else
			is_greater_equal = mac_res_q[31];
	assign div_sign_a = (op_a_i[31] & signed_mode_i[0]);
	assign div_sign_b = (op_b_i[31] & signed_mode_i[1]);
	assign div_change_sign = (div_sign_a ^ div_sign_b);
	assign rem_change_sign = div_sign_a;
	always @(*) begin : md_fsm
		div_counter_n = (div_counter_q - 5'h1);
		op_remainder_n = mac_res_q;
		op_quotient_n = op_quotient_q;
		md_state_n = md_state_q;
		op_numerator_n = op_numerator_q;
		op_denominator_n = op_denominator_q;
		alu_operand_a_o = {32'h0, 1'b1};
		alu_operand_b_o = {~op_b_i, 1'b1};
		div_valid = 1'b0;
		case (md_state_q)
			MD_IDLE: begin
				if ((operator_i == MD_OP_DIV)) begin
					op_remainder_n = 1'sb1;
					md_state_n = (equal_to_zero ? MD_FINISH : MD_ABS_A);
				end
				else begin
					op_remainder_n = {2'b0, op_a_i};
					md_state_n = (equal_to_zero ? MD_FINISH : MD_ABS_A);
				end
				alu_operand_a_o = {32'h0, 1'b1};
				alu_operand_b_o = {~op_b_i, 1'b1};
				div_counter_n = 5'd31;
			end
			MD_ABS_A: begin
				op_quotient_n = 1'sb0;
				op_numerator_n = (div_sign_a ? alu_adder_i : op_a_i);
				md_state_n = MD_ABS_B;
				div_counter_n = 5'd31;
				alu_operand_a_o = {32'h0, 1'b1};
				alu_operand_b_o = {~op_a_i, 1'b1};
			end
			MD_ABS_B: begin
				op_remainder_n = {33'h0, op_numerator_q[31]};
				op_denominator_n = (div_sign_b ? alu_adder_i : op_b_i);
				md_state_n = MD_COMP;
				div_counter_n = 5'd31;
				alu_operand_a_o = {32'h0, 1'b1};
				alu_operand_b_o = {~op_b_i, 1'b1};
			end
			MD_COMP: begin
				op_remainder_n = {1'b0, next_remainder[31:0], op_numerator_q[div_counter_n]};
				op_quotient_n = next_quotient[31:0];
				md_state_n = ((div_counter_q == 5'd1) ? MD_LAST : MD_COMP);
				alu_operand_a_o = {mac_res_q[31:0], 1'b1};
				alu_operand_b_o = {~op_denominator_q[31:0], 1'b1};
			end
			MD_LAST: begin
				if ((operator_i == MD_OP_DIV))
					op_remainder_n = {1'b0, next_quotient};
				else
					op_remainder_n = {2'b0, next_remainder[31:0]};
				alu_operand_a_o = {mac_res_q[31:0], 1'b1};
				alu_operand_b_o = {~op_denominator_q[31:0], 1'b1};
				md_state_n = MD_CHANGE_SIGN;
			end
			MD_CHANGE_SIGN: begin
				md_state_n = MD_FINISH;
				if ((operator_i == MD_OP_DIV))
					op_remainder_n = (div_change_sign ? {2'h0, alu_adder_i} : mac_res_q);
				else
					op_remainder_n = (rem_change_sign ? {2'h0, alu_adder_i} : mac_res_q);
				alu_operand_a_o = {32'h0, 1'b1};
				alu_operand_b_o = {~mac_res_q[31:0], 1'b1};
			end
			MD_FINISH: begin
				md_state_n = MD_IDLE;
				div_valid = 1'b1;
			end
			default: md_state_n = 1'bX;
		endcase
	end
	assign valid_o = (mult_valid | div_valid);
	always @(*) begin : mult_fsm
		mult_op_a = op_a_i[15:0];
		mult_op_b = op_b_i[15:0];
		sign_a = 1'b0;
		sign_b = 1'b0;
		accum = mac_res_q;
		mac_res_n = mac_res;
		mult_state_n = mult_state_q;
		mult_valid = 1'b0;
		case (mult_state_q)
			ALBL: begin
				mult_op_a = op_a_i[15:0];
				mult_op_b = op_b_i[15:0];
				sign_a = 1'b0;
				sign_b = 1'b0;
				accum = 1'sb0;
				mac_res_n = mac_res;
				mult_state_n = ALBH;
			end
			ALBH: begin
				mult_op_a = op_a_i[15:0];
				mult_op_b = op_b_i[31:16];
				sign_a = 1'b0;
				sign_b = (signed_mode_i[1] & op_b_i[31]);
				accum = {18'b0, mac_res_q[31:16]};
				if ((operator_i == MD_OP_MULL))
					mac_res_n = {2'b0, mac_res[15:0], mac_res_q[15:0]};
				else
					mac_res_n = mac_res;
				mult_state_n = AHBL;
			end
			AHBL: begin
				mult_op_a = op_a_i[31:16];
				mult_op_b = op_b_i[15:0];
				sign_a = (signed_mode_i[0] & op_a_i[31]);
				sign_b = 1'b0;
				if ((operator_i == MD_OP_MULL)) begin
					accum = {18'b0, mac_res_q[31:16]};
					mac_res_n = {2'b0, mac_res[15:0], mac_res_q[15:0]};
					mult_valid = 1'b1;
					mult_state_n = ALBL;
				end
				else begin
					accum = mac_res_q;
					mac_res_n = mac_res;
					mult_state_n = AHBH;
				end
			end
			AHBH: begin
				mult_op_a = op_a_i[31:16];
				mult_op_b = op_b_i[31:16];
				sign_a = (signed_mode_i[0] & op_a_i[31]);
				sign_b = (signed_mode_i[1] & op_b_i[31]);
				accum[17:0] = mac_res_q[33:16];
				accum[33:18] = {16 {(signed_mult & mac_res_q[33])}};
				mac_res_n = mac_res;
				mult_state_n = ALBL;
				mult_valid = 1'b1;
			end
			default: mult_state_n = 1'bX;
		endcase
	end
endmodule
