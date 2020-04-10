module ibex_core (
	clk_i,
	rst_ni,
	test_en_i,
	hart_id_i,
	boot_addr_i,
	instr_req_o,
	instr_gnt_i,
	instr_rvalid_i,
	instr_addr_o,
	instr_rdata_i,
	instr_err_i,
	data_req_o,
	data_gnt_i,
	data_rvalid_i,
	data_we_o,
	data_be_o,
	data_addr_o,
	data_wdata_o,
	data_rdata_i,
	data_err_i,
	irq_software_i,
	irq_timer_i,
	irq_external_i,
	irq_fast_i,
	irq_nm_i,
	debug_req_i,
	rvfi_valid,
	rvfi_order,
	rvfi_insn,
	rvfi_trap,
	rvfi_halt,
	rvfi_intr,
	rvfi_mode,
	rvfi_rs1_addr,
	rvfi_rs2_addr,
	rvfi_rs1_rdata,
	rvfi_rs2_rdata,
	rvfi_rd_addr,
	rvfi_rd_wdata,
	rvfi_pc_rdata,
	rvfi_pc_wdata,
	rvfi_mem_addr,
	rvfi_mem_rmask,
	rvfi_mem_wmask,
	rvfi_mem_rdata,
	rvfi_mem_wdata,
	fetch_enable_i,
	core_sleep_o
);
	parameter PMPEnable = 1'b0;
	parameter [31:0] PMPGranularity = 0;
	parameter [31:0] PMPNumRegions = 4;
	parameter [31:0] MHPMCounterNum = 0;
	parameter [31:0] MHPMCounterWidth = 40;
	parameter RV32E = 1'b0;
	parameter RV32M = 1'b1;
	parameter MultiplierImplementation = "fast";
	parameter [31:0] DmHaltAddr = 32'h1A110800;
	parameter [31:0] DmExceptionAddr = 32'h1A110808;
	input wire clk_i;
	input wire rst_ni;
	input wire test_en_i;
	input wire [31:0] hart_id_i;
	input wire [31:0] boot_addr_i;
	output wire instr_req_o;
	input wire instr_gnt_i;
	input wire instr_rvalid_i;
	output wire [31:0] instr_addr_o;
	input wire [31:0] instr_rdata_i;
	input wire instr_err_i;
	output wire data_req_o;
	input wire data_gnt_i;
	input wire data_rvalid_i;
	output wire data_we_o;
	output wire [3:0] data_be_o;
	output wire [31:0] data_addr_o;
	output wire [31:0] data_wdata_o;
	input wire [31:0] data_rdata_i;
	input wire data_err_i;
	input wire irq_software_i;
	input wire irq_timer_i;
	input wire irq_external_i;
	input wire [14:0] irq_fast_i;
	input wire irq_nm_i;
	input wire debug_req_i;
	output reg rvfi_valid;
	output reg [63:0] rvfi_order;
	output reg [31:0] rvfi_insn;
	output reg rvfi_trap;
	output reg rvfi_halt;
	output reg rvfi_intr;
	output reg [1:0] rvfi_mode;
	output reg [4:0] rvfi_rs1_addr;
	output reg [4:0] rvfi_rs2_addr;
	output reg [31:0] rvfi_rs1_rdata;
	output reg [31:0] rvfi_rs2_rdata;
	output reg [4:0] rvfi_rd_addr;
	output reg [31:0] rvfi_rd_wdata;
	output reg [31:0] rvfi_pc_rdata;
	output reg [31:0] rvfi_pc_wdata;
	output reg [31:0] rvfi_mem_addr;
	output reg [3:0] rvfi_mem_rmask;
	output reg [3:0] rvfi_mem_wmask;
	output reg [31:0] rvfi_mem_rdata;
	output reg [31:0] rvfi_mem_wdata;
	input wire fetch_enable_i;
	output wire core_sleep_o;
	`include "ibex_pkg.v"
	localparam [31:0] PMP_NUM_CHAN = 2;
	wire instr_valid_id;
	wire instr_new_id;
	wire [31:0] instr_rdata_id;
	wire [15:0] instr_rdata_c_id;
	wire instr_is_compressed_id;
	wire instr_fetch_err;
	wire illegal_c_insn_id;
	wire [31:0] pc_if;
	wire [31:0] pc_id;
	wire instr_valid_clear;
	wire pc_set;
	wire [2:0]  pc_mux_id;
	wire [1:0] exc_pc_mux_id;
	wire [5:0] exc_cause;
	wire lsu_load_err;
	wire lsu_store_err;
	wire lsu_addr_incr_req;
	wire [31:0] lsu_addr_last;
	wire [31:0] jump_target_ex;
	wire branch_decision;
	wire ctrl_busy;
	wire if_busy;
	wire lsu_busy;
	wire core_busy_d;
	reg core_busy_q;
	wire [4:0] alu_operator_ex;
	wire [31:0] alu_operand_a_ex;
	wire [31:0] alu_operand_b_ex;
	wire [31:0] alu_adder_result_ex;
	wire [31:0] regfile_wdata_ex;
	wire mult_en_ex;
	wire div_en_ex;
	wire [1:0] multdiv_operator_ex;
	wire [1:0] multdiv_signed_mode_ex;
	wire [31:0] multdiv_operand_a_ex;
	wire [31:0] multdiv_operand_b_ex;
	wire csr_access;
	wire valid_csr_id;
	wire [1:0] csr_op;
	wire [11:0] csr_addr;
	wire [31:0] csr_rdata;
	wire [31:0] csr_wdata;
	wire illegal_csr_insn_id;
	wire data_we_ex;
	wire [1:0] data_type_ex;
	wire data_sign_ext_ex;
	wire data_req_ex;
	wire [31:0] data_wdata_ex;
	wire [31:0] regfile_wdata_lsu;
	wire id_in_ready;
	wire ex_valid;
	wire lsu_data_valid;
	wire instr_req_int;
	wire irq_pending;
	wire csr_msip;
	wire csr_mtip;
	wire csr_meip;
	wire [14:0] csr_mfip;
	wire csr_mstatus_mie;
	wire [31:0] csr_mepc;
	wire [31:0] csr_depc;
    /*
	wire [((0 >= (PMPNumRegions - 1)) ? ((((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions) * 34) + (((PMPNumRegions - 1) * 34) - 1)) : (((((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions)) * 34) + -1)):((0 >= (PMPNumRegions - 1)) ? ((PMPNumRegions - 1) * 34) : 0)] csr_pmp_addr;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_lock;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_exec;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_mode_0;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_mode_1;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_write;
	wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_read;
	wire [0:(PMP_NUM_CHAN - 1)] pmp_req_err;
    */

	wire [135:0] csr_pmp_addr;
	wire [0:3] csr_pmp_cfg_lock;
	wire [0:3] csr_pmp_cfg_exec;
	wire [0:3] csr_pmp_cfg_mode_0;
	wire [0:3] csr_pmp_cfg_mode_1;
	wire [0:3] csr_pmp_cfg_write;
	wire [0:3] csr_pmp_cfg_read;
	wire [0:1] pmp_req_err;

	wire instr_req_out;
	wire data_req_out;
	wire csr_save_if;
	wire csr_save_id;
	wire csr_restore_mret_id;
	wire csr_restore_dret_id;
	wire csr_save_cause;
	wire csr_mtvec_init;
	wire [31:0] csr_mtvec;
	wire [31:0] csr_mtval;
	wire csr_mstatus_tw;
	wire [1:0] priv_mode_id;
	wire [1:0] priv_mode_if;
	wire [1:0] priv_mode_lsu;
	wire debug_mode;
	wire [2:0] debug_cause;
	wire debug_csr_save;
	wire debug_single_step;
	wire debug_ebreakm;
	wire debug_ebreaku;
	wire instr_ret;
	wire instr_ret_compressed;
	wire perf_imiss;
	wire perf_jump;
	wire perf_branch;
	wire perf_tbranch;
	wire perf_load;
	wire perf_store;
	wire illegal_insn_id;
	wire unused_illegal_insn_id;
	wire rvfi_intr_d;
	reg rvfi_set_trap_pc_d;
	reg rvfi_set_trap_pc_q;
	reg [31:0] rvfi_insn_id;
	wire [4:0] rvfi_rs1_addr_id;
	wire [4:0] rvfi_rs2_addr_id;
	reg [31:0] rvfi_rs1_data_d;
	wire [31:0] rvfi_rs1_data_id;
	reg [31:0] rvfi_rs1_data_q;
	reg [31:0] rvfi_rs2_data_d;
	wire [31:0] rvfi_rs2_data_id;
	reg [31:0] rvfi_rs2_data_q;
	wire [4:0] rvfi_rd_addr_id;
	reg [4:0] rvfi_rd_addr_q;
	reg [4:0] rvfi_rd_addr_d;
	wire [31:0] rvfi_rd_wdata_id;
	reg [31:0] rvfi_rd_wdata_d;
	reg [31:0] rvfi_rd_wdata_q;
	wire rvfi_rd_we_id;
	reg rvfi_insn_new_d;
	reg rvfi_insn_new_q;
	reg [3:0] rvfi_mem_mask_int;
	reg [31:0] rvfi_mem_rdata_d;
	reg [31:0] rvfi_mem_rdata_q;
	reg [31:0] rvfi_mem_wdata_d;
	reg [31:0] rvfi_mem_wdata_q;
	reg [31:0] rvfi_mem_addr_d;
	reg [31:0] rvfi_mem_addr_q;
	wire clk;
	wire clock_en;
	assign core_busy_d = ((ctrl_busy | if_busy) | lsu_busy);
	always @(posedge clk_i or negedge rst_ni)
		if (!rst_ni)
			core_busy_q <= 1'b0;
		else
			core_busy_q <= core_busy_d;
	assign clock_en = (((core_busy_q | debug_req_i) | irq_pending) | irq_nm_i);
	assign core_sleep_o = ~clock_en;
	prim_clock_gating core_clock_gate_i(
		.clk_i(clk_i),
		.en_i(clock_en),
		.test_en_i(test_en_i),
		.clk_o(clk)
	);
	ibex_if_stage #(
		.DmHaltAddr(DmHaltAddr),
		.DmExceptionAddr(DmExceptionAddr)
	) if_stage_i(
		.clk_i(clk),
		.rst_ni(rst_ni),
		.boot_addr_i(boot_addr_i),
		.req_i(instr_req_int),
		.instr_req_o(instr_req_out),
		.instr_addr_o(instr_addr_o),
		.instr_gnt_i(instr_gnt_i),
		.instr_rvalid_i(instr_rvalid_i),
		.instr_rdata_i(instr_rdata_i),
		.instr_err_i(instr_err_i),
		.instr_pmp_err_i(pmp_req_err[PMP_I]),
		.instr_valid_id_o(instr_valid_id),
		.instr_new_id_o(instr_new_id),
		.instr_rdata_id_o(instr_rdata_id),
		.instr_rdata_c_id_o(instr_rdata_c_id),
		.instr_is_compressed_id_o(instr_is_compressed_id),
		.instr_fetch_err_o(instr_fetch_err),
		.illegal_c_insn_id_o(illegal_c_insn_id),
		.pc_if_o(pc_if),
		.pc_id_o(pc_id),
		.instr_valid_clear_i(instr_valid_clear),
		.pc_set_i(pc_set),
		.pc_mux_i(pc_mux_id),
		.exc_pc_mux_i(exc_pc_mux_id),
		.exc_cause(exc_cause),
		.jump_target_ex_i(jump_target_ex),
		.csr_mepc_i(csr_mepc),
		.csr_depc_i(csr_depc),
		.csr_mtvec_i(csr_mtvec),
		.csr_mtvec_init_o(csr_mtvec_init),
		.id_in_ready_i(id_in_ready),
		.if_busy_o(if_busy),
		.perf_imiss_o(perf_imiss)
	);
	assign instr_req_o = (instr_req_out & ~pmp_req_err[PMP_I]);
	ibex_id_stage #(
		.RV32E(RV32E),
		.RV32M(RV32M)
	) id_stage_i(
		.clk_i(clk),
		.rst_ni(rst_ni),
		.test_en_i(test_en_i),
		.fetch_enable_i(fetch_enable_i),
		.ctrl_busy_o(ctrl_busy),
		.illegal_insn_o(illegal_insn_id),
		.instr_valid_i(instr_valid_id),
		.instr_new_i(instr_new_id),
		.instr_rdata_i(instr_rdata_id),
		.instr_rdata_c_i(instr_rdata_c_id),
		.instr_is_compressed_i(instr_is_compressed_id),
		.branch_decision_i(branch_decision),
		.id_in_ready_o(id_in_ready),
		.instr_valid_clear_o(instr_valid_clear),
		.instr_req_o(instr_req_int),
		.pc_set_o(pc_set),
		.pc_mux_o(pc_mux_id),
		.exc_pc_mux_o(exc_pc_mux_id),
		.exc_cause_o(exc_cause),
		.instr_fetch_err_i(instr_fetch_err),
		.illegal_c_insn_i(illegal_c_insn_id),
		.pc_id_i(pc_id),
		.ex_valid_i(ex_valid),
		.lsu_valid_i(lsu_data_valid),
		.alu_operator_ex_o(alu_operator_ex),
		.alu_operand_a_ex_o(alu_operand_a_ex),
		.alu_operand_b_ex_o(alu_operand_b_ex),
		.mult_en_ex_o(mult_en_ex),
		.div_en_ex_o(div_en_ex),
		.multdiv_operator_ex_o(multdiv_operator_ex),
		.multdiv_signed_mode_ex_o(multdiv_signed_mode_ex),
		.multdiv_operand_a_ex_o(multdiv_operand_a_ex),
		.multdiv_operand_b_ex_o(multdiv_operand_b_ex),
		.csr_access_o(csr_access),
		.csr_op_o(csr_op),
		.csr_save_if_o(csr_save_if),
		.csr_save_id_o(csr_save_id),
		.csr_restore_mret_id_o(csr_restore_mret_id),
		.csr_restore_dret_id_o(csr_restore_dret_id),
		.csr_save_cause_o(csr_save_cause),
		.csr_mtval_o(csr_mtval),
		.priv_mode_i(priv_mode_id),
		.csr_mstatus_tw_i(csr_mstatus_tw),
		.illegal_csr_insn_i(illegal_csr_insn_id),
		.data_req_ex_o(data_req_ex),
		.data_we_ex_o(data_we_ex),
		.data_type_ex_o(data_type_ex),
		.data_sign_ext_ex_o(data_sign_ext_ex),
		.data_wdata_ex_o(data_wdata_ex),
		.lsu_addr_incr_req_i(lsu_addr_incr_req),
		.lsu_addr_last_i(lsu_addr_last),
		.lsu_load_err_i(lsu_load_err),
		.lsu_store_err_i(lsu_store_err),
		.csr_mstatus_mie_i(csr_mstatus_mie),
		.csr_msip_i(csr_msip),
		.csr_mtip_i(csr_mtip),
		.csr_meip_i(csr_meip),
		.csr_mfip_i(csr_mfip),
		.irq_pending_i(irq_pending),
		.irq_nm_i(irq_nm_i),
		.debug_mode_o(debug_mode),
		.debug_cause_o(debug_cause),
		.debug_csr_save_o(debug_csr_save),
		.debug_req_i(debug_req_i),
		.debug_single_step_i(debug_single_step),
		.debug_ebreakm_i(debug_ebreakm),
		.debug_ebreaku_i(debug_ebreaku),
		.regfile_wdata_lsu_i(regfile_wdata_lsu),
		.regfile_wdata_ex_i(regfile_wdata_ex),
		.csr_rdata_i(csr_rdata),
		.rfvi_reg_raddr_ra_o(rvfi_rs1_addr_id),
		.rfvi_reg_rdata_ra_o(rvfi_rs1_data_id),
		.rfvi_reg_raddr_rb_o(rvfi_rs2_addr_id),
		.rfvi_reg_rdata_rb_o(rvfi_rs2_data_id),
		.rfvi_reg_waddr_rd_o(rvfi_rd_addr_id),
		.rfvi_reg_wdata_rd_o(rvfi_rd_wdata_id),
		.rfvi_reg_we_o(rvfi_rd_we_id),
		.perf_jump_o(perf_jump),
		.perf_branch_o(perf_branch),
		.perf_tbranch_o(perf_tbranch),
		.instr_ret_o(instr_ret),
		.instr_ret_compressed_o(instr_ret_compressed)
	);
	assign unused_illegal_insn_id = illegal_insn_id;
	ibex_ex_block #(
		.RV32M(RV32M),
		.MultiplierImplementation(MultiplierImplementation)
	) ex_block_i(
		.clk_i(clk),
		.rst_ni(rst_ni),
		.alu_operator_i(alu_operator_ex),
		.alu_operand_a_i(alu_operand_a_ex),
		.alu_operand_b_i(alu_operand_b_ex),
		.multdiv_operator_i(multdiv_operator_ex),
		.mult_en_i(mult_en_ex),
		.div_en_i(div_en_ex),
		.multdiv_signed_mode_i(multdiv_signed_mode_ex),
		.multdiv_operand_a_i(multdiv_operand_a_ex),
		.multdiv_operand_b_i(multdiv_operand_b_ex),
		.alu_adder_result_ex_o(alu_adder_result_ex),
		.regfile_wdata_ex_o(regfile_wdata_ex),
		.jump_target_o(jump_target_ex),
		.branch_decision_o(branch_decision),
		.ex_valid_o(ex_valid)
	);
	assign data_req_o = (data_req_out & ~pmp_req_err[PMP_D]);
	ibex_load_store_unit load_store_unit_i(
		.clk_i(clk),
		.rst_ni(rst_ni),
		.data_req_o(data_req_out),
		.data_gnt_i(data_gnt_i),
		.data_rvalid_i(data_rvalid_i),
		.data_err_i(data_err_i),
		.data_pmp_err_i(pmp_req_err[PMP_D]),
		.data_addr_o(data_addr_o),
		.data_we_o(data_we_o),
		.data_be_o(data_be_o),
		.data_wdata_o(data_wdata_o),
		.data_rdata_i(data_rdata_i),
		.data_we_ex_i(data_we_ex),
		.data_type_ex_i(data_type_ex),
		.data_wdata_ex_i(data_wdata_ex),
		.data_sign_ext_ex_i(data_sign_ext_ex),
		.data_rdata_ex_o(regfile_wdata_lsu),
		.data_req_ex_i(data_req_ex),
		.adder_result_ex_i(alu_adder_result_ex),
		.addr_incr_req_o(lsu_addr_incr_req),
		.addr_last_o(lsu_addr_last),
		.data_valid_o(lsu_data_valid),
		.load_err_o(lsu_load_err),
		.store_err_o(lsu_store_err),
		.busy_o(lsu_busy)
	);
	assign csr_wdata = alu_operand_a_ex;
	assign csr_addr = sv2v_cast_290A1((csr_access ? alu_operand_b_ex[11:0] : 12'b0));
	assign perf_load = ((data_req_o & data_gnt_i) & ~data_we_o);
	assign perf_store = ((data_req_o & data_gnt_i) & data_we_o);
	assign valid_csr_id = (instr_new_id & ~instr_fetch_err);
	ibex_cs_registers #(
		.MHPMCounterNum(MHPMCounterNum),
		.MHPMCounterWidth(MHPMCounterWidth),
		.PMPEnable(PMPEnable),
		.PMPGranularity(PMPGranularity),
		.PMPNumRegions(PMPNumRegions),
		.RV32E(RV32E),
		.RV32M(RV32M)
	) cs_registers_i(
		.clk_i(clk),
		.rst_ni(rst_ni),
		.hart_id_i(hart_id_i),
		.priv_mode_id_o(priv_mode_id),
		.priv_mode_if_o(priv_mode_if),
		.priv_mode_lsu_o(priv_mode_lsu),
		.csr_mtvec_o(csr_mtvec),
		.csr_mtvec_init_i(csr_mtvec_init),
		.boot_addr_i(boot_addr_i),
		.csr_access_i(csr_access),
		.csr_addr_i(csr_addr),
		.csr_wdata_i(csr_wdata),
		.csr_op_i(csr_op),
		.csr_rdata_o(csr_rdata),
		.irq_software_i(irq_software_i),
		.irq_timer_i(irq_timer_i),
		.irq_external_i(irq_external_i),
		.irq_fast_i(irq_fast_i),
		.irq_pending_o(irq_pending),
		.csr_msip_o(csr_msip),
		.csr_mtip_o(csr_mtip),
		.csr_meip_o(csr_meip),
		.csr_mfip_o(csr_mfip),
		.csr_mstatus_mie_o(csr_mstatus_mie),
		.csr_mstatus_tw_o(csr_mstatus_tw),
		.csr_mepc_o(csr_mepc),
		.csr_pmp_cfg_o_lock(csr_pmp_cfg_lock),
		.csr_pmp_cfg_o_exec(csr_pmp_cfg_exec),
		.csr_pmp_cfg_o_mode_0(csr_pmp_cfg_mode_0),
		.csr_pmp_cfg_o_mode_1(csr_pmp_cfg_mode_1),
		.csr_pmp_cfg_o_read(csr_pmp_cfg_read),
		.csr_pmp_cfg_o_write(csr_pmp_cfg_write),
		.csr_pmp_addr_o(csr_pmp_addr),
		.csr_depc_o(csr_depc),
		.debug_mode_i(debug_mode),
		.debug_cause_i(debug_cause),
		.debug_csr_save_i(debug_csr_save),
		.debug_single_step_o(debug_single_step),
		.debug_ebreakm_o(debug_ebreakm),
		.debug_ebreaku_o(debug_ebreaku),
		.pc_if_i(pc_if),
		.pc_id_i(pc_id),
		.csr_save_if_i(csr_save_if),
		.csr_save_id_i(csr_save_id),
		.csr_restore_mret_i(csr_restore_mret_id),
		.csr_restore_dret_i(csr_restore_dret_id),
		.csr_save_cause_i(csr_save_cause),
		.csr_mcause_i(exc_cause),
		.csr_mtval_i(csr_mtval),
		.illegal_csr_insn_o(illegal_csr_insn_id),
		.instr_new_id_i(valid_csr_id),
		.instr_ret_i(instr_ret),
		.instr_ret_compressed_i(instr_ret_compressed),
		.imiss_i(perf_imiss),
		.pc_set_i(pc_set),
		.jump_i(perf_jump),
		.branch_i(perf_branch),
		.branch_taken_i(perf_tbranch),
		.mem_load_i(perf_load),
		.mem_store_i(perf_store),
		.lsu_busy_i(lsu_busy)
	);
	generate
    /*
		if (PMPEnable) begin : g_pmp
			wire [((PMP_NUM_CHAN * 34) + -1):0] pmp_req_addr;
			wire [0:(PMP_NUM_CHAN - 1)] pmp_req_type [1:0];
			wire [0:(PMP_NUM_CHAN - 1)] pmp_priv_lvl [1:0];
			assign pmp_req_addr[(((PMP_NUM_CHAN - 1) - PMP_I) * 34)+:34] = {2'b00, instr_addr_o[31:0]};
			assign pmp_req_type[PMP_I] = PMP_ACC_EXEC;
			assign pmp_priv_lvl[PMP_I] = priv_mode_if;
			assign pmp_req_addr[(((PMP_NUM_CHAN - 1) - PMP_D) * 34)+:34] = {2'b00, data_addr_o[31:0]};
			assign pmp_req_type[PMP_D] = (data_we_o ? PMP_ACC_WRITE : PMP_ACC_READ);
			assign pmp_priv_lvl[PMP_D] = priv_mode_lsu;
			ibex_pmp #(
				.PMPGranularity(PMPGranularity),
				.PMPNumChan(PMP_NUM_CHAN),
				.PMPNumRegions(PMPNumRegions)
			) pmp_i(
				.clk_i(clk),
				.rst_ni(rst_ni),
				.csr_pmp_cfg_i_lock(csr_pmp_cfg_lock),
				.csr_pmp_cfg_i_mode(csr_pmp_cfg_mode),
				.csr_pmp_cfg_i_exec(csr_pmp_cfg_exec),
				.csr_pmp_cfg_i_write(csr_pmp_cfg_write),
				.csr_pmp_cfg_i_read(csr_pmp_cfg_read),
				.csr_pmp_addr_i(csr_pmp_addr),
				.priv_mode_i(pmp_priv_lvl),
				.pmp_req_addr_i(pmp_req_addr),
				.pmp_req_type_i(pmp_req_type),
				.pmp_req_err_o(pmp_req_err)
			);
		end
		else begin : g_no_pmp
    */
			wire [1:0] unused_priv_lvl_if;
			wire [1:0] unused_priv_lvl_ls;
            /*
			wire [((0 >= (PMPNumRegions - 1)) ? ((((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions) * 34) + (((PMPNumRegions - 1) * 34) - 1)) : (((((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions)) * 34) + -1)):((0 >= (PMPNumRegions - 1)) ? ((PMPNumRegions - 1) * 34) : 0)] unused_csr_pmp_addr;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_lock;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_exec;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_mode_0;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_mode_1;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_write;
			wire [0:(PMPNumRegions - 1)] unused_csr_pmp_cfg_read;
            */

			wire [135:0] unused_csr_pmp_addr;
			wire [0:3] unused_csr_pmp_cfg_lock;
			wire [0:3] unused_csr_pmp_cfg_exec;
			wire [0:3] unused_csr_pmp_cfg_mode_0;
			wire [0:3] unused_csr_pmp_cfg_mode_1;
			wire [0:3] unused_csr_pmp_cfg_write;
			wire [0:3] unused_csr_pmp_cfg_read;

			assign unused_priv_lvl_if = priv_mode_if;
			assign unused_priv_lvl_ls = priv_mode_lsu;
			assign unused_csr_pmp_addr = csr_pmp_addr;
			assign unused_csr_pmp_cfg_lock = csr_pmp_cfg_lock;
			assign unused_csr_pmp_cfg_exec = csr_pmp_cfg_exec;
			assign unused_csr_pmp_cfg_mode_0 = csr_pmp_cfg_mode_0;
			assign unused_csr_pmp_cfg_mode_1 = csr_pmp_cfg_mode_1;
			assign unused_csr_pmp_cfg_write = csr_pmp_cfg_write;
			assign unused_csr_pmp_cfg_read = csr_pmp_cfg_read;
			assign pmp_req_err[PMP_I] = 1'b0;
			assign pmp_req_err[PMP_D] = 1'b0;
	//	end
	endgenerate
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni) begin
			rvfi_halt <= 1'sb0;
			rvfi_trap <= 1'sb0;
			rvfi_intr <= 1'sb0;
			rvfi_order <= 1'sb0;
			rvfi_insn <= 1'sb0;
			rvfi_mode <= PRIV_LVL_M;
			rvfi_rs1_addr <= 1'sb0;
			rvfi_rs2_addr <= 1'sb0;
			rvfi_pc_rdata <= 1'sb0;
			rvfi_pc_wdata <= 1'sb0;
			rvfi_mem_rmask <= 1'sb0;
			rvfi_mem_wmask <= 1'sb0;
			rvfi_valid <= 1'sb0;
			rvfi_rs1_rdata <= 1'sb0;
			rvfi_rs2_rdata <= 1'sb0;
			rvfi_rd_wdata <= 1'sb0;
			rvfi_rd_addr <= 1'sb0;
			rvfi_mem_rdata <= 1'sb0;
			rvfi_mem_wdata <= 1'sb0;
			rvfi_mem_addr <= 1'sb0;
		end
		else begin
			rvfi_halt <= 1'sb0;
			rvfi_trap <= illegal_insn_id;
			rvfi_intr <= rvfi_intr_d;
			rvfi_order <= (rvfi_order + sv2v_cast_64(rvfi_valid));
			rvfi_insn <= rvfi_insn_id;
			rvfi_mode <= priv_mode_id;
			rvfi_rs1_addr <= rvfi_rs1_addr_id;
			rvfi_rs2_addr <= rvfi_rs2_addr_id;
			rvfi_pc_rdata <= pc_id;
			rvfi_pc_wdata <= pc_if;
			rvfi_mem_rmask <= rvfi_mem_mask_int;
			rvfi_mem_wmask <= (data_we_o ? rvfi_mem_mask_int : 4'b0000);
			rvfi_valid <= instr_ret;
			rvfi_rs1_rdata <= rvfi_rs1_data_d;
			rvfi_rs2_rdata <= rvfi_rs2_data_d;
			rvfi_rd_wdata <= rvfi_rd_wdata_d;
			rvfi_rd_addr <= rvfi_rd_addr_d;
			rvfi_mem_rdata <= rvfi_mem_rdata_d;
			rvfi_mem_wdata <= rvfi_mem_wdata_d;
			rvfi_mem_addr <= rvfi_mem_addr_d;
		end
	always @(*)
		if ((rvfi_insn_new_d && lsu_data_valid)) begin
			rvfi_mem_addr_d = alu_adder_result_ex;
			rvfi_mem_rdata_d = regfile_wdata_lsu;
			rvfi_mem_wdata_d = data_wdata_ex;
		end
		else begin
			rvfi_mem_addr_d = rvfi_mem_addr_q;
			rvfi_mem_rdata_d = rvfi_mem_rdata_q;
			rvfi_mem_wdata_d = rvfi_mem_wdata_q;
		end
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni) begin
			rvfi_mem_addr_q <= 1'sb0;
			rvfi_mem_rdata_q <= 1'sb0;
			rvfi_mem_wdata_q <= 1'sb0;
		end
		else begin
			rvfi_mem_addr_q <= rvfi_mem_addr_d;
			rvfi_mem_rdata_q <= rvfi_mem_rdata_d;
			rvfi_mem_wdata_q <= rvfi_mem_wdata_d;
		end
	always @(*)
		case (data_type_ex)
			2'b00: rvfi_mem_mask_int = 4'b1111;
			2'b01: rvfi_mem_mask_int = 4'b0011;
			2'b10: rvfi_mem_mask_int = 4'b0001;
			default: rvfi_mem_mask_int = 4'b0000;
		endcase
	always @(*)
		if (instr_is_compressed_id)
			rvfi_insn_id = {16'b0, instr_rdata_c_id};
		else
			rvfi_insn_id = instr_rdata_id;
	always @(*)
		if (instr_new_id) begin
			rvfi_rs1_data_d = rvfi_rs1_data_id;
			rvfi_rs2_data_d = rvfi_rs2_data_id;
		end
		else begin
			rvfi_rs1_data_d = rvfi_rs1_data_q;
			rvfi_rs2_data_d = rvfi_rs2_data_q;
		end
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni) begin
			rvfi_rs1_data_q <= 1'sb0;
			rvfi_rs2_data_q <= 1'sb0;
		end
		else begin
			rvfi_rs1_data_q <= rvfi_rs1_data_d;
			rvfi_rs2_data_q <= rvfi_rs2_data_d;
		end
	always @(*)
		if (rvfi_insn_new_d) begin
			if (!rvfi_rd_we_id) begin
				rvfi_rd_addr_d = 1'sb0;
				rvfi_rd_wdata_d = 1'sb0;
			end
			else begin
				rvfi_rd_addr_d = rvfi_rd_addr_id;
				if ((rvfi_rd_addr_id == 5'h0))
					rvfi_rd_wdata_d = 1'sb0;
				else
					rvfi_rd_wdata_d = rvfi_rd_wdata_id;
			end
		end
		else begin
			rvfi_rd_addr_d = rvfi_rd_addr_q;
			rvfi_rd_wdata_d = rvfi_rd_wdata_q;
		end
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni) begin
			rvfi_rd_addr_q <= 1'sb0;
			rvfi_rd_wdata_q <= 1'sb0;
		end
		else begin
			rvfi_rd_addr_q <= rvfi_rd_addr_d;
			rvfi_rd_wdata_q <= rvfi_rd_wdata_d;
		end
	always @(*)
		if (instr_new_id)
			rvfi_insn_new_d = 1'b1;
		else
			rvfi_insn_new_d = rvfi_insn_new_q;
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni)
			rvfi_insn_new_q <= 1'b0;
		else if (instr_ret)
			rvfi_insn_new_q <= 1'b0;
		else
			rvfi_insn_new_q <= rvfi_insn_new_d;
	assign rvfi_intr_d = (rvfi_set_trap_pc_q & rvfi_insn_new_d);
	always @(*) begin
		rvfi_set_trap_pc_d = rvfi_set_trap_pc_q;
		if (((pc_set && (pc_mux_id == PC_EXC)) && ((exc_pc_mux_id == EXC_PC_EXC) || (exc_pc_mux_id == EXC_PC_IRQ))))
			rvfi_set_trap_pc_d = 1'b1;
		else if ((rvfi_set_trap_pc_q && instr_ret))
			rvfi_set_trap_pc_d = 1'b0;
	end
	always @(posedge clk or negedge rst_ni)
		if (!rst_ni)
			rvfi_set_trap_pc_q <= 1'b0;
		else
			rvfi_set_trap_pc_q <= rvfi_set_trap_pc_d;
	function [63:0] sv2v_cast_64;
		input [63:0] inp;
		sv2v_cast_64 = inp;
	endfunction
	function [(12 - 1):0] sv2v_cast_290A1;
		input [(12 - 1):0] inp;
		sv2v_cast_290A1 = inp;
	endfunction
    /*	
	initial begin
		$dumpfile("test.vcd");
		$dumpvars();
	end
    */
endmodule
