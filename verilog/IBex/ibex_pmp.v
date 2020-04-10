module ibex_pmp (
	clk_i,
	rst_ni,
	csr_pmp_cfg_i_lock,
	csr_pmp_cfg_i_exec,
	csr_pmp_cfg_i_write,
	csr_pmp_cfg_i_read,
	csr_pmp_cfg_i_mode_0,
	csr_pmp_cfg_i_mode_1,
	csr_pmp_addr_i,
	priv_mode_i_0,
	priv_mode_i_1,
	pmp_req_addr_i,
	pmp_req_type_i_0,
	pmp_req_type_i_1,
	pmp_req_err_o
);
	parameter [31:0] PMPGranularity = 0;
	parameter [31:0] PMPNumChan = 2;
	parameter [31:0] PMPNumRegions = 4;
	input wire clk_i;
	input wire rst_ni;
	//input ibex_pkg_pmp_cfg_t [0:(PMPNumRegions - 1)] csr_pmp_cfg_i;
	//STRUCT TO EXTRA INPUTS
	/*
	input wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_lock;
	input wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_exec;
	input wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_write;
	input wire [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_read;
	input [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_mode_0;
	input [0:(PMPNumRegions - 1)] csr_pmp_cfg_i_mode_1;
	*/

	input wire [0:3] csr_pmp_cfg_i_lock;
	input wire [0:3] csr_pmp_cfg_i_exec;
	input wire [0:3] csr_pmp_cfg_i_write;
	input wire [0:3] csr_pmp_cfg_i_read;
	input [0:3] csr_pmp_cfg_i_mode_0;
	input [0:3] csr_pmp_cfg_i_mode_1;

	/*
	input wire [((0 >= (PMPNumRegions - 1)) ? ((((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions) * 34) + (((PMPNumRegions - 1) * 34) - 1)) : (((((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions)) * 34) + -1)):((0 >= (PMPNumRegions - 1)) ? ((PMPNumRegions - 1) * 34) : 0)] csr_pmp_addr_i;
	input [0:(PMPNumChan - 1)] priv_mode_i_0;
	input [0:(PMPNumChan - 1)] priv_mode_i_1;
	input wire [((0 >= (PMPNumChan - 1)) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * 34) + (((PMPNumChan - 1) * 34) - 1)) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * 34) + -1)):((0 >= (PMPNumChan - 1)) ? ((PMPNumChan - 1) * 34) : 0)] pmp_req_addr_i;
	input [0:(PMPNumChan - 1)] pmp_req_type_i_0;
	input [0:(PMPNumChan - 1)] pmp_req_type_i_1;
	output wire [0:(PMPNumChan - 1)] pmp_req_err_o;
	`include "ibex_pkg.v"
	wire [33:0]region_start_addr [0:(PMPNumRegions - 1)] ;
	wire [33:(PMPGranularity + 2)] region_addr_mask [0:(PMPNumRegions - 1)];
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] region_match_high;
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] region_match_low;
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] region_match_both;
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] region_perm_check;
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] machine_access_fault;
	wire [(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + -1) : (((((PMPNumChan - 1) >= 0) ? PMPNumChan : (2 - PMPNumChan)) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + ((PMPNumRegions - 1) - 1))) : (((PMPNumRegions - 1) >= 0) ? ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) - 1)) : ((((0 >= (PMPNumChan - 1)) ? (2 - PMPNumChan) : PMPNumChan) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)) + (((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions))) - 1)))):(((PMPNumChan - 1) >= 0) ? (((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) : (((PMPNumRegions - 1) >= 0) ? ((PMPNumChan - 1) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) : ((PMPNumRegions - 1) + ((PMPNumChan - 1) * ((0 >= (PMPNumRegions - 1)) ? (2 - PMPNumRegions) : PMPNumRegions)))))] user_access_allowed;
	wire [(PMPNumChan - 1):0] access_fault;
	*/

	input wire [135:0] csr_pmp_addr_i;
	input [0:1] priv_mode_i_0;
	input [0:1] priv_mode_i_1;
	input wire [67:0] pmp_req_addr_i;
	input [0:1] pmp_req_type_i_0;
	input [0:1] pmp_req_type_i_1;
	output wire [0:1] pmp_req_err_o;
	`include "ibex_pkg.v"
	wire [33:0]region_start_addr [0:(PMPNumRegions - 1)] ;
	wire [33:(PMPGranularity + 2)] region_addr_mask [0:(PMPNumRegions - 1)];
	wire [7:0] region_match_high;
	wire [7:0] region_match_low;
	wire [7:0] region_match_both;
	wire [7:0] region_perm_check;
	wire [7:0] machine_access_fault;
	wire [7:0] user_access_allowed;
	wire [1:0] access_fault;



	generate
		genvar g_addr_exp_r;
		for (g_addr_exp_r = 0; (g_addr_exp_r < PMPNumRegions); g_addr_exp_r = (g_addr_exp_r + 1)) begin : g_addr_exp
			if ((g_addr_exp_r == 0)) begin : g_entry0
				assign region_start_addr[g_addr_exp_r] = (({csr_pmp_cfg_i_mode_1[g_addr_exp_r],csr_pmp_cfg_i_mode_0[g_addr_exp_r]} == PMP_MODE_TOR) ? 34'h000000000 : csr_pmp_addr_i[(((0 >= (PMPNumRegions - 1)) ? g_addr_exp_r : ((PMPNumRegions - 1) - g_addr_exp_r)) * 34)+:34]);
			end
			else begin : g_oth
				assign region_start_addr[g_addr_exp_r] = (({csr_pmp_cfg_i_mode_1[g_addr_exp_r],csr_pmp_cfg_i_mode_0[g_addr_exp_r]} == PMP_MODE_TOR) ? csr_pmp_addr_i[(((0 >= (PMPNumRegions - 1)) ? (g_addr_exp_r - 1) : ((PMPNumRegions - 1) - (g_addr_exp_r - 1))) * 34)+:34] : csr_pmp_addr_i[(((0 >= (PMPNumRegions - 1)) ? g_addr_exp_r : ((PMPNumRegions - 1) - g_addr_exp_r)) * 34)+:34]);
			end
			genvar g_bitmask_b;
			for (g_bitmask_b = (PMPGranularity + 2); (g_bitmask_b < 34); g_bitmask_b = (g_bitmask_b + 1)) begin : g_bitmask
				if ((g_bitmask_b == (PMPGranularity + 2))) begin : g_bit0
					assign region_addr_mask[g_addr_exp_r][g_bitmask_b] = ({csr_pmp_cfg_i_mode_1[g_addr_exp_r],csr_pmp_cfg_i_mode_0[g_addr_exp_r]} != PMP_MODE_NAPOT);
				end
				else begin : g_others
					assign region_addr_mask[g_addr_exp_r][g_bitmask_b] = (({csr_pmp_cfg_i_mode_1[g_addr_exp_r],csr_pmp_cfg_i_mode_0[g_addr_exp_r]} != PMP_MODE_NAPOT) | ~&csr_pmp_addr_i[((((0 >= (PMPNumRegions - 1)) ? g_addr_exp_r : ((PMPNumRegions - 1) - g_addr_exp_r)) * 34) + (PMPGranularity + 2))+:(((g_bitmask_b - 1) >= (PMPGranularity + 2)) ? (((g_bitmask_b - 1) - (PMPGranularity + 2)) + 1) : (((PMPGranularity + 2) - (g_bitmask_b - 1)) + 1))]);
				end
			end
		end
	endgenerate
	generate
		genvar g_access_check_c;
		for (g_access_check_c = 0; (g_access_check_c < PMPNumChan); g_access_check_c = (g_access_check_c + 1)) begin : g_access_check
			genvar g_regions_r;
			for (g_regions_r = 0; (g_regions_r < PMPNumRegions); g_regions_r = (g_regions_r + 1)) begin : g_regions
				assign region_match_low[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = (pmp_req_addr_i[((((0 >= (PMPNumChan - 1)) ? g_access_check_c : ((PMPNumChan - 1) - g_access_check_c)) * 34) + (PMPGranularity + 2))+:((33 >= (PMPGranularity + 2)) ? (34 - (PMPGranularity + 2)) : (((PMPGranularity + 2) - 33) + 1))] >= (region_start_addr[g_regions_r][33:(PMPGranularity + 2)] & region_addr_mask[g_regions_r]));
				assign region_match_high[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = (pmp_req_addr_i[((((0 >= (PMPNumChan - 1)) ? g_access_check_c : ((PMPNumChan - 1) - g_access_check_c)) * 34) + (PMPGranularity + 2))+:((33 >= (PMPGranularity + 2)) ? (34 - (PMPGranularity + 2)) : (((PMPGranularity + 2) - 33) + 1))] <= csr_pmp_addr_i[((((0 >= (PMPNumRegions - 1)) ? g_regions_r : ((PMPNumRegions - 1) - g_regions_r)) * 34) + (PMPGranularity + 2))+:((33 >= (PMPGranularity + 2)) ? (34 - (PMPGranularity + 2)) : (((PMPGranularity + 2) - 33) + 1))]);
				assign region_match_both[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = ((region_match_low[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] & region_match_high[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))]) & ({csr_pmp_cfg_i_mode_1[g_regions_r],csr_pmp_cfg_i_mode_0[g_regions_r]} != PMP_MODE_OFF));
				assign region_perm_check[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = (((({pmp_req_type_i_1[g_access_check_c],pmp_req_type_i_0[g_access_check_c]} == PMP_ACC_EXEC) & csr_pmp_cfg_i_exec[g_regions_r]) | (({pmp_req_type_i_1[g_access_check_c],pmp_req_type_i_0[g_access_check_c]} == PMP_ACC_WRITE) & csr_pmp_cfg_i_write[g_regions_r])) | (({pmp_req_type_i_1[g_access_check_c],pmp_req_type_i_0[g_access_check_c]} == PMP_ACC_READ) & csr_pmp_cfg_i_read[g_regions_r]));
				assign machine_access_fault[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = ((region_match_both[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] & csr_pmp_cfg_i_lock[g_regions_r]) & ~region_perm_check[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))]);
				assign user_access_allowed[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] = (region_match_both[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))] & region_perm_check[(((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))) + (((PMPNumRegions - 1) >= 0) ? g_regions_r : (0 - (g_regions_r - (PMPNumRegions - 1)))))]);
			end
			assign access_fault[g_access_check_c] = (({priv_mode_i_1[g_access_check_c],priv_mode_i_0[g_access_check_c]} == PRIV_LVL_M) ? |machine_access_fault[((((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) + ((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))))+:(((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))] : ~|user_access_allowed[((((PMPNumRegions - 1) >= 0) ? 0 : (PMPNumRegions - 1)) + ((((PMPNumChan - 1) >= 0) ? g_access_check_c : (0 - (g_access_check_c - (PMPNumChan - 1)))) * (((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))))+:(((PMPNumRegions - 1) >= 0) ? PMPNumRegions : (2 - PMPNumRegions))]);
			assign pmp_req_err_o[g_access_check_c] = access_fault[g_access_check_c];
		end
	endgenerate
    /*
	initial begin
		$dumpfile("test.vcd");
		$dumpvars();
	end
    */
endmodule
