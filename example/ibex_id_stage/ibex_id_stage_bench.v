`timescale 1ns/1ps

module ibex_id_stage_bench();

reg [31:0] regfile_wdata_lsu_i;
reg irq_pending_i;
reg fetch_enable_i;
reg [31:0] lsu_addr_last_i;
reg lsu_load_err_i;
reg csr_mtip_i;
reg csr_msip_i;
reg instr_valid_i;
reg csr_mstatus_tw_i;
reg instr_new_i;
reg lsu_valid_i;
reg lsu_addr_incr_req_i;
reg branch_decision_i;
reg [31:0] pc_id_i;
reg debug_single_step_i;
reg [15:0] instr_rdata_c_i;
reg instr_is_compressed_i;
reg csr_meip_i;
reg [31:0] instr_rdata_i;
reg illegal_c_insn_i;
reg instr_fetch_err_i;
reg rst_ni;
reg lsu_store_err_i;
reg irq_nm_i;
reg [1:0] priv_mode_i;
reg csr_mstatus_mie_i;
reg test_en_i;
reg [31:0] regfile_wdata_ex_i;
reg debug_ebreaku_i;
reg debug_ebreakm_i;
reg clk_i;
reg ex_valid_i;
reg [31:0] csr_rdata_i;
reg [14:0] csr_mfip_i;
reg illegal_csr_insn_i;
reg debug_req_i;

wire csr_access_o;
wire [1:0] multdiv_signed_mode_ex_o;
wire instr_valid_clear_o;
wire [31:0] data_wdata_ex_o;
wire [1:0] data_type_ex_o;
wire debug_csr_save_o;
wire [2:0] pc_mux_o;
wire [4:0] alu_operator_ex_o;
wire id_in_ready_o;
wire [31:0] multdiv_operand_b_ex_o;
wire csr_save_id_o;
wire csr_restore_mret_id_o;
wire [4:0] rfvi_reg_raddr_ra_o;
wire [31:0] rfvi_reg_wdata_rd_o;
wire [31:0] rfvi_reg_rdata_ra_o;
wire mult_en_ex_o;
wire data_we_ex_o;
wire csr_save_cause_o;
wire [1:0] exc_pc_mux_o;
wire [31:0] rfvi_reg_rdata_rb_o;
wire [31:0] csr_mtval_o;
wire [1:0] multdiv_operator_ex_o;
wire [2:0] debug_cause_o;
wire [5:0] exc_cause_o;
wire data_sign_ext_ex_o;
wire perf_tbranch_o;
wire csr_save_if_o;
wire instr_req_o;
wire [31:0] multdiv_operand_a_ex_o;
wire illegal_insn_o;
wire [4:0] rfvi_reg_raddr_rb_o;
wire div_en_ex_o;
wire debug_mode_o;
wire pc_set_o;
wire [31:0] alu_operand_a_ex_o;
wire [31:0] alu_operand_b_ex_o;
wire data_req_ex_o;
wire perf_jump_o;
wire instr_ret_o;
wire perf_branch_o;
wire csr_restore_dret_id_o;
wire rfvi_reg_we_o;
wire [1:0] csr_op_o;
wire instr_ret_compressed_o;
wire [4:0] rfvi_reg_waddr_rd_o;
wire ctrl_busy_o;

ibex_id_stage ibex_id_stage_ (
	.regfile_wdata_lsu_i(regfile_wdata_lsu_i),
	.irq_pending_i(irq_pending_i),
	.fetch_enable_i(fetch_enable_i),
	.lsu_addr_last_i(lsu_addr_last_i),
	.lsu_load_err_i(lsu_load_err_i),
	.csr_mtip_i(csr_mtip_i),
	.csr_msip_i(csr_msip_i),
	.instr_valid_i(instr_valid_i),
	.csr_mstatus_tw_i(csr_mstatus_tw_i),
	.instr_new_i(instr_new_i),
	.lsu_valid_i(lsu_valid_i),
	.lsu_addr_incr_req_i(lsu_addr_incr_req_i),
	.branch_decision_i(branch_decision_i),
	.pc_id_i(pc_id_i),
	.debug_single_step_i(debug_single_step_i),
	.instr_rdata_c_i(instr_rdata_c_i),
	.instr_is_compressed_i(instr_is_compressed_i),
	.csr_meip_i(csr_meip_i),
	.instr_rdata_i(instr_rdata_i),
	.illegal_c_insn_i(illegal_c_insn_i),
	.instr_fetch_err_i(instr_fetch_err_i),
	.rst_ni(rst_ni),
	.lsu_store_err_i(lsu_store_err_i),
	.irq_nm_i(irq_nm_i),
	.priv_mode_i(priv_mode_i),
	.csr_mstatus_mie_i(csr_mstatus_mie_i),
	.test_en_i(test_en_i),
	.regfile_wdata_ex_i(regfile_wdata_ex_i),
	.debug_ebreaku_i(debug_ebreaku_i),
	.debug_ebreakm_i(debug_ebreakm_i),
	.clk_i(clk_i),
	.ex_valid_i(ex_valid_i),
	.csr_rdata_i(csr_rdata_i),
	.csr_mfip_i(csr_mfip_i),
	.illegal_csr_insn_i(illegal_csr_insn_i),
	.debug_req_i(debug_req_i),
	.csr_access_o(csr_access_o),
	.multdiv_signed_mode_ex_o(multdiv_signed_mode_ex_o),
	.instr_valid_clear_o(instr_valid_clear_o),
	.data_wdata_ex_o(data_wdata_ex_o),
	.data_type_ex_o(data_type_ex_o),
	.debug_csr_save_o(debug_csr_save_o),
	.pc_mux_o(pc_mux_o),
	.alu_operator_ex_o(alu_operator_ex_o),
	.id_in_ready_o(id_in_ready_o),
	.multdiv_operand_b_ex_o(multdiv_operand_b_ex_o),
	.csr_save_id_o(csr_save_id_o),
	.csr_restore_mret_id_o(csr_restore_mret_id_o),
	.rfvi_reg_raddr_ra_o(rfvi_reg_raddr_ra_o),
	.rfvi_reg_wdata_rd_o(rfvi_reg_wdata_rd_o),
	.rfvi_reg_rdata_ra_o(rfvi_reg_rdata_ra_o),
	.mult_en_ex_o(mult_en_ex_o),
	.data_we_ex_o(data_we_ex_o),
	.csr_save_cause_o(csr_save_cause_o),
	.exc_pc_mux_o(exc_pc_mux_o),
	.rfvi_reg_rdata_rb_o(rfvi_reg_rdata_rb_o),
	.csr_mtval_o(csr_mtval_o),
	.multdiv_operator_ex_o(multdiv_operator_ex_o),
	.debug_cause_o(debug_cause_o),
	.exc_cause_o(exc_cause_o),
	.data_sign_ext_ex_o(data_sign_ext_ex_o),
	.perf_tbranch_o(perf_tbranch_o),
	.csr_save_if_o(csr_save_if_o),
	.instr_req_o(instr_req_o),
	.multdiv_operand_a_ex_o(multdiv_operand_a_ex_o),
	.illegal_insn_o(illegal_insn_o),
	.rfvi_reg_raddr_rb_o(rfvi_reg_raddr_rb_o),
	.div_en_ex_o(div_en_ex_o),
	.debug_mode_o(debug_mode_o),
	.pc_set_o(pc_set_o),
	.alu_operand_a_ex_o(alu_operand_a_ex_o),
	.alu_operand_b_ex_o(alu_operand_b_ex_o),
	.data_req_ex_o(data_req_ex_o),
	.perf_jump_o(perf_jump_o),
	.instr_ret_o(instr_ret_o),
	.perf_branch_o(perf_branch_o),
	.csr_restore_dret_id_o(csr_restore_dret_id_o),
	.rfvi_reg_we_o(rfvi_reg_we_o),
	.csr_op_o(csr_op_o),
	.instr_ret_compressed_o(instr_ret_compressed_o),
	.rfvi_reg_waddr_rd_o(rfvi_reg_waddr_rd_o),
	.ctrl_busy_o(ctrl_busy_o));

	initial begin
		$dumpfile("/home/debjit/Work/GoldMine/dev_static_miner_integ/RunTime/goldmine.out/ibex_id_stage/ibex_id_stage.vcd");
		$dumpvars(0, ibex_id_stage_bench.ibex_id_stage_);
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
		regfile_wdata_lsu_i = $random;
		irq_pending_i = $random;
		fetch_enable_i = $random;
		lsu_addr_last_i = $random;
		lsu_load_err_i = $random;
		csr_mtip_i = $random;
		csr_msip_i = $random;
		instr_valid_i = $random;
		csr_mstatus_tw_i = $random;
		instr_new_i = $random;
		lsu_valid_i = $random;
		lsu_addr_incr_req_i = $random;
		branch_decision_i = $random;
		pc_id_i = $random;
		debug_single_step_i = $random;
		instr_rdata_c_i = $random;
		instr_is_compressed_i = $random;
		csr_meip_i = $random;
		instr_rdata_i = $random;
		illegal_c_insn_i = $random;
		instr_fetch_err_i = $random;
		lsu_store_err_i = $random;
		irq_nm_i = $random;
		priv_mode_i = $random;
		csr_mstatus_mie_i = $random;
		test_en_i = $random;
		regfile_wdata_ex_i = $random;
		debug_ebreaku_i = $random;
		debug_ebreakm_i = $random;
		ex_valid_i = $random;
		csr_rdata_i = $random;
		csr_mfip_i = $random;
		illegal_csr_insn_i = $random;
		debug_req_i = $random;
		#26;
	end

endmodule