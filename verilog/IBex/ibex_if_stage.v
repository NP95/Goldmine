module ibex_if_stage (
	clk_i,
	rst_ni,
	boot_addr_i,
	req_i,
	instr_req_o,
	instr_addr_o,
	instr_gnt_i,
	instr_rvalid_i,
	instr_rdata_i,
	instr_err_i,
	instr_pmp_err_i,
	instr_valid_id_o,
	instr_new_id_o,
	instr_rdata_id_o,
	instr_rdata_c_id_o,
	instr_is_compressed_id_o,
	instr_fetch_err_o,
	illegal_c_insn_id_o,
	pc_if_o,
	pc_id_o,
	instr_valid_clear_i,
	pc_set_i,
	pc_mux_i,
	exc_pc_mux_i,
	exc_cause,
	jump_target_ex_i,
	csr_mepc_i,
	csr_depc_i,
	csr_mtvec_i,
	csr_mtvec_init_o,
	id_in_ready_i,
	if_busy_o,
	perf_imiss_o
);
	parameter [31:0] DmHaltAddr = 32'h1A110800;
	parameter [31:0] DmExceptionAddr = 32'h1A110808;
	input wire clk_i;
	input wire rst_ni;
	input wire [31:0] boot_addr_i;
	input wire req_i;
	output wire instr_req_o;
	output wire [31:0] instr_addr_o;
	input wire instr_gnt_i;
	input wire instr_rvalid_i;
	input wire [31:0] instr_rdata_i;
	input wire instr_err_i;
	input wire instr_pmp_err_i;
	output reg instr_valid_id_o;
	output reg instr_new_id_o;
	output reg [31:0] instr_rdata_id_o;
	output reg [15:0] instr_rdata_c_id_o;
	output reg instr_is_compressed_id_o;
	output reg instr_fetch_err_o;
	output reg illegal_c_insn_id_o;
	output wire [31:0] pc_if_o;
	output reg [31:0] pc_id_o;
	input wire instr_valid_clear_i;
	input wire pc_set_i;
	input wire [2:0] pc_mux_i;
	input wire [1:0] exc_pc_mux_i;
	input wire [5:0] exc_cause;
	input wire [31:0] jump_target_ex_i;
	input wire [31:0] csr_mepc_i;
	input wire [31:0] csr_depc_i;
	input wire [31:0] csr_mtvec_i;
	output wire csr_mtvec_init_o;
	input wire id_in_ready_i;
	output wire if_busy_o;
	output wire perf_imiss_o;
	`include "ibex_pkg.v"
	reg offset_in_init_d;
	reg offset_in_init_q;
	reg have_instr;
	wire prefetch_busy;
	reg branch_req;
	reg [31:0] fetch_addr_n;
	wire fetch_valid;
	reg fetch_ready;
	wire [31:0] fetch_rdata;
	wire [31:0] fetch_addr;
	wire fetch_err;
	reg [31:0] exc_pc;
	wire [5:0] irq_id;
	wire unused_irq_bit;
	wire if_id_pipe_reg_we;
	wire [7:0] unused_boot_addr;
	wire [7:0] unused_csr_mtvec;
	assign unused_boot_addr = boot_addr_i[7:0];
	assign unused_csr_mtvec = csr_mtvec_i[7:0];
	assign irq_id = exc_cause;
	assign unused_irq_bit = irq_id[5];
	always @(*) begin : exc_pc_mux
		case (exc_pc_mux_i)
			EXC_PC_EXC: exc_pc = {csr_mtvec_i[31:8], 8'h00};
			EXC_PC_IRQ: exc_pc = {csr_mtvec_i[31:8], 1'b0, irq_id[4:0], 2'b00};
			EXC_PC_DBD: exc_pc = DmHaltAddr;
			EXC_PC_DBG_EXC: exc_pc = DmExceptionAddr;
			default: exc_pc = 1'bX;
		endcase
	end
	always @(*) begin : fetch_addr_mux
		case (pc_mux_i)
			PC_BOOT: fetch_addr_n = {boot_addr_i[31:8], 8'h80};
			PC_JUMP: fetch_addr_n = jump_target_ex_i;
			PC_EXC: fetch_addr_n = exc_pc;
			PC_ERET: fetch_addr_n = csr_mepc_i;
			PC_DRET: fetch_addr_n = csr_depc_i;
			default: fetch_addr_n = 1'bX;
		endcase
	end
	assign csr_mtvec_init_o = ((pc_mux_i == PC_BOOT) & pc_set_i);
	ibex_prefetch_buffer prefetch_buffer_i(
		.clk_i(clk_i),
		.rst_ni(rst_ni),
		.req_i(req_i),
		.branch_i(branch_req),
		.addr_i({fetch_addr_n[31:1], 1'b0}),
		.ready_i(fetch_ready),
		.valid_o(fetch_valid),
		.rdata_o(fetch_rdata),
		.addr_o(fetch_addr),
		.err_o(fetch_err),
		.instr_req_o(instr_req_o),
		.instr_addr_o(instr_addr_o),
		.instr_gnt_i(instr_gnt_i),
		.instr_rvalid_i(instr_rvalid_i),
		.instr_rdata_i(instr_rdata_i),
		.instr_err_i(instr_err_i),
		.instr_pmp_err_i(instr_pmp_err_i),
		.busy_o(prefetch_busy)
	);
	always @(posedge clk_i or negedge rst_ni)
		if (!rst_ni)
			offset_in_init_q <= 1'b1;
		else
			offset_in_init_q <= offset_in_init_d;
	always @(*) begin
		offset_in_init_d = offset_in_init_q;
		fetch_ready = 1'b0;
		branch_req = 1'b0;
		have_instr = 1'b0;
		if (offset_in_init_q) begin
			if (req_i) begin
				branch_req = 1'b1;
				offset_in_init_d = 1'b0;
			end
		end
		else if (fetch_valid) begin
			have_instr = 1'b1;
			if ((req_i && if_id_pipe_reg_we)) begin
				fetch_ready = 1'b1;
				offset_in_init_d = 1'b0;
			end
		end
		if (pc_set_i) begin
			have_instr = 1'b0;
			branch_req = 1'b1;
			offset_in_init_d = 1'b0;
		end
	end
	assign pc_if_o = fetch_addr;
	assign if_busy_o = prefetch_busy;
	assign perf_imiss_o = (~fetch_valid | branch_req);
	wire [31:0] instr_decompressed;
	wire illegal_c_insn;
	wire instr_is_compressed_int;
	ibex_compressed_decoder compressed_decoder_i(
		.instr_i(fetch_rdata),
		.instr_o(instr_decompressed),
		.is_compressed_o(instr_is_compressed_int),
		.illegal_instr_o(illegal_c_insn)
	);
	assign if_id_pipe_reg_we = (have_instr & id_in_ready_i);
	always @(posedge clk_i or negedge rst_ni) begin : if_id_pipeline_regs
		if (!rst_ni) begin
			instr_new_id_o <= 1'b0;
			instr_valid_id_o <= 1'b0;
			instr_rdata_id_o <= 1'b0;
			instr_fetch_err_o <= 1'b0;
			instr_rdata_c_id_o <= 1'b0;
			instr_is_compressed_id_o <= 1'b0;
			illegal_c_insn_id_o <= 1'b0;
			pc_id_o <= 1'b0;
		end
		else begin
			instr_new_id_o <= if_id_pipe_reg_we;
			if (if_id_pipe_reg_we) begin
				instr_valid_id_o <= 1'b1;
				instr_rdata_id_o <= instr_decompressed;
				instr_fetch_err_o <= fetch_err;
				instr_rdata_c_id_o <= fetch_rdata[15:0];
				instr_is_compressed_id_o <= instr_is_compressed_int;
				illegal_c_insn_id_o <= illegal_c_insn;
				pc_id_o <= pc_if_o;
			end
			else if (instr_valid_clear_i)
				instr_valid_id_o <= 1'b0;
		end
	end
endmodule
