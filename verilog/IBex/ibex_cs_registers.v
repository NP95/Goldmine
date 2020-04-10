module ibex_cs_registers (
	clk_i,
	rst_ni,
	hart_id_i,
	priv_mode_id_o,
	priv_mode_if_o,
	priv_mode_lsu_o,
	csr_mstatus_tw_o,
	csr_mtvec_o,
	csr_mtvec_init_i,
	boot_addr_i,
	csr_access_i,
	csr_addr_i,
	csr_wdata_i,
	csr_op_i,
	csr_rdata_o,
	irq_software_i,
	irq_timer_i,
	irq_external_i,
	irq_fast_i,
	irq_pending_o,
	csr_msip_o,
	csr_mtip_o,
	csr_meip_o,
	csr_mfip_o,
	csr_mstatus_mie_o,
	csr_mepc_o,
	csr_pmp_cfg_o_lock,
	csr_pmp_cfg_o_exec,
	csr_pmp_cfg_o_write,
	csr_pmp_cfg_o_read,
	csr_pmp_cfg_o_mode_0,
	csr_pmp_cfg_o_mode_1,
	csr_pmp_addr_o,
	debug_mode_i,
	debug_cause_i,
	debug_csr_save_i,
	csr_depc_o,
	debug_single_step_o,
	debug_ebreakm_o,
	debug_ebreaku_o,
	pc_if_i,
	pc_id_i,
	csr_save_if_i,
	csr_save_id_i,
	csr_restore_mret_i,
	csr_restore_dret_i,
	csr_save_cause_i,
	csr_mcause_i,
	csr_mtval_i,
	illegal_csr_insn_o,
	instr_new_id_i,
	instr_ret_i,
	instr_ret_compressed_i,
	imiss_i,
	pc_set_i,
	jump_i,
	branch_i,
	branch_taken_i,
	mem_load_i,
	mem_store_i,
	lsu_busy_i
);

`include "ibex_pkg.v"

	parameter [31:0] MHPMCounterNum = 8;
	parameter [31:0] MHPMCounterWidth = 40;
	parameter PMPEnable = 0;
	parameter [31:0] PMPGranularity = 0;
	parameter [31:0] PMPNumRegions = 4;
	parameter RV32E = 0;
	parameter RV32M = 0;
	input wire clk_i;
	input wire rst_ni;
	input wire [31:0] hart_id_i;
	output [1:0] priv_mode_id_o;
	output [1:0] priv_mode_if_o;
	output [1:0] priv_mode_lsu_o;
	output wire csr_mstatus_tw_o;
	output wire [31:0] csr_mtvec_o;
	input wire csr_mtvec_init_i;
	input wire [31:0] boot_addr_i;
	input wire csr_access_i;
	input wire [11:0] csr_addr_i;
	input wire [31:0] csr_wdata_i;
	input wire [1:0] csr_op_i;
	output wire [31:0] csr_rdata_o;
	input wire irq_software_i;
	input wire irq_timer_i;
	input wire irq_external_i;
	input wire [14:0] irq_fast_i;
	output wire irq_pending_o;
	output wire csr_msip_o;
	output wire csr_mtip_o;
	output wire csr_meip_o;
	output wire [14:0] csr_mfip_o;
	output wire csr_mstatus_mie_o;
	output wire [31:0] csr_mepc_o;
	/*
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_lock;
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_exec;
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_write;
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_read;
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_mode_0;
	output wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_o_mode_1;
	*/
	output wire [0:3] csr_pmp_cfg_o_lock;
	output wire [0:3] csr_pmp_cfg_o_exec;
	output wire [0:3] csr_pmp_cfg_o_write;
	output wire [0:3] csr_pmp_cfg_o_read;
	output wire [0:3] csr_pmp_cfg_o_mode_0;
	output wire [0:3] csr_pmp_cfg_o_mode_1;
	/*
	output wire [((0 >= (PMPNumRegions - 1)) ? ((((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions) * 34) + (((PMPNumRegions - 1) * 34) - 1)) : (((((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions)) * 34) + -1)):((0 >= (PMPNumRegions - 1)) ? ((PMPNumRegions - 1) * 34) : 0)] csr_pmp_addr_o;
	*/
	output wire [135:0] csr_pmp_addr_o;
	input wire debug_mode_i;
	input wire [2:0] debug_cause_i;
	input wire debug_csr_save_i;
	output wire [31:0] csr_depc_o;
	output wire debug_single_step_o;
	output wire debug_ebreakm_o;
	output wire debug_ebreaku_o;
	input wire [31:0] pc_if_i;
	input wire [31:0] pc_id_i;
	input wire csr_save_if_i;
	input wire csr_save_id_i;
	input wire csr_restore_mret_i;
	input wire csr_restore_dret_i;
	input wire csr_save_cause_i;
	input wire [5:0] csr_mcause_i;
	input wire [31:0] csr_mtval_i;
	output wire illegal_csr_insn_o;
	input wire instr_new_id_i;
	input wire instr_ret_i;
	input wire instr_ret_compressed_i;
	input wire imiss_i;
	input wire pc_set_i;
	input wire jump_i;
	input wire branch_i;
	input wire branch_taken_i;
	input wire mem_load_i;
	input wire mem_store_i;
	input wire lsu_busy_i;
	//import ibex_pkg::*;
	localparam [1:0] MXL = 2'd1;
	localparam [31:0] MISA_VALUE = ((((((((((((0 << 0) | (1 << 2)) | (0 << 3)) | (sv2v_cast_32(RV32E) << 4)) | (0 << 5)) | (1 << 8)) | (sv2v_cast_32(RV32M) << 12)) | (0 << 13)) | (0 << 18)) | (1 << 20)) | (0 << 23)) | (sv2v_cast_32(MXL) << 30));
	reg [31:0] exception_pc;
	reg [1:0] priv_lvl_q;
        reg [1:0] priv_lvl_d;

	reg mstatus_q_Status_t_mie;
	reg mstatus_q_Status_t_mpie;
	reg [1:0] mstatus_q_Status_t_mpp;
	reg mstatus_q_Status_t_mprv;
	reg mstatus_q_Status_t_tw;

	reg mstatus_d_Status_t_mie;
	reg mstatus_d_Status_t_mpie;
	reg [1:0] mstatus_d_Status_t_mpp;
	reg mstatus_d_Status_t_mprv;
	reg mstatus_d_Status_t_tw;
	
	reg mie_q_Interrupts_t_irq_software;
	reg mie_q_Interrupts_t_irq_timer;
	reg mie_q_Interrupts_t_irq_external;
	reg [14:0] mie_q_Interrupts_t_irq_fast;
	reg mie_d_Interrupts_t_irq_software;
	reg mie_d_Interrupts_t_irq_timer;
	reg mie_d_Interrupts_t_irq_external;
	reg [14:0] mie_d_Interrupts_t_irq_fast;
	wire mip_Interrupts_t_irq_software;
	wire mip_Interrupts_t_irq_timer;
	wire mip_Interrupts_t_irq_external;
	wire [14:0] mip_Interrupts_t_irq_fast;
	reg [31:0] mscratch_q;
	reg [31:0] mscratch_d;
	reg [31:0] mepc_q;
	reg [31:0] mepc_d;
	reg [5:0] mcause_q;
	reg [5:0] mcause_d;
	reg [31:0] mtval_q;
	reg [31:0] mtval_d;
	reg [31:0] mtvec_q;
	reg [31:0] mtvec_d;
	reg [3:0] dcsr_q_Dcsr_t_xdebugver;
	reg [11:0] dcsr_q_Dcsr_t_zero2;
	reg dcsr_q_Dcsr_t_ebreakm;
	reg dcsr_q_Dcsr_t_zero1;
	reg dcsr_q_Dcsr_t_ebreaks;
	reg dcsr_q_Dcsr_t_ebreaku;
	reg dcsr_q_Dcsr_t_stepie;
	reg dcsr_q_Dcsr_t_stopcount;
	reg dcsr_q_Dcsr_t_stoptime;
	reg dcsr_q_Dcsr_t_cause;
	reg dcsr_q_Dcsr_t_zero0;
	reg dcsr_q_Dcsr_t_mprven;
	reg dcsr_q_Dcsr_t_nmip;
	reg dcsr_q_Dcsr_t_step;
	reg [1:0] dcsr_q_Dcsr_t_prv;
	reg [3:0] dcsr_d_Dcsr_t_xdebugver;
	reg [11:0] dcsr_d_Dcsr_t_zero2;
	reg dcsr_d_Dcsr_t_ebreakm;
	reg dcsr_d_Dcsr_t_zero1;
	reg dcsr_d_Dcsr_t_ebreaks;
	reg dcsr_d_Dcsr_t_ebreaku;
	reg dcsr_d_Dcsr_t_stepie;
	reg dcsr_d_Dcsr_t_stopcount;
	reg dcsr_d_Dcsr_t_stoptime;
	reg dcsr_d_Dcsr_t_cause;
	reg dcsr_d_Dcsr_t_zero0;
	reg dcsr_d_Dcsr_t_mprven;
	reg dcsr_d_Dcsr_t_nmip;
	reg dcsr_d_Dcsr_t_step;
	reg [1:0] dcsr_d_Dcsr_t_prv;
	reg [31:0] depc_q;
	reg [31:0] depc_d;
	reg [31:0] dscratch0_q;
	reg [31:0] dscratch0_d;
	reg [31:0] dscratch1_q;
	reg [31:0] dscratch1_d;
	reg mstack_q_StatusStk_t_mpie;
	reg [1:0] mstack_q_StatusStk_t_mpp;
	reg mstack_d_StatusStk_t_mpie;
	reg [1:0] mstack_d_StatusStk_t_mpp;
	reg [31:0] mstack_epc_q;
	reg [31:0] mstack_epc_d;
	reg [5:0] mstack_cause_q;
	reg [5:0] mstack_cause_d;
	wire [31:0] pmp_addr_rdata [0:(PMP_MAX_REGIONS - 1)];
	wire [(PMP_CFG_W - 1):0] pmp_cfg_rdata [0:(PMP_MAX_REGIONS - 1)];
	reg [31:0] mcountinhibit_d;
	reg [31:0] mcountinhibit_q;
	wire [31:0] mcountinhibit;
	wire [31:0] mcountinhibit_force;
	reg mcountinhibit_we;
	reg [63:0] mhpmcounter_mask [0:(32 - 1)];
	reg [2047:0] mhpmcounter_d;
	reg [2047:0] mhpmcounter_q;
	reg [31:0] mhpmcounter_we;
	reg [31:0] mhpmcounterh_we;
	reg [31:0] mhpmcounter_incr;
	reg [31:0] mhpmevent [0:(32 - 1)];
	wire [4:0] mhpmcounter_idx;
	reg [31:0] csr_wdata_int;
	reg [31:0] csr_rdata_int;
	wire csr_we_int;
	reg csr_wreq;
	reg illegal_csr;
	wire illegal_csr_priv;
	wire illegal_csr_write;
	wire [7:0] unused_boot_addr;
	wire [2:0] unused_csr_addr;
	assign unused_boot_addr = boot_addr_i[7:0];
	wire [11:0] csr_addr;
	assign csr_addr = csr_addr_i;
	assign unused_csr_addr = csr_addr[7:5];
	assign mhpmcounter_idx = csr_addr[4:0];
	assign illegal_csr_priv = (csr_addr[9:8] > priv_lvl_q);
	assign illegal_csr_write = ((csr_addr[11:10] == 2'b11) && csr_wreq);
	assign illegal_csr_insn_o = (csr_access_i & ((illegal_csr | illegal_csr_write) | illegal_csr_priv));
	assign mip_Interrupts_t_irq_software = (irq_software_i & mie_q_Interrupts_t_irq_software);
	assign mip_Interrupts_t_irq_timer = (irq_timer_i & mie_q_Interrupts_t_irq_timer);
	assign mip_Interrupts_t_irq_external = (irq_external_i & mie_q_Interrupts_t_irq_external);
	assign mip_Interrupts_t_irq_fast = (irq_fast_i & mie_q_Interrupts_t_irq_fast);

	always @(*) begin
		csr_rdata_int = 1'b0;
		illegal_csr = 1'b0;
		case (csr_addr_i)
			CSR_MHARTID: csr_rdata_int = hart_id_i;
			CSR_MSTATUS: begin
				csr_rdata_int = 1'b0;
				csr_rdata_int[CSR_MSTATUS_MIE_BIT] = mstatus_q_Status_t_mie;
				csr_rdata_int[CSR_MSTATUS_MPIE_BIT] = mstatus_q_Status_t_mpie;
				csr_rdata_int[CSR_MSTATUS_MPP_BIT_HIGH:CSR_MSTATUS_MPP_BIT_LOW] = mstatus_q_Status_t_mpp;
				csr_rdata_int[CSR_MSTATUS_MPRV_BIT] = mstatus_q_Status_t_mprv;
				csr_rdata_int[CSR_MSTATUS_TW_BIT] = mstatus_q_Status_t_tw;
			end
			CSR_MISA: csr_rdata_int = MISA_VALUE;
			CSR_MIE: begin
				csr_rdata_int = 1'b0;
				csr_rdata_int[CSR_MSIX_BIT] = mie_q_Interrupts_t_irq_software;
				csr_rdata_int[CSR_MTIX_BIT] = mie_q_Interrupts_t_irq_timer;
				csr_rdata_int[CSR_MEIX_BIT] = mie_q_Interrupts_t_irq_external;
				csr_rdata_int[CSR_MFIX_BIT_HIGH:CSR_MFIX_BIT_LOW] = mie_q_Interrupts_t_irq_fast;
			end
			CSR_MSCRATCH: csr_rdata_int = mscratch_q;
			CSR_MTVEC: csr_rdata_int = mtvec_q;
			CSR_MEPC: csr_rdata_int = mepc_q;
			CSR_MCAUSE: csr_rdata_int = {mcause_q[5], 26'b0, mcause_q[4:0]};
			CSR_MTVAL: csr_rdata_int = mtval_q;
			CSR_MIP: begin
				csr_rdata_int = 1'b0;
				csr_rdata_int[CSR_MSIX_BIT] = mip_Interrupts_t_irq_software;
				csr_rdata_int[CSR_MTIX_BIT] = mip_Interrupts_t_irq_timer;
				csr_rdata_int[CSR_MEIX_BIT] = mip_Interrupts_t_irq_external;
				csr_rdata_int[CSR_MFIX_BIT_HIGH:CSR_MFIX_BIT_LOW] = mip_Interrupts_t_irq_fast;
			end
			CSR_PMPCFG0: csr_rdata_int = {pmp_cfg_rdata[3], pmp_cfg_rdata[2], pmp_cfg_rdata[1], pmp_cfg_rdata[0]};
			//CSR_PMPCFG0: csr_rdata_int = pmp_cfg_rdata[3];
			CSR_PMPCFG1: csr_rdata_int = {pmp_cfg_rdata[7], pmp_cfg_rdata[6], pmp_cfg_rdata[5], pmp_cfg_rdata[4]};
			//CSR_PMPCFG1: csr_rdata_int = pmp_cfg_rdata[7];
			CSR_PMPCFG2: csr_rdata_int = {pmp_cfg_rdata[11], pmp_cfg_rdata[10], pmp_cfg_rdata[9], pmp_cfg_rdata[8]};
			//CSR_PMPCFG2: csr_rdata_int = pmp_cfg_rdata[11];
			CSR_PMPCFG3: csr_rdata_int = {pmp_cfg_rdata[15], pmp_cfg_rdata[14], pmp_cfg_rdata[13], pmp_cfg_rdata[12]};
			//CSR_PMPCFG3: csr_rdata_int = pmp_cfg_rdata[15];
			CSR_PMPADDR0: csr_rdata_int = pmp_addr_rdata[0];
			CSR_PMPADDR1: csr_rdata_int = pmp_addr_rdata[1];
			CSR_PMPADDR2: csr_rdata_int = pmp_addr_rdata[2];
			CSR_PMPADDR3: csr_rdata_int = pmp_addr_rdata[3];
			CSR_PMPADDR4: csr_rdata_int = pmp_addr_rdata[4];
			CSR_PMPADDR5: csr_rdata_int = pmp_addr_rdata[5];
			CSR_PMPADDR6: csr_rdata_int = pmp_addr_rdata[6];
			CSR_PMPADDR7: csr_rdata_int = pmp_addr_rdata[7];
			CSR_PMPADDR8: csr_rdata_int = pmp_addr_rdata[8];
			CSR_PMPADDR9: csr_rdata_int = pmp_addr_rdata[9];
			CSR_PMPADDR10: csr_rdata_int = pmp_addr_rdata[10];
			CSR_PMPADDR11: csr_rdata_int = pmp_addr_rdata[11];
			CSR_PMPADDR12: csr_rdata_int = pmp_addr_rdata[12];
			CSR_PMPADDR13: csr_rdata_int = pmp_addr_rdata[13];
			CSR_PMPADDR14: csr_rdata_int = pmp_addr_rdata[14];
			CSR_PMPADDR15: csr_rdata_int = pmp_addr_rdata[15];
			CSR_DCSR: begin
				//csr_rdata_int = dcsr_q;
				csr_rdata_int = {dcsr_q_Dcsr_t_xdebugver[3:0],dcsr_q_Dcsr_t_zero2[11:0],dcsr_q_Dcsr_t_ebreakm,dcsr_q_Dcsr_t_zero1,dcsr_q_Dcsr_t_ebreaks,dcsr_q_Dcsr_t_ebreaku,dcsr_q_Dcsr_t_stepie,dcsr_q_Dcsr_t_stopcount,dcsr_q_Dcsr_t_stoptime,dcsr_q_Dcsr_t_cause,dcsr_q_Dcsr_t_zero0,dcsr_q_Dcsr_t_mprven,dcsr_q_Dcsr_t_nmip,dcsr_q_Dcsr_t_step,dcsr_q_Dcsr_t_prv};
				illegal_csr = ~debug_mode_i;
			end
			CSR_DPC: begin
				csr_rdata_int = depc_q;
				illegal_csr = ~debug_mode_i;
			end
			CSR_DSCRATCH0: begin
				csr_rdata_int = dscratch0_q;
				illegal_csr = ~debug_mode_i;
			end
			CSR_DSCRATCH1: begin
				csr_rdata_int = dscratch1_q;
				illegal_csr = ~debug_mode_i;
			end
			CSR_MCOUNTINHIBIT: csr_rdata_int = mcountinhibit;
			CSR_MHPMEVENT3, CSR_MHPMEVENT4, CSR_MHPMEVENT5, CSR_MHPMEVENT6, CSR_MHPMEVENT7, CSR_MHPMEVENT8, CSR_MHPMEVENT9, CSR_MHPMEVENT10, CSR_MHPMEVENT11, CSR_MHPMEVENT12, CSR_MHPMEVENT13, CSR_MHPMEVENT14, CSR_MHPMEVENT15, CSR_MHPMEVENT16, CSR_MHPMEVENT17, CSR_MHPMEVENT18, CSR_MHPMEVENT19, CSR_MHPMEVENT20, CSR_MHPMEVENT21, CSR_MHPMEVENT22, CSR_MHPMEVENT23, CSR_MHPMEVENT24, CSR_MHPMEVENT25, CSR_MHPMEVENT26, CSR_MHPMEVENT27, CSR_MHPMEVENT28, CSR_MHPMEVENT29, CSR_MHPMEVENT30, CSR_MHPMEVENT31: csr_rdata_int = mhpmevent[mhpmcounter_idx];
			//CSR_MCYCLE, CSR_MINSTRET, CSR_MHPMCOUNTER3, CSR_MHPMCOUNTER4, CSR_MHPMCOUNTER5, CSR_MHPMCOUNTER6, CSR_MHPMCOUNTER7, CSR_MHPMCOUNTER8, CSR_MHPMCOUNTER9, CSR_MHPMCOUNTER10, CSR_MHPMCOUNTER11, CSR_MHPMCOUNTER12, CSR_MHPMCOUNTER13, CSR_MHPMCOUNTER14, CSR_MHPMCOUNTER15, CSR_MHPMCOUNTER16, CSR_MHPMCOUNTER17, CSR_MHPMCOUNTER18, CSR_MHPMCOUNTER19, CSR_MHPMCOUNTER20, CSR_MHPMCOUNTER21, CSR_MHPMCOUNTER22, CSR_MHPMCOUNTER23, CSR_MHPMCOUNTER24, CSR_MHPMCOUNTER25, CSR_MHPMCOUNTER26, CSR_MHPMCOUNTER27, CSR_MHPMCOUNTER28, CSR_MHPMCOUNTER29, CSR_MHPMCOUNTER30, CSR_MHPMCOUNTER31: csr_rdata_int = mhpmcounter_q[((31 - mhpmcounter_idx) * 64)+:32];
			CSR_MCYCLE, CSR_MINSTRET, CSR_MHPMCOUNTER3, CSR_MHPMCOUNTER4, CSR_MHPMCOUNTER5, CSR_MHPMCOUNTER6, CSR_MHPMCOUNTER7, CSR_MHPMCOUNTER8, CSR_MHPMCOUNTER9, CSR_MHPMCOUNTER10, CSR_MHPMCOUNTER11, CSR_MHPMCOUNTER12, CSR_MHPMCOUNTER13, CSR_MHPMCOUNTER14, CSR_MHPMCOUNTER15, CSR_MHPMCOUNTER16, CSR_MHPMCOUNTER17, CSR_MHPMCOUNTER18, CSR_MHPMCOUNTER19, CSR_MHPMCOUNTER20, CSR_MHPMCOUNTER21, CSR_MHPMCOUNTER22, CSR_MHPMCOUNTER23, CSR_MHPMCOUNTER24, CSR_MHPMCOUNTER25, CSR_MHPMCOUNTER26, CSR_MHPMCOUNTER27, CSR_MHPMCOUNTER28, CSR_MHPMCOUNTER29, CSR_MHPMCOUNTER30, CSR_MHPMCOUNTER31: csr_rdata_int = mhpmcounter_q[mhpmcounter_idx][31:0];
			//CSR_MCYCLEH, CSR_MINSTRETH, CSR_MHPMCOUNTER3H, CSR_MHPMCOUNTER4H, CSR_MHPMCOUNTER5H, CSR_MHPMCOUNTER6H, CSR_MHPMCOUNTER7H, CSR_MHPMCOUNTER8H, CSR_MHPMCOUNTER9H, CSR_MHPMCOUNTER10H, CSR_MHPMCOUNTER11H, CSR_MHPMCOUNTER12H, CSR_MHPMCOUNTER13H, CSR_MHPMCOUNTER14H, CSR_MHPMCOUNTER15H, CSR_MHPMCOUNTER16H, CSR_MHPMCOUNTER17H, CSR_MHPMCOUNTER18H, CSR_MHPMCOUNTER19H, CSR_MHPMCOUNTER20H, CSR_MHPMCOUNTER21H, CSR_MHPMCOUNTER22H, CSR_MHPMCOUNTER23H, CSR_MHPMCOUNTER24H, CSR_MHPMCOUNTER25H, CSR_MHPMCOUNTER26H, CSR_MHPMCOUNTER27H, CSR_MHPMCOUNTER28H, CSR_MHPMCOUNTER29H, CSR_MHPMCOUNTER30H, CSR_MHPMCOUNTER31H: csr_rdata_int = mhpmcounter_q[(((31 - mhpmcounter_idx) * 64) + 32)+:32];
			CSR_MCYCLEH, CSR_MINSTRETH, CSR_MHPMCOUNTER3H, CSR_MHPMCOUNTER4H, CSR_MHPMCOUNTER5H, CSR_MHPMCOUNTER6H, CSR_MHPMCOUNTER7H, CSR_MHPMCOUNTER8H, CSR_MHPMCOUNTER9H, CSR_MHPMCOUNTER10H, CSR_MHPMCOUNTER11H, CSR_MHPMCOUNTER12H, CSR_MHPMCOUNTER13H, CSR_MHPMCOUNTER14H, CSR_MHPMCOUNTER15H, CSR_MHPMCOUNTER16H, CSR_MHPMCOUNTER17H, CSR_MHPMCOUNTER18H, CSR_MHPMCOUNTER19H, CSR_MHPMCOUNTER20H, CSR_MHPMCOUNTER21H, CSR_MHPMCOUNTER22H, CSR_MHPMCOUNTER23H, CSR_MHPMCOUNTER24H, CSR_MHPMCOUNTER25H, CSR_MHPMCOUNTER26H, CSR_MHPMCOUNTER27H, CSR_MHPMCOUNTER28H, CSR_MHPMCOUNTER29H, CSR_MHPMCOUNTER30H, CSR_MHPMCOUNTER31H: csr_rdata_int = mhpmcounter_q[mhpmcounter_idx][63:32];
			default: illegal_csr = 1'b1;
		endcase
	end
	
   always @(*) begin
		exception_pc = pc_id_i;
		priv_lvl_d = priv_lvl_q;
		//mstatus_d = mstatus_q;
		//mie_d = mie_q;
		mscratch_d = mscratch_q;
		mepc_d = mepc_q;
		mcause_d = mcause_q;
		mtval_d = mtval_q;
		mtvec_d = (csr_mtvec_init_i ? {boot_addr_i[31:8], 6'b0, 2'b01} : mtvec_q);
		mstatus_d_Status_t_mie = mstatus_q_Status_t_mie ;
 mstatus_d_Status_t_mpie = mstatus_q_Status_t_mpie;
 mstatus_d_Status_t_mpp = mstatus_q_Status_t_mpp;
mstatus_d_Status_t_mprv = mstatus_q_Status_t_mprv ;
mstatus_d_Status_t_tw = mstatus_q_Status_t_tw;

mie_d_Interrupts_t_irq_software = mie_q_Interrupts_t_irq_software;
mie_d_Interrupts_t_irq_timer = mie_q_Interrupts_t_irq_timer;
mie_d_Interrupts_t_irq_external = mie_q_Interrupts_t_irq_external;
mie_d_Interrupts_t_irq_fast = mie_q_Interrupts_t_irq_fast;

dcsr_d_Dcsr_t_xdebugver	= dcsr_q_Dcsr_t_xdebugver; 
dcsr_d_Dcsr_t_zero2=	 dcsr_q_Dcsr_t_zero2;
dcsr_d_Dcsr_t_ebreakm=	 dcsr_q_Dcsr_t_ebreakm;
dcsr_d_Dcsr_t_zero1=	 dcsr_q_Dcsr_t_zero1;
dcsr_d_Dcsr_t_ebreaks=	 dcsr_q_Dcsr_t_ebreaks;
dcsr_d_Dcsr_t_ebreaku=	 dcsr_q_Dcsr_t_ebreaku;
dcsr_d_Dcsr_t_stepie=	 dcsr_q_Dcsr_t_stepie;
dcsr_d_Dcsr_t_stopcount=	 dcsr_q_Dcsr_t_stopcount;
dcsr_d_Dcsr_t_stoptime	= dcsr_q_Dcsr_t_stoptime;
dcsr_d_Dcsr_t_cause=	 dcsr_q_Dcsr_t_cause;
dcsr_d_Dcsr_t_zero0=	 dcsr_q_Dcsr_t_zero0;
dcsr_d_Dcsr_t_mprven=	 dcsr_q_Dcsr_t_mprven;
dcsr_d_Dcsr_t_nmip=	 dcsr_q_Dcsr_t_nmip;
dcsr_d_Dcsr_t_step=	 dcsr_q_Dcsr_t_step;
	

		//dcsr_d = dcsr_q;
		depc_d = depc_q;
		dscratch0_d = dscratch0_q;
		dscratch1_d = dscratch1_q;
		//mstack_d = mstack_q;
		mstack_d_StatusStk_t_mpie=mstack_q_StatusStk_t_mpie;
mstack_d_StatusStk_t_mpp=mstack_q_StatusStk_t_mpp;

		mstack_epc_d = mstack_epc_q;
		mstack_cause_d = mstack_cause_q;
		mcountinhibit_we = 1'b0;
		mhpmcounter_we = 1'b0;
		mhpmcounterh_we = 1'b0;
		if (csr_we_int)
			case (csr_addr_i)
                // CULPRIT
				CSR_MSTATUS: begin
					mstatus_d_Status_t_mie = csr_wdata_int[CSR_MSTATUS_MIE_BIT];
					mstatus_d_Status_t_mpie = csr_wdata_int[CSR_MSTATUS_MPIE_BIT];
					mstatus_d_Status_t_mpp = csr_wdata_int[CSR_MSTATUS_MPP_BIT_HIGH:CSR_MSTATUS_MPP_BIT_LOW];
					mstatus_d_Status_t_mprv = csr_wdata_int[CSR_MSTATUS_MPRV_BIT];
					mstatus_d_Status_t_tw = csr_wdata_int[CSR_MSTATUS_TW_BIT];

                /*
					if (((mstatus_d_Status_t_mpp != PRIV_LVL_M) && (mstatus_d_Status_t_mpp != PRIV_LVL_U)))
						mstatus_d_Status_t_mpp = PRIV_LVL_M;
                */
				end
				CSR_MIE: begin
					mie_d_Interrupts_t_irq_software = csr_wdata_int[CSR_MSIX_BIT];
					mie_d_Interrupts_t_irq_timer = csr_wdata_int[CSR_MTIX_BIT];
					mie_d_Interrupts_t_irq_external = csr_wdata_int[CSR_MEIX_BIT];
					mie_d_Interrupts_t_irq_fast = csr_wdata_int[CSR_MFIX_BIT_HIGH:CSR_MFIX_BIT_LOW];

				end
                // CULPRIT
				CSR_MSCRATCH: mscratch_d = csr_wdata_int;
				CSR_MEPC: mepc_d = {csr_wdata_int[31:1], 1'b0};
				CSR_MCAUSE: mcause_d = {csr_wdata_int[31], csr_wdata_int[4:0]};
				CSR_MTVAL: mtval_d = csr_wdata_int;
				CSR_MTVEC: mtvec_d = {csr_wdata_int[31:8], 6'b0, 2'b01};
				CSR_DCSR: begin
					{dcsr_d_Dcsr_t_xdebugver[3:0],dcsr_d_Dcsr_t_zero2[11:0],dcsr_d_Dcsr_t_ebreakm,dcsr_d_Dcsr_t_zero1,dcsr_d_Dcsr_t_ebreaks,dcsr_d_Dcsr_t_ebreaku,dcsr_d_Dcsr_t_stepie,dcsr_d_Dcsr_t_stopcount,dcsr_d_Dcsr_t_stoptime,dcsr_d_Dcsr_t_cause,dcsr_d_Dcsr_t_zero0,dcsr_d_Dcsr_t_mprven,dcsr_d_Dcsr_t_nmip,dcsr_d_Dcsr_t_step,dcsr_d_Dcsr_t_prv} = csr_wdata_int;
					dcsr_d_Dcsr_t_xdebugver = XDEBUGVER_STD;
					if (((dcsr_d_Dcsr_t_prv != PRIV_LVL_M) && (dcsr_d_Dcsr_t_prv != PRIV_LVL_U)))
						dcsr_d_Dcsr_t_prv = PRIV_LVL_M;
					dcsr_d_Dcsr_t_nmip = 1'b0;
					dcsr_d_Dcsr_t_mprven = 1'b0;
					dcsr_d_Dcsr_t_stopcount = 1'b0;
					dcsr_d_Dcsr_t_stoptime = 1'b0;
					dcsr_d_Dcsr_t_zero0 = 1'b0;
					dcsr_d_Dcsr_t_zero1 = 1'b0;
					dcsr_d_Dcsr_t_zero2 = 12'h0;
				end
				CSR_DPC: depc_d = {csr_wdata_int[31:1], 1'b0};
				CSR_DSCRATCH0: dscratch0_d = csr_wdata_int;
				CSR_DSCRATCH1: dscratch1_d = csr_wdata_int;
				CSR_MCOUNTINHIBIT: mcountinhibit_we = 1'b1;
				CSR_MCYCLE, CSR_MINSTRET, CSR_MHPMCOUNTER3, CSR_MHPMCOUNTER4, CSR_MHPMCOUNTER5, CSR_MHPMCOUNTER6, CSR_MHPMCOUNTER7, CSR_MHPMCOUNTER8, CSR_MHPMCOUNTER9, CSR_MHPMCOUNTER10, CSR_MHPMCOUNTER11, CSR_MHPMCOUNTER12, CSR_MHPMCOUNTER13, CSR_MHPMCOUNTER14, CSR_MHPMCOUNTER15, CSR_MHPMCOUNTER16, CSR_MHPMCOUNTER17, CSR_MHPMCOUNTER18, CSR_MHPMCOUNTER19, CSR_MHPMCOUNTER20, CSR_MHPMCOUNTER21, CSR_MHPMCOUNTER22, CSR_MHPMCOUNTER23, CSR_MHPMCOUNTER24, CSR_MHPMCOUNTER25, CSR_MHPMCOUNTER26, CSR_MHPMCOUNTER27, CSR_MHPMCOUNTER28, CSR_MHPMCOUNTER29, CSR_MHPMCOUNTER30, CSR_MHPMCOUNTER31: mhpmcounter_we[mhpmcounter_idx] = 1'b1;
				CSR_MCYCLEH, CSR_MINSTRETH, CSR_MHPMCOUNTER3H, CSR_MHPMCOUNTER4H, CSR_MHPMCOUNTER5H, CSR_MHPMCOUNTER6H, CSR_MHPMCOUNTER7H, CSR_MHPMCOUNTER8H, CSR_MHPMCOUNTER9H, CSR_MHPMCOUNTER10H, CSR_MHPMCOUNTER11H, CSR_MHPMCOUNTER12H, CSR_MHPMCOUNTER13H, CSR_MHPMCOUNTER14H, CSR_MHPMCOUNTER15H, CSR_MHPMCOUNTER16H, CSR_MHPMCOUNTER17H, CSR_MHPMCOUNTER18H, CSR_MHPMCOUNTER19H, CSR_MHPMCOUNTER20H, CSR_MHPMCOUNTER21H, CSR_MHPMCOUNTER22H, CSR_MHPMCOUNTER23H, CSR_MHPMCOUNTER24H, CSR_MHPMCOUNTER25H, CSR_MHPMCOUNTER26H, CSR_MHPMCOUNTER27H, CSR_MHPMCOUNTER28H, CSR_MHPMCOUNTER29H, CSR_MHPMCOUNTER30H, CSR_MHPMCOUNTER31H: mhpmcounterh_we[mhpmcounter_idx] = 1'b1;
				default: ;
			endcase
		case (1'b1)
			csr_save_cause_i: begin
				case (1'b1)
					csr_save_if_i: exception_pc = pc_if_i;
					csr_save_id_i: exception_pc = pc_id_i;
					default: ;
				endcase
				priv_lvl_d = PRIV_LVL_M;
				if (debug_csr_save_i) begin
					dcsr_d_Dcsr_t_prv = priv_lvl_q;
					dcsr_d_Dcsr_t_cause = debug_cause_i;
					depc_d = exception_pc;
				end
				else if (!debug_mode_i) begin
					mtval_d = csr_mtval_i;
					mstatus_d_Status_t_mie = 1'b0;
					mstatus_d_Status_t_mpie = mstatus_q_Status_t_mie;
					mstatus_d_Status_t_mpp = priv_lvl_q;
					mepc_d = exception_pc;
					mcause_d = csr_mcause_i;
					mstack_d_StatusStk_t_mpie = mstatus_q_Status_t_mpie;
					mstack_d_StatusStk_t_mpp = mstatus_q_Status_t_mpp;
					mstack_epc_d = mepc_q;
					mstack_cause_d = mcause_q;
				end
			end
			csr_restore_dret_i: priv_lvl_d = dcsr_q_Dcsr_t_prv;
			csr_restore_mret_i: begin
				priv_lvl_d = mstatus_q_Status_t_mpp;
				mstatus_d_Status_t_mie = mstatus_q_Status_t_mpie;
				mstatus_d_Status_t_mpie = mstack_q_StatusStk_t_mpie;
				mstatus_d_Status_t_mpp = mstack_q_StatusStk_t_mpp;
				mepc_d = mstack_epc_q;
				mcause_d = mstack_cause_q;
				mstack_d_StatusStk_t_mpie = 1'b1;
				mstack_d_StatusStk_t_mpp = PRIV_LVL_U;
			end
			default: ;
		endcase
	end

	always @(*) begin
		csr_wreq = 1'b1;
		case (csr_op_i)
			CSR_OP_WRITE: csr_wdata_int = csr_wdata_i;
			CSR_OP_SET: csr_wdata_int = (csr_wdata_i | csr_rdata_o);
			CSR_OP_CLEAR: csr_wdata_int = (~csr_wdata_i & csr_rdata_o);
			CSR_OP_READ: begin
				csr_wdata_int = csr_wdata_i;
				csr_wreq = 1'b0;
			end
			default: begin
			csr_wdata_int = 1'bX;
			csr_wreq = 1'bX;
		end
		endcase
	end
	
    assign csr_we_int = ((csr_wreq & ~illegal_csr_insn_o) & instr_new_id_i);
	assign csr_rdata_o = csr_rdata_int;
	assign csr_msip_o = mip_Interrupts_t_irq_software;
	assign csr_mtip_o = mip_Interrupts_t_irq_timer;
	assign csr_meip_o = mip_Interrupts_t_irq_external;
	assign csr_mfip_o = mip_Interrupts_t_irq_fast;
	assign csr_mepc_o = mepc_q;
	assign csr_depc_o = depc_q;
	assign csr_mtvec_o = mtvec_q;
	assign csr_mstatus_mie_o = mstatus_q_Status_t_mie;
	assign csr_mstatus_tw_o = mstatus_q_Status_t_tw;
	assign debug_single_step_o = dcsr_q_Dcsr_t_step;
	assign debug_ebreakm_o = dcsr_q_Dcsr_t_ebreakm;
	assign debug_ebreaku_o = dcsr_q_Dcsr_t_ebreaku;
	assign irq_pending_o = (((csr_msip_o | csr_mtip_o) | csr_meip_o) | |csr_mfip_o);
	
    always @(posedge clk_i or negedge rst_ni)
		if (!rst_ni) begin
			priv_lvl_q <= PRIV_LVL_M;
			mstatus_q_Status_t_mie <= 1'b0 ;
			mstatus_q_Status_t_mpie <= 1'b1;
			mstatus_q_Status_t_mpp <= PRIV_LVL_U;
			mstatus_q_Status_t_mprv <= 1'b0;
			mstatus_q_Status_t_tw <= 1'b0;

			
			//mstatus_q <= '{
			//	mie: 1'b0,
			//	mpie: 1'b1,
			//	mpp: PRIV_LVL_U,
			//	mprv: 1'b0,
			//	tw: 1'b0
			//};

			//mie_q <= 1'b0;
			 mie_q_Interrupts_t_irq_software <= 'b0;
	 mie_q_Interrupts_t_irq_timer <= 'b0;
	 mie_q_Interrupts_t_irq_external <= 'b0;
	 mie_q_Interrupts_t_irq_fast <='b0;

			mscratch_q <= 1'b0;
			mepc_q <= 1'b0;
			mcause_q <= 1'b0;
			mtval_q <= 1'b0;
			mtvec_q <= 32'b01;
			
			dcsr_q_Dcsr_t_xdebugver <=  XDEBUGVER_STD;
			dcsr_q_Dcsr_t_cause <= DBG_CAUSE_NONE;
			dcsr_q_Dcsr_t_prv <= PRIV_LVL_M;
			dcsr_q_Dcsr_t_zero2 <= 'b0;
			dcsr_q_Dcsr_t_ebreakm <= 'b0;
			dcsr_q_Dcsr_t_zero1 <= 'b0;
			dcsr_q_Dcsr_t_ebreaks <= 'b0;
			dcsr_q_Dcsr_t_ebreaku <= 'b0;
			dcsr_q_Dcsr_t_stepie <= 'b0;
			dcsr_q_Dcsr_t_stopcount <= 'b0;
			dcsr_q_Dcsr_t_stoptime <= 'b0;
			dcsr_q_Dcsr_t_zero0 <= 'b0;
			dcsr_q_Dcsr_t_mprven <= 'b0;
			dcsr_q_Dcsr_t_prv <= 'b0;
			dcsr_q_Dcsr_t_nmip <= 'b0;
			dcsr_q_Dcsr_t_step <= 'b0;

			//dcsr_q <= '{
			//	xdebugver: XDEBUGVER_STD,
			//	cause: DBG_CAUSE_NONE,
			//	prv: PRIV_LVL_M,
			//	default: 1'b0
			//};
		       
			depc_q <= 1'b0;
			dscratch0_q <= 1'b0;
			dscratch1_q <= 1'b0;
			
			mstack_q_StatusStk_t_mpie <= 1'b1;
			mstack_q_StatusStk_t_mpp <= PRIV_LVL_U;
			//mstack_q <= '{
			//	mpie: 1'b1,
			//	mpp: PRIV_LVL_U
			//};
			mstack_epc_q <= 1'b0;
			mstack_cause_q <= 1'b0;
		end
		else begin
			priv_lvl_q <= priv_lvl_d;
			//mstatus_q <= mstatus_d;
			mstatus_q_Status_t_mie = mstatus_d_Status_t_mie ;
 mstatus_q_Status_t_mpie = mstatus_d_Status_t_mpie;
 mstatus_q_Status_t_mpp = mstatus_d_Status_t_mpp;
mstatus_q_Status_t_mprv = mstatus_d_Status_t_mprv ;
mstatus_q_Status_t_tw = mstatus_d_Status_t_tw;

			//mie_q <= mie_d;
			mie_q_Interrupts_t_irq_software = mie_d_Interrupts_t_irq_software;
mie_q_Interrupts_t_irq_timer = mie_d_Interrupts_t_irq_timer;
mie_q_Interrupts_t_irq_external = mie_d_Interrupts_t_irq_external;
mie_q_Interrupts_t_irq_fast = mie_d_Interrupts_t_irq_fast;


			mscratch_q <= mscratch_d;
			mepc_q <= mepc_d;
			mcause_q <= mcause_d;
			mtval_q <= mtval_d;
			mtvec_q <= mtvec_d;
			//dcsr_q <= dcsr_d;
			dcsr_q_Dcsr_t_xdebugver	= dcsr_d_Dcsr_t_xdebugver; 
dcsr_q_Dcsr_t_zero2=	 dcsr_d_Dcsr_t_zero2;
dcsr_q_Dcsr_t_ebreakm=	 dcsr_d_Dcsr_t_ebreakm;
dcsr_q_Dcsr_t_zero1=	 dcsr_d_Dcsr_t_zero1;
dcsr_q_Dcsr_t_ebreaks=	 dcsr_d_Dcsr_t_ebreaks;
dcsr_q_Dcsr_t_ebreaku=	 dcsr_d_Dcsr_t_ebreaku;
dcsr_q_Dcsr_t_stepie=	 dcsr_d_Dcsr_t_stepie;
dcsr_q_Dcsr_t_stopcount=	 dcsr_d_Dcsr_t_stopcount;
dcsr_q_Dcsr_t_stoptime	= dcsr_d_Dcsr_t_stoptime;
dcsr_q_Dcsr_t_cause=	 dcsr_d_Dcsr_t_cause;
dcsr_q_Dcsr_t_zero0=	 dcsr_d_Dcsr_t_zero0;
dcsr_q_Dcsr_t_mprven=	 dcsr_d_Dcsr_t_mprven;
dcsr_q_Dcsr_t_nmip=	 dcsr_d_Dcsr_t_nmip;
dcsr_q_Dcsr_t_step=	 dcsr_d_Dcsr_t_step;
	

			depc_q <= depc_d;
			dscratch0_q <= dscratch0_d;
			dscratch1_q <= dscratch1_d;
			//mstack_q <= mstack_d;
			mstack_q_StatusStk_t_mpie=mstack_d_StatusStk_t_mpie;
mstack_q_StatusStk_t_mpp=mstack_d_StatusStk_t_mpp;

	

			mstack_epc_q <= mstack_epc_d;
			mstack_cause_q <= mstack_cause_d;
		end
	
    assign priv_mode_id_o = priv_lvl_q;
	assign priv_mode_if_o = priv_lvl_d;
	assign priv_mode_lsu_o = (mstatus_q_Status_t_mprv ? mstatus_q_Status_t_mpp : priv_lvl_q);
    
	generate
    /*
		if (PMPEnable) begin : g_pmp_registers
			reg pmp_cfg_lock [0:(PMPNumRegions - 1)];
			reg pmp_cfg_exec [0:(PMPNumRegions - 1)];
			reg pmp_cfg_write [0:(PMPNumRegions - 1)];
			reg pmp_cfg_read [0:(PMPNumRegions - 1)];
			reg pmp_cfg_mode_0 [0:(PMPNumRegions - 1)];
			reg pmp_cfg_mode_1 [0:(PMPNumRegions - 1)];
			wire pmp_cfg_wdata_lock [0:(PMPNumRegions - 1)];
			wire pmp_cfg_wdata_exec [0:(PMPNumRegions - 1)];
			wire pmp_cfg_wdata_write [0:(PMPNumRegions - 1)];
			wire pmp_cfg_wdata_read [0:(PMPNumRegions - 1)];
			reg pmp_cfg_wdata_mode_1 [0:(PMPNumRegions - 1)];
			reg pmp_cfg_wdata_mode_0 [0:(PMPNumRegions - 1)];
			reg [31:0] pmp_addr [0:(PMPNumRegions - 1)];
			wire [(PMPNumRegions - 1):0] pmp_cfg_we;
			wire [(PMPNumRegions - 1):0] pmp_addr_we;

			genvar g_exp_rd_data_i;
			for (g_exp_rd_data_i = 0; (g_exp_rd_data_i < PMP_MAX_REGIONS); g_exp_rd_data_i = (g_exp_rd_data_i + 1)) begin : g_exp_rd_data
				if ((g_exp_rd_data_i < PMPNumRegions)) begin : g_implemented_regions
					assign pmp_cfg_rdata[g_exp_rd_data_i] = {pmp_cfg_lock[g_exp_rd_data_i], 2'b00, pmp_cfg_mode_1[g_exp_rd_data_i], pmp_cfg_mode_0[g_exp_rd_data_i], pmp_cfg_exec[g_exp_rd_data_i], pmp_cfg_write[g_exp_rd_data_i], pmp_cfg_read[g_exp_rd_data_i]};
					if ((PMPGranularity == 0)) begin : g_pmp_g0
						always @(*) pmp_addr_rdata[g_exp_rd_data_i] = pmp_addr[g_exp_rd_data_i];
					end
					else if ((PMPGranularity == 1)) begin : g_pmp_g1
						always @(*) begin
							pmp_addr_rdata[g_exp_rd_data_i] = pmp_addr[g_exp_rd_data_i];
							if ((({pmp_cfg_mode_1[g_exp_rd_data_i], pmp_cfg_mode_0[g_exp_rd_data_i]} == PMP_MODE_OFF) || ({pmp_cfg_mode_1[g_exp_rd_data_i], pmp_cfg_mode_0[g_exp_rd_data_i]} == PMP_MODE_TOR)))
								pmp_addr_rdata[g_exp_rd_data_i][(PMPGranularity - 1):0] = 1'b0;
						end
					end
					else begin : g_pmp_g2
						always @(*) begin
							pmp_addr_rdata[g_exp_rd_data_i] = pmp_addr[g_exp_rd_data_i];
							if ((({pmp_cfg_mode_1[g_exp_rd_data_i], pmp_cfg_mode_0[g_exp_rd_data_i]} == PMP_MODE_OFF) || ({pmp_cfg_mode_1[g_exp_rd_data_i],pmp_cfg_mode_0[g_exp_rd_data_i]} == PMP_MODE_TOR)))
								pmp_addr_rdata[g_exp_rd_data_i][(PMPGranularity - 1):0] = 1'b0;
							else if (({pmp_cfg_mode_1[g_exp_rd_data_i],pmp_cfg_mode_0[g_exp_rd_data_i]} == PMP_MODE_NAPOT))
								pmp_addr_rdata[g_exp_rd_data_i][(PMPGranularity - 2):0] = 1'b1;
						end
					end
				end
				else begin : g_other_regions
					assign pmp_cfg_rdata[g_exp_rd_data_i] = 1'b0;
					always @(*) pmp_addr_rdata[g_exp_rd_data_i] = 1'b0;
				end
			end

			genvar g_pmp_csrs_i;
			for (g_pmp_csrs_i = 0; (g_pmp_csrs_i < PMPNumRegions); g_pmp_csrs_i = (g_pmp_csrs_i + 1)) begin : g_pmp_csrs
				assign pmp_cfg_we[g_pmp_csrs_i] = ((csr_we_int & ~pmp_cfg_lock[g_pmp_csrs_i]) & (csr_addr == (CSR_OFF_PMP_CFG + (g_pmp_csrs_i[11:0] >> 2))));
				assign pmp_cfg_wdata_lock[g_pmp_csrs_i] = csr_wdata_int[(((g_pmp_csrs_i % 4) * PMP_CFG_W) + 7)];
				always @(*)
					case (csr_wdata_int[(((g_pmp_csrs_i % 4) * PMP_CFG_W) + 3)+:2])
						2'b00: {pmp_cfg_wdata_mode_1[g_pmp_csrs_i], pmp_cfg_wdata_mode_0[g_pmp_csrs_i]} = PMP_MODE_OFF;
						2'b01: {pmp_cfg_wdata_mode_1[g_pmp_csrs_i], pmp_cfg_wdata_mode_0[g_pmp_csrs_i]} = PMP_MODE_TOR;
						2'b10: {pmp_cfg_wdata_mode_1[g_pmp_csrs_i], pmp_cfg_wdata_mode_0[g_pmp_csrs_i]} = ((PMPGranularity == 0) ? PMP_MODE_NA4 : PMP_MODE_OFF);
						2'b11: {pmp_cfg_wdata_mode_1[g_pmp_csrs_i], pmp_cfg_wdata_mode_0[g_pmp_csrs_i]} = PMP_MODE_NAPOT;
						default: {pmp_cfg_wdata_mode_1[g_pmp_csrs_i], pmp_cfg_wdata_mode_0[g_pmp_csrs_i]} = sv2v_cast_7D216(1'bX);
					endcase
				assign pmp_cfg_wdata_exec[g_pmp_csrs_i] = csr_wdata_int[(((g_pmp_csrs_i % 4) * PMP_CFG_W) + 2)];
				assign pmp_cfg_wdata_write[g_pmp_csrs_i] = &csr_wdata_int[((g_pmp_csrs_i % 4) * PMP_CFG_W)+:2];
				assign pmp_cfg_wdata_read[g_pmp_csrs_i] = csr_wdata_int[((g_pmp_csrs_i % 4) * PMP_CFG_W)];
				always @(posedge clk_i or negedge rst_ni)
					if (!rst_ni) begin
						pmp_cfg_lock[g_pmp_csrs_i] <= 'b0;
						pmp_cfg_exec[g_pmp_csrs_i] <= 'b0;
						pmp_cfg_write[g_pmp_csrs_i] <= 'b0;
						pmp_cfg_read[g_pmp_csrs_i] <= 'b0;
						pmp_cfg_mode_1[g_pmp_csrs_i] <= 'b0;
						pmp_cfg_mode_0[g_pmp_csrs_i] <= 'b0;
					end
					else if (pmp_cfg_we[g_pmp_csrs_i]) begin
						pmp_cfg_lock[g_pmp_csrs_i] <= pmp_cfg_wdata_lock[g_pmp_csrs_i];
						pmp_cfg_exec[g_pmp_csrs_i] <= pmp_cfg_wdata_exec[g_pmp_csrs_i];
						pmp_cfg_write[g_pmp_csrs_i] <= pmp_cfg_wdata_write[g_pmp_csrs_i];
						pmp_cfg_read[g_pmp_csrs_i] <= pmp_cfg_wdata_read[g_pmp_csrs_i];
						pmp_cfg_mode_1[g_pmp_csrs_i] <= pmp_cfg_wdata_mode_1[g_pmp_csrs_i];
						pmp_cfg_mode_0[g_pmp_csrs_i] <= pmp_cfg_wdata_mode_0[g_pmp_csrs_i];
					end
				if ((g_pmp_csrs_i < (PMPNumRegions - 1))) begin : g_lower
					assign pmp_addr_we[g_pmp_csrs_i] = (((csr_we_int & ~pmp_cfg_lock[g_pmp_csrs_i]) & ({pmp_cfg_mode_1[(g_pmp_csrs_i + 1)],pmp_cfg_mode_0[(g_pmp_csrs_i + 1)]} != PMP_MODE_TOR)) & (csr_addr == (CSR_OFF_PMP_ADDR + g_pmp_csrs_i[11:0])));
				end
				else begin : g_upper
					assign pmp_addr_we[g_pmp_csrs_i] = ((csr_we_int & ~pmp_cfg_lock[g_pmp_csrs_i]) & (csr_addr == (CSR_OFF_PMP_ADDR + g_pmp_csrs_i[11:0])));
				end
				always @(posedge clk_i or negedge rst_ni)
					if (!rst_ni)
						pmp_addr[g_pmp_csrs_i] <= 'b0;
					else if (pmp_addr_we[g_pmp_csrs_i])
						pmp_addr[g_pmp_csrs_i] <= csr_wdata_int;
				assign csr_pmp_cfg_o_lock[g_pmp_csrs_i] = pmp_cfg_lock[g_pmp_csrs_i];
				assign csr_pmp_cfg_o_exec[g_pmp_csrs_i] = pmp_cfg_exec[g_pmp_csrs_i];
				assign csr_pmp_cfg_o_write[g_pmp_csrs_i] = pmp_cfg_write[g_pmp_csrs_i];
				assign csr_pmp_cfg_o_read[g_pmp_csrs_i] = pmp_cfg_read[g_pmp_csrs_i];
				assign csr_pmp_cfg_o_mode_0[(((0 >= (PMPNumRegions - 1)) ? g_pmp_csrs_i : ((PMPNumRegions - 1) - g_pmp_csrs_i)) * 2)+:2] = pmp_cfg_mode_0[g_pmp_csrs_i];
				assign csr_pmp_cfg_o_mode_1[(((0 >= (PMPNumRegions - 1)) ? g_pmp_csrs_i : ((PMPNumRegions - 1) - g_pmp_csrs_i)) * 2)+:2] = pmp_cfg_mode_1[g_pmp_csrs_i];
				assign csr_pmp_addr_o[(((0 >= (PMPNumRegions - 1)) ? g_pmp_csrs_i : ((PMPNumRegions - 1) - g_pmp_csrs_i)) * 34)+:34] = {pmp_addr[g_pmp_csrs_i], 2'b00};
			end
		end
		else begin : g_no_pmp_tieoffs
    */
			genvar g_rdata_i;
			for (g_rdata_i = 0; (g_rdata_i < PMP_MAX_REGIONS); g_rdata_i = (g_rdata_i + 1)) begin : g_rdata
				assign pmp_addr_rdata[g_rdata_i] = 'b0;
				assign pmp_cfg_rdata[g_rdata_i] = 'b0;
			end

			genvar g_outputs_i;
			for (g_outputs_i = 0; (g_outputs_i < PMPNumRegions); g_outputs_i = (g_outputs_i + 1)) begin : g_outputs
				assign csr_pmp_cfg_o_lock[g_outputs_i] = 'b0;
				assign csr_pmp_cfg_o_exec[g_outputs_i] = 'b0;
				assign csr_pmp_cfg_o_write[g_outputs_i] = 'b0;
				assign csr_pmp_cfg_o_read[g_outputs_i] = 'b0;
				assign csr_pmp_cfg_o_mode_0[g_outputs_i] = 'b0;
				assign csr_pmp_cfg_o_mode_1[g_outputs_i] = 'b0;
				assign csr_pmp_addr_o[(((0 >= (PMPNumRegions - 1)) ? g_outputs_i : ((PMPNumRegions - 1) - g_outputs_i)) * 34)+:34] = 'b0;
			end
	//	end
	endgenerate

	always @(*) begin : mcountinhibit_update
		if ((mcountinhibit_we == 1'b1))
			mcountinhibit_d = {csr_wdata_int[31:2], 1'b0, csr_wdata_int[0]};
		else
			mcountinhibit_d = mcountinhibit_q;
	end

	/*assign mcountinhibit_force = {{(29 - MHPMCounterNum) {1'b1}}, {MHPMCounterNum {1'b0}}, 3'b000};*/
	assign mcountinhibit_force = {{21{1'b1}}, {21{1'b0}}, 3'b000};
	assign mcountinhibit = (mcountinhibit_q | mcountinhibit_force);

	always @(*) begin : gen_mhpmcounter_incr
		mhpmcounter_incr[0] = 1'b1;
		mhpmcounter_incr[1] = 1'b0;
		mhpmcounter_incr[2] = instr_ret_i;
		mhpmcounter_incr[3] = lsu_busy_i;
		mhpmcounter_incr[4] = (imiss_i & ~pc_set_i);
		mhpmcounter_incr[5] = mem_load_i;
		mhpmcounter_incr[6] = mem_store_i;
		mhpmcounter_incr[7] = jump_i;
		mhpmcounter_incr[8] = branch_i;
		mhpmcounter_incr[9] = branch_taken_i;
		mhpmcounter_incr[10] = instr_ret_compressed_i;
		begin : sv2v_autoblock_14
			reg [31:0] i;
			for (i = (3 + MHPMCounterNum); (i < 32); i = (i + 1))
				begin : gen_mhpmcounter_incr_inactive
					mhpmcounter_incr[i] = 1'b0;
				end
		end
	end

	always @(*) begin : gen_mhpmevent
		begin : sv2v_autoblock_15
			reg signed [31:0] i;
			for (i = 0; (i < 32); i = (i + 1))
				begin : gen_mhpmevent_active
					mhpmevent[i] = 1'b0;
					mhpmevent[i][i] = 1'b1;
				end
		end
		mhpmevent[1] = 1'b0;
		begin : sv2v_autoblock_16
			reg [31:0] i;
			for (i = (3 + MHPMCounterNum); (i < 32); i = (i + 1))
				begin : gen_mhpmevent_inactive
					mhpmevent[i] = 1'b0;
				end
		end
	end

	always @(*) begin : gen_mask
		begin : sv2v_autoblock_17
			reg signed [31:0] i;
			for (i = 0; (i < 3); i = (i + 1))
				begin : gen_mask_fixed
					mhpmcounter_mask[i] = {64 {1'b1}};
				end
		end
		begin : sv2v_autoblock_18
			reg [31:0] i;
			for (i = 3; (i < (3 + MHPMCounterNum)); i = (i + 1))
				begin : gen_mask_configurable
					mhpmcounter_mask[i] = {{(64 - MHPMCounterWidth) {1'b0}}, {MHPMCounterWidth {1'b1}}};
				end
		end
		begin : sv2v_autoblock_19
			reg [31:0] i;
			for (i = (3 + MHPMCounterNum); (i < 32); i = (i + 1))
				begin : gen_mask_inactive
					mhpmcounter_mask[i] = 1'b0;
				end
		end
	end

	always @(*) begin : mhpmcounter_update
		mhpmcounter_d = mhpmcounter_q;
		begin : sv2v_autoblock_20
			reg signed [31:0] i;
			for (i = 0; (i < 32); i = (i + 1))
				begin : gen_mhpmcounter_update
					if ((mhpmcounter_incr[i] & ~mcountinhibit[i]))
						mhpmcounter_d[((31 - i) * 64)+:64] = (mhpmcounter_mask[i] & (mhpmcounter_q[((31 - i) * 64)+:64] + 64'h1));
					if (mhpmcounter_we[i])
						mhpmcounter_d[((31 - i) * 64)+:32] = (mhpmcounter_mask[i][31:0] & csr_wdata_int);
					else if (mhpmcounterh_we[i])
						mhpmcounter_d[(((31 - i) * 64) + 32)+:32] = (mhpmcounter_mask[i][63:32] & csr_wdata_int);
				end
		end
	end

	always @(posedge clk_i or negedge rst_ni) begin : perf_counter_registers
		if (!rst_ni) begin
			mcountinhibit_q <= 1'b0;
			begin : sv2v_autoblock_21
				reg signed [31:0] i;
				for (i = 0; (i < 32); i = (i + 1))
					mhpmcounter_q[((31 - i) * 64)+:64] <= 1'b0;
			end
		end
		else begin
			mhpmcounter_q <= mhpmcounter_d;
			mcountinhibit_q <= mcountinhibit_d;
		end
	end

	function [31:0] sv2v_cast_32;
		input [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
	function  [(2 - 1):0] sv2v_cast_7D216;
		input [(2 - 1):0] inp;
		sv2v_cast_7D216 = inp;
	endfunction
	function [(2 - 1):0] sv2v_cast_D04CA;
		input [(2 - 1):0] inp;
		sv2v_cast_D04CA = inp;
	endfunction
   /* 
	initial begin
		$dumpfile("test.vcd");
		$dumpvars();
	end
    */
endmodule
