module ibex_tracer (
	clk_i,
	rst_ni,
	hart_id_i,
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
	rvfi_mem_wdata
);
	input wire clk_i;
	input wire rst_ni;
	input wire [31:0] hart_id_i;
	input wire rvfi_valid;
	input wire [63:0] rvfi_order;
	input wire [31:0] rvfi_insn;
	input wire rvfi_trap;
	input wire rvfi_halt;
	input wire rvfi_intr;
	input wire [1:0] rvfi_mode;
	input wire [4:0] rvfi_rs1_addr;
	input wire [4:0] rvfi_rs2_addr;
	input wire [31:0] rvfi_rs1_rdata;
	input wire [31:0] rvfi_rs2_rdata;
	input wire [4:0] rvfi_rd_addr;
	input wire [31:0] rvfi_rd_wdata;
	input wire [31:0] rvfi_pc_rdata;
	input wire [31:0] rvfi_pc_wdata;
	input wire [31:0] rvfi_mem_addr;
	input wire [3:0] rvfi_mem_rmask;
	input wire [3:0] rvfi_mem_wmask;
	input wire [31:0] rvfi_mem_rdata;
	input wire [31:0] rvfi_mem_wdata;
	wire [63:0] unused_rvfi_order = rvfi_order;
	wire unused_rvfi_trap = rvfi_trap;
	wire unused_rvfi_halt = rvfi_halt;
	wire unused_rvfi_intr = rvfi_intr;
	wire [1:0] unused_rvfi_mode = rvfi_mode;
	`include "ibex_pkg.v"
	`include "ibex_tracer_pkg.v"
	integer file_handle;
	reg file_opened;
	reg [256:0] file_name;
	reg [31:0] cycle;
	reg [256:0] decoded_str;
	reg insn_is_compressed;
	localparam RS1 = (1 << 0);
	localparam RS2 = (1 << 1);
	localparam RD = (1 << 2);
	localparam MEM = (1 << 3);
	reg [3:0] data_accessed;
	task printbuffer_dumpline;
		reg [256:0] rvfi_insn_str;
		begin
			if ((file_handle == 32'h0)) begin : sv2v_autoblock_1
				reg [256:0] file_name_base;
				file_name_base = "trace_core";
				$value$plusargs("ibex_tracer_file_base=%s", file_name_base);
				$sformat(file_name, "%s_%h.log", file_name_base, hart_id_i);
				$display("%m: Writing execution trace to %s", file_name);
				if ((file_opened == 1'b0)) begin
					file_handle = $fopen(file_name, "w");
					file_opened = 1'b1; 
				end
				else
					file_handle = $fopen(file_name, "a+");
				$fwrite(file_handle, "Time\tCycle\tPC\tInsn\tDecoded instruction\tRegister and memory contents\n");
			end
			if (insn_is_compressed)
				rvfi_insn_str = $sformatf("%h", rvfi_insn[15:0]);
			else
				rvfi_insn_str = $sformatf("%h", rvfi_insn);
			$fwrite(file_handle, "%15t\t%d\t%h\t%s\t%s\t", $time, cycle, rvfi_pc_rdata, rvfi_insn_str, decoded_str);
			if (((data_accessed & RS1) != 0))
				$fwrite(file_handle, " %s:0x%08x", reg_addr_to_str(rvfi_rs1_addr), rvfi_rs1_rdata);
			if (((data_accessed & RS2) != 0))
				$fwrite(file_handle, " %s:0x%08x", reg_addr_to_str(rvfi_rs2_addr), rvfi_rs2_rdata);
			if (((data_accessed & RD) != 0))
				$fwrite(file_handle, " %s=0x%08x", reg_addr_to_str(rvfi_rd_addr), rvfi_rd_wdata);
			if (((data_accessed & MEM) != 0)) begin
				$fwrite(file_handle, " PA:0x%08x", rvfi_mem_addr);
				if ((rvfi_mem_rmask != 4'b000))
					$fwrite(file_handle, " store:0x%08x", rvfi_mem_wdata);
				if ((rvfi_mem_wmask != 4'b000))
					$fwrite(file_handle, " load:0x%08x", rvfi_mem_rdata);
			end
			$fwrite(file_handle, "\n");
			$fclose(file_handle);
		end
	endtask
	function [256:0] reg_addr_to_str;
		input  [4:0] addr;
		if ((addr < 10))
			reg_addr_to_str = $sformatf(" x%0d", addr);
		else
			reg_addr_to_str = $sformatf("x%0d", addr);
	endfunction
	function [256:0] get_csr_name;
		input [11:0] csr_addr;
		case (csr_addr)
			12'd0: get_csr_name = "ustatus";
			12'd4: get_csr_name = "uie";
			12'd5: get_csr_name = "utvec";
			12'd64: get_csr_name = "uscratch";
			12'd65: get_csr_name = "uepc";
			12'd66: get_csr_name = "ucause";
			12'd67: get_csr_name = "utval";
			12'd68: get_csr_name = "uip";
			12'd1: get_csr_name = "fflags";
			12'd2: get_csr_name = "frm";
			12'd3: get_csr_name = "fcsr";
			12'd3072: get_csr_name = "cycle";
			12'd3073: get_csr_name = "time";
			12'd3074: get_csr_name = "instret";
			12'd3075: get_csr_name = "hpmcounter3";
			12'd3076: get_csr_name = "hpmcounter4";
			12'd3077: get_csr_name = "hpmcounter5";
			12'd3078: get_csr_name = "hpmcounter6";
			12'd3079: get_csr_name = "hpmcounter7";
			12'd3080: get_csr_name = "hpmcounter8";
			12'd3081: get_csr_name = "hpmcounter9";
			12'd3082: get_csr_name = "hpmcounter10";
			12'd3083: get_csr_name = "hpmcounter11";
			12'd3084: get_csr_name = "hpmcounter12";
			12'd3085: get_csr_name = "hpmcounter13";
			12'd3086: get_csr_name = "hpmcounter14";
			12'd3087: get_csr_name = "hpmcounter15";
			12'd3088: get_csr_name = "hpmcounter16";
			12'd3089: get_csr_name = "hpmcounter17";
			12'd3090: get_csr_name = "hpmcounter18";
			12'd3091: get_csr_name = "hpmcounter19";
			12'd3092: get_csr_name = "hpmcounter20";
			12'd3093: get_csr_name = "hpmcounter21";
			12'd3094: get_csr_name = "hpmcounter22";
			12'd3095: get_csr_name = "hpmcounter23";
			12'd3096: get_csr_name = "hpmcounter24";
			12'd3097: get_csr_name = "hpmcounter25";
			12'd3098: get_csr_name = "hpmcounter26";
			12'd3099: get_csr_name = "hpmcounter27";
			12'd3100: get_csr_name = "hpmcounter28";
			12'd3101: get_csr_name = "hpmcounter29";
			12'd3102: get_csr_name = "hpmcounter30";
			12'd3103: get_csr_name = "hpmcounter31";
			12'd3200: get_csr_name = "cycleh";
			12'd3201: get_csr_name = "timeh";
			12'd3202: get_csr_name = "instreth";
			12'd3203: get_csr_name = "hpmcounter3h";
			12'd3204: get_csr_name = "hpmcounter4h";
			12'd3205: get_csr_name = "hpmcounter5h";
			12'd3206: get_csr_name = "hpmcounter6h";
			12'd3207: get_csr_name = "hpmcounter7h";
			12'd3208: get_csr_name = "hpmcounter8h";
			12'd3209: get_csr_name = "hpmcounter9h";
			12'd3210: get_csr_name = "hpmcounter10h";
			12'd3211: get_csr_name = "hpmcounter11h";
			12'd3212: get_csr_name = "hpmcounter12h";
			12'd3213: get_csr_name = "hpmcounter13h";
			12'd3214: get_csr_name = "hpmcounter14h";
			12'd3215: get_csr_name = "hpmcounter15h";
			12'd3216: get_csr_name = "hpmcounter16h";
			12'd3217: get_csr_name = "hpmcounter17h";
			12'd3218: get_csr_name = "hpmcounter18h";
			12'd3219: get_csr_name = "hpmcounter19h";
			12'd3220: get_csr_name = "hpmcounter20h";
			12'd3221: get_csr_name = "hpmcounter21h";
			12'd3222: get_csr_name = "hpmcounter22h";
			12'd3223: get_csr_name = "hpmcounter23h";
			12'd3224: get_csr_name = "hpmcounter24h";
			12'd3225: get_csr_name = "hpmcounter25h";
			12'd3226: get_csr_name = "hpmcounter26h";
			12'd3227: get_csr_name = "hpmcounter27h";
			12'd3228: get_csr_name = "hpmcounter28h";
			12'd3229: get_csr_name = "hpmcounter29h";
			12'd3230: get_csr_name = "hpmcounter30h";
			12'd3231: get_csr_name = "hpmcounter31h";
			12'd256: get_csr_name = "sstatus";
			12'd258: get_csr_name = "sedeleg";
			12'd259: get_csr_name = "sideleg";
			12'd260: get_csr_name = "sie";
			12'd261: get_csr_name = "stvec";
			12'd262: get_csr_name = "scounteren";
			12'd320: get_csr_name = "sscratch";
			12'd321: get_csr_name = "sepc";
			12'd322: get_csr_name = "scause";
			12'd323: get_csr_name = "stval";
			12'd324: get_csr_name = "sip";
			12'd384: get_csr_name = "satp";
			12'd3857: get_csr_name = "mvendorid";
			12'd3858: get_csr_name = "marchid";
			12'd3859: get_csr_name = "mimpid";
			12'd3860: get_csr_name = "mhartid";
			12'd768: get_csr_name = "mstatus";
			12'd769: get_csr_name = "misa";
			12'd770: get_csr_name = "medeleg";
			12'd771: get_csr_name = "mideleg";
			12'd772: get_csr_name = "mie";
			12'd773: get_csr_name = "mtvec";
			12'd774: get_csr_name = "mcounteren";
			12'd832: get_csr_name = "mscratch";
			12'd833: get_csr_name = "mepc";
			12'd834: get_csr_name = "mcause";
			12'd835: get_csr_name = "mtval";
			12'd836: get_csr_name = "mip";
			12'd928: get_csr_name = "pmpcfg0";
			12'd929: get_csr_name = "pmpcfg1";
			12'd930: get_csr_name = "pmpcfg2";
			12'd931: get_csr_name = "pmpcfg3";
			12'd944: get_csr_name = "pmpaddr0";
			12'd945: get_csr_name = "pmpaddr1";
			12'd946: get_csr_name = "pmpaddr2";
			12'd947: get_csr_name = "pmpaddr3";
			12'd948: get_csr_name = "pmpaddr4";
			12'd949: get_csr_name = "pmpaddr5";
			12'd950: get_csr_name = "pmpaddr6";
			12'd951: get_csr_name = "pmpaddr7";
			12'd952: get_csr_name = "pmpaddr8";
			12'd953: get_csr_name = "pmpaddr9";
			12'd954: get_csr_name = "pmpaddr10";
			12'd955: get_csr_name = "pmpaddr11";
			12'd956: get_csr_name = "pmpaddr12";
			12'd957: get_csr_name = "pmpaddr13";
			12'd958: get_csr_name = "pmpaddr14";
			12'd959: get_csr_name = "pmpaddr15";
			12'd2816: get_csr_name = "mcycle";
			12'd2818: get_csr_name = "minstret";
			12'd2819: get_csr_name = "mhpmcounter3";
			12'd2820: get_csr_name = "mhpmcounter4";
			12'd2821: get_csr_name = "mhpmcounter5";
			12'd2822: get_csr_name = "mhpmcounter6";
			12'd2823: get_csr_name = "mhpmcounter7";
			12'd2824: get_csr_name = "mhpmcounter8";
			12'd2825: get_csr_name = "mhpmcounter9";
			12'd2826: get_csr_name = "mhpmcounter10";
			12'd2827: get_csr_name = "mhpmcounter11";
			12'd2828: get_csr_name = "mhpmcounter12";
			12'd2829: get_csr_name = "mhpmcounter13";
			12'd2830: get_csr_name = "mhpmcounter14";
			12'd2831: get_csr_name = "mhpmcounter15";
			12'd2832: get_csr_name = "mhpmcounter16";
			12'd2833: get_csr_name = "mhpmcounter17";
			12'd2834: get_csr_name = "mhpmcounter18";
			12'd2835: get_csr_name = "mhpmcounter19";
			12'd2836: get_csr_name = "mhpmcounter20";
			12'd2837: get_csr_name = "mhpmcounter21";
			12'd2838: get_csr_name = "mhpmcounter22";
			12'd2839: get_csr_name = "mhpmcounter23";
			12'd2840: get_csr_name = "mhpmcounter24";
			12'd2841: get_csr_name = "mhpmcounter25";
			12'd2842: get_csr_name = "mhpmcounter26";
			12'd2843: get_csr_name = "mhpmcounter27";
			12'd2844: get_csr_name = "mhpmcounter28";
			12'd2845: get_csr_name = "mhpmcounter29";
			12'd2846: get_csr_name = "mhpmcounter30";
			12'd2847: get_csr_name = "mhpmcounter31";
			12'd2944: get_csr_name = "mcycleh";
			12'd2946: get_csr_name = "minstreth";
			12'd2947: get_csr_name = "mhpmcounter3h";
			12'd2948: get_csr_name = "mhpmcounter4h";
			12'd2949: get_csr_name = "mhpmcounter5h";
			12'd2950: get_csr_name = "mhpmcounter6h";
			12'd2951: get_csr_name = "mhpmcounter7h";
			12'd2952: get_csr_name = "mhpmcounter8h";
			12'd2953: get_csr_name = "mhpmcounter9h";
			12'd2954: get_csr_name = "mhpmcounter10h";
			12'd2955: get_csr_name = "mhpmcounter11h";
			12'd2956: get_csr_name = "mhpmcounter12h";
			12'd2957: get_csr_name = "mhpmcounter13h";
			12'd2958: get_csr_name = "mhpmcounter14h";
			12'd2959: get_csr_name = "mhpmcounter15h";
			12'd2960: get_csr_name = "mhpmcounter16h";
			12'd2961: get_csr_name = "mhpmcounter17h";
			12'd2962: get_csr_name = "mhpmcounter18h";
			12'd2963: get_csr_name = "mhpmcounter19h";
			12'd2964: get_csr_name = "mhpmcounter20h";
			12'd2965: get_csr_name = "mhpmcounter21h";
			12'd2966: get_csr_name = "mhpmcounter22h";
			12'd2967: get_csr_name = "mhpmcounter23h";
			12'd2968: get_csr_name = "mhpmcounter24h";
			12'd2969: get_csr_name = "mhpmcounter25h";
			12'd2970: get_csr_name = "mhpmcounter26h";
			12'd2971: get_csr_name = "mhpmcounter27h";
			12'd2972: get_csr_name = "mhpmcounter28h";
			12'd2973: get_csr_name = "mhpmcounter29h";
			12'd2974: get_csr_name = "mhpmcounter30h";
			12'd2975: get_csr_name = "mhpmcounter31h";
			12'd803: get_csr_name = "mhpmevent3";
			12'd804: get_csr_name = "mhpmevent4";
			12'd805: get_csr_name = "mhpmevent5";
			12'd806: get_csr_name = "mhpmevent6";
			12'd807: get_csr_name = "mhpmevent7";
			12'd808: get_csr_name = "mhpmevent8";
			12'd809: get_csr_name = "mhpmevent9";
			12'd810: get_csr_name = "mhpmevent10";
			12'd811: get_csr_name = "mhpmevent11";
			12'd812: get_csr_name = "mhpmevent12";
			12'd813: get_csr_name = "mhpmevent13";
			12'd814: get_csr_name = "mhpmevent14";
			12'd815: get_csr_name = "mhpmevent15";
			12'd816: get_csr_name = "mhpmevent16";
			12'd817: get_csr_name = "mhpmevent17";
			12'd818: get_csr_name = "mhpmevent18";
			12'd819: get_csr_name = "mhpmevent19";
			12'd820: get_csr_name = "mhpmevent20";
			12'd821: get_csr_name = "mhpmevent21";
			12'd822: get_csr_name = "mhpmevent22";
			12'd823: get_csr_name = "mhpmevent23";
			12'd824: get_csr_name = "mhpmevent24";
			12'd825: get_csr_name = "mhpmevent25";
			12'd826: get_csr_name = "mhpmevent26";
			12'd827: get_csr_name = "mhpmevent27";
			12'd828: get_csr_name = "mhpmevent28";
			12'd829: get_csr_name = "mhpmevent29";
			12'd830: get_csr_name = "mhpmevent30";
			12'd831: get_csr_name = "mhpmevent31";
			12'd1952: get_csr_name = "tselect";
			12'd1953: get_csr_name = "tdata1";
			12'd1954: get_csr_name = "tdata2";
			12'd1955: get_csr_name = "tdata3";
			12'd1968: get_csr_name = "dcsr";
			12'd1969: get_csr_name = "dpc";
			12'd1970: get_csr_name = "dscratch";
			12'd512: get_csr_name = "hstatus";
			12'd514: get_csr_name = "hedeleg";
			12'd515: get_csr_name = "hideleg";
			12'd516: get_csr_name = "hie";
			12'd517: get_csr_name = "htvec";
			12'd576: get_csr_name = "hscratch";
			12'd577: get_csr_name = "hepc";
			12'd578: get_csr_name = "hcause";
			12'd579: get_csr_name = "hbadaddr";
			12'd580: get_csr_name = "hip";
			12'd896: get_csr_name = "mbase";
			12'd897: get_csr_name = "mbound";
			12'd898: get_csr_name = "mibase";
			12'd899: get_csr_name = "mibound";
			12'd900: get_csr_name = "mdbase";
			12'd901: get_csr_name = "mdbound";
			12'd800: get_csr_name = "mucounteren";
			12'd801: get_csr_name = "mscounteren";
			12'd802: get_csr_name = "mhcounteren";
			default: get_csr_name = $sformatf("0x%x", csr_addr);
		endcase
	endfunction
	task decode_mnemonic;
		input [256:0] mnemonic;
		decoded_str = mnemonic;
	endtask
	task decode_r_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = ((RS1 | RS2) | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d,x%0d", mnemonic, rvfi_rd_addr, rvfi_rs1_addr, rvfi_rs2_addr);
		end
	endtask
	task decode_i_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d,%0d", mnemonic, rvfi_rd_addr, rvfi_rs1_addr, $signed({{20 {rvfi_insn[31]}}, rvfi_insn[31:20]}));
		end
	endtask
	task decode_i_shift_insn;
		input [256:0] mnemonic;
		reg [4:0] shamt;
		begin
			shamt = rvfi_insn[24:20];
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d,0x%0x", mnemonic, rvfi_rd_addr, rvfi_rs1_addr, shamt);
		end
	endtask
	task decode_i_jalr_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,%0d(x%0d)", mnemonic, rvfi_rd_addr, $signed({{20 {rvfi_insn[31]}}, rvfi_insn[31:20]}), rvfi_rs1_addr);
		end
	endtask
	task decode_u_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = RD;
			decoded_str = $sformatf("%s\tx%0d,0x%0x", mnemonic, rvfi_rd_addr, rvfi_insn[31:12]);
		end
	endtask
	task decode_j_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = RD;
			decoded_str = $sformatf("%s\tx%0d,%0x", mnemonic, rvfi_rd_addr, rvfi_pc_wdata);
		end
	endtask
	task decode_b_insn;
		input [256:0] mnemonic;
		reg [31:0] branch_target;
		reg [31:0] imm;
		begin
			imm = $signed({{19 {rvfi_insn[31]}}, rvfi_insn[31], rvfi_insn[7], rvfi_insn[30:25], rvfi_insn[11:8], 1'b0});
			branch_target = (rvfi_pc_rdata + imm);
			data_accessed = ((RS1 | RS2) | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d,%0x", mnemonic, rvfi_rs1_addr, rvfi_rs2_addr, branch_target);
		end
	endtask
	task decode_csr_insn;
		input [256:0] mnemonic;
		reg [11:0] csr;
		reg [256:0] csr_name;
		begin
			csr = rvfi_insn[31:20];
			csr_name = get_csr_name(csr);
			data_accessed = RD;
			if (!rvfi_insn[14]) begin
				data_accessed = (data_accessed | RS1);
				decoded_str = $sformatf("%s\tx%0d,%s,x%0d", mnemonic, rvfi_rd_addr, csr_name, rvfi_rs1_addr);
			end
			else
				decoded_str = $sformatf("%s\tx%0d,%s,%0d", mnemonic, rvfi_rd_addr, csr_name, {27'b0, rvfi_insn[19:15]});
		end
	endtask
	task decode_cr_insn;
		input [256:0] mnemonic;
		if ((rvfi_rs2_addr == 5'b0)) begin
			if ((rvfi_insn[12] == 1'b1))
				data_accessed = (RS1 | RD);
			else
				data_accessed = RS1;
			decoded_str = $sformatf("%s\tx%0d", mnemonic, rvfi_rs1_addr);
		end
		else begin
			data_accessed = ((RS1 | RS2) | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d", mnemonic, rvfi_rd_addr, rvfi_rs2_addr);
		end
	endtask
	task decode_ci_cli_insn;
		input [256:0] mnemonic;
		reg [5:0] imm;
		begin
			imm = {rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = RD;
			decoded_str = $sformatf("%s\tx%0d,%0d", mnemonic, rvfi_rd_addr, $signed(imm));
		end
	endtask
	task decode_ci_caddi_insn;
		input [256:0] mnemonic;
		reg [5:0] nzimm;
		begin
			nzimm = {rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,%0d", mnemonic, rvfi_rd_addr, $signed(nzimm));
		end
	endtask
	task decode_ci_caddi16sp_insn;
		input [256:0] mnemonic;
		reg [9:0] nzimm;
		begin
			nzimm = {rvfi_insn[12], rvfi_insn[4:3], rvfi_insn[5], rvfi_insn[2], rvfi_insn[6], 4'b0};
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,%0d", mnemonic, rvfi_rd_addr, $signed(nzimm));
		end
	endtask
	task decode_ci_clui_insn;
		input [256:0] mnemonic;
		reg [5:0] nzimm;
		begin
			nzimm = {rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = RD;
			decoded_str = $sformatf("%s\tx%0d,0x%0x", mnemonic, rvfi_rd_addr, sv2v_cast_20($signed(nzimm)));
		end
	endtask
	task decode_ci_cslli_insn;
		input [256:0] mnemonic;
		reg [5:0] shamt;
		begin
			shamt = {rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,0x%0x", mnemonic, rvfi_rd_addr, shamt);
		end
	endtask
	task decode_ciw_insn;
		input [256:0] mnemonic;
		reg [9:0] nzuimm;
		begin
			nzuimm = {rvfi_insn[10:7], rvfi_insn[12:11], rvfi_insn[5], rvfi_insn[6], 2'b00};
			data_accessed = RD;
			decoded_str = $sformatf("%s\tx%0d,x2,%0d", mnemonic, rvfi_rd_addr, nzuimm);
		end
	endtask
	task decode_cb_sr_insn;
		input [256:0] mnemonic;
		reg [5:0] shamt;
		begin
			shamt = {rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,0x%0x", mnemonic, rvfi_rs1_addr, shamt);
		end
	endtask
	task decode_cb_insn;
		input [256:0] mnemonic;
		reg [7:0] imm;
		reg [31:0] jump_target;
		if (((rvfi_insn[15:13] == 3'b110) || (rvfi_insn[15:13] == 3'b111))) begin
			imm = {rvfi_insn[12], rvfi_insn[6:5], rvfi_insn[2], rvfi_insn[11:10], rvfi_insn[4:3]};
			jump_target = (rvfi_pc_rdata + sv2v_cast_32($signed({imm, 1'b0})));
			data_accessed = RS1;
			decoded_str = $sformatf("%s\tx%0d,%0x", mnemonic, rvfi_rs1_addr, jump_target);
		end
		else if ((rvfi_insn[15:13] == 3'b100)) begin
			imm = {{2 {rvfi_insn[12]}}, rvfi_insn[12], rvfi_insn[6:2]};
			data_accessed = (RS1 | RD);
			decoded_str = $sformatf("%s\tx%0d,%0d", mnemonic, rvfi_rd_addr, $signed(imm));
		end
		else begin
			imm = {rvfi_insn[12], rvfi_insn[6:2], 2'b00};
			data_accessed = RS1;
			decoded_str = $sformatf("%s\tx%0d,0x%0x", mnemonic, rvfi_rs1_addr, imm);
		end
	endtask
	task decode_cs_insn;
		input [256:0] mnemonic;
		begin
			data_accessed = ((RS1 | RS2) | RD);
			decoded_str = $sformatf("%s\tx%0d,x%0d", mnemonic, rvfi_rd_addr, rvfi_rs2_addr);
		end
	endtask
	task decode_cj_insn;
		input [256:0] mnemonic;
		begin
			if ((rvfi_insn[15:13] == 3'b001))
				data_accessed = RD;
			decoded_str = $sformatf("%s\t%0x", mnemonic, rvfi_pc_wdata);
		end
	endtask
	task decode_compressed_load_insn;
		input [256:0] mnemonic;
		reg [7:0] imm;
		begin
			if ((rvfi_insn[1:0] == OPCODE_C0))
				imm = {1'b0, rvfi_insn[5], rvfi_insn[12:10], rvfi_insn[6], 2'b00};
			else
				imm = {rvfi_insn[3:2], rvfi_insn[12], rvfi_insn[6:4], 2'b00};
			data_accessed = ((RS1 | RD) | MEM);
			decoded_str = $sformatf("%s\tx%0d,%0d(x%0d)", mnemonic, rvfi_rd_addr, imm, rvfi_rs1_addr);
		end
	endtask
	task decode_compressed_store_insn;
		input [256:0] mnemonic;
		reg [7:0] imm;
		begin
			if ((rvfi_insn[1:0] == OPCODE_C0))
				imm = {1'b0, rvfi_insn[5], rvfi_insn[12:10], rvfi_insn[6], 2'b00};
			else
				imm = {rvfi_insn[8:7], rvfi_insn[12:9], 2'b00};
			data_accessed = ((RS1 | RS2) | MEM);
			decoded_str = $sformatf("%s\tx%0d,%0d(x%0d)", mnemonic, rvfi_rs2_addr, imm, rvfi_rs1_addr);
		end
	endtask
	task decode_load_insn;
		reg [256:0] mnemonic;
		reg [2:0] size;
		begin
			size = rvfi_insn[14:12];
			if ((size == 3'b000))
				mnemonic = "lb";
			else if ((size == 3'b001))
				mnemonic = "lh";
			else if ((size == 3'b010))
				mnemonic = "lw";
			else if ((size == 3'b100))
				mnemonic = "lbu";
			else if ((size == 3'b101))
				mnemonic = "lhu";
			else
				decode_mnemonic("INVALID");
		end
	endtask
	task decode_store_insn;
		reg [256:0] mnemonic;
		case (rvfi_insn[13:12])
			2'b00: mnemonic = "sb";
			2'b01: mnemonic = "sh";
			2'b10: mnemonic = "sw";
			default: decode_mnemonic("INVALID");
		endcase
	endtask
	function [256:0] get_fence_description;
		input [3:0] bits;
		reg [256:0] desc;
		begin
			desc = "";
			if (bits[3])
				desc = {desc, "i"};
			if (bits[2])
				desc = {desc, "o"};
			if (bits[1])
				desc = {desc, "r"};
			if (bits[0])
				desc = {desc, "w"};
			get_fence_description = desc;
		end
	endfunction
	task decode_fence;
		reg [256:0] predecessor;
		reg [256:0] successor;
		begin
			predecessor = get_fence_description(rvfi_insn[27:24]);
			successor = get_fence_description(rvfi_insn[23:20]);
			decoded_str = $sformatf("fence\t%s,%s", predecessor, successor);
		end
	endtask
	always @(posedge clk_i or negedge rst_ni)
		if (!rst_ni)
			cycle <= 0;
		else
			cycle <= (cycle + 1);
	always @(posedge clk_i)
		if (rvfi_valid)
			printbuffer_dumpline;
	always @(*) begin
		decoded_str = "";
		data_accessed = 4'h0;
		insn_is_compressed = 0;
		if ((rvfi_insn[1:0] != 2'b11)) begin
			insn_is_compressed = 1;
			if (((rvfi_insn[15:13] == 3'b100) && (rvfi_insn[1:0] == 2'b10))) begin
				if (rvfi_insn[12]) begin
					if ((rvfi_insn[11:2] == 10'h0))
						decode_mnemonic("c.ebreak");
					else if ((rvfi_insn[6:2] == 5'b0))
						decode_cr_insn("c.jalr");
					else
						decode_cr_insn("c.add");
				end
				else if ((rvfi_insn[6:2] == 5'h0))
					decode_cr_insn("c.jr");
				else
					decode_cr_insn("c.mv");
			end
			else
				casez (rvfi_insn[15:0])
					INSN_CADDI4SPN:
						if ((rvfi_insn[12:2] == 11'h0))
							decode_mnemonic("c.unimp");
						else
							decode_ciw_insn("c.addi4spn");
					INSN_CLW:
						decode_compressed_load_insn("c.lw");
					INSN_CSW:
						decode_compressed_store_insn("c.sw");
					INSN_CADDI:
						decode_ci_caddi_insn("c.addi");
					INSN_CJAL:
						decode_cj_insn("c.jal");
					INSN_CJ:
						decode_cj_insn("c.j");
					INSN_CLI:
						decode_ci_cli_insn("c.li");
					INSN_CLUI:
						if ((rvfi_insn[11:7] == 5'd2))
							decode_ci_caddi16sp_insn("c.addi16sp");
						else
							decode_ci_clui_insn("c.lui");
					INSN_CSRLI:
						decode_cb_sr_insn("c.srli");
					INSN_CSRAI:
						decode_cb_sr_insn("c.srai");
					INSN_CANDI:
						decode_cb_insn("c.andi");
					INSN_CSUB:
						decode_cs_insn("c.sub");
					INSN_CXOR:
						decode_cs_insn("c.xor");
					INSN_COR:
						decode_cs_insn("c.or");
					INSN_CAND:
						decode_cs_insn("c.and");
					INSN_CBEQZ:
						decode_cb_insn("c.beqz");
					INSN_CBNEZ:
						decode_cb_insn("c.bnez");
					INSN_CSLLI:
						decode_ci_cslli_insn("c.slli");
					INSN_CLWSP:
						decode_compressed_load_insn("c.lwsp");
					INSN_SWSP:
						decode_compressed_store_insn("c.swsp");
					default: decode_mnemonic("INVALID");
				endcase
		end
		else
			casez (rvfi_insn)
				INSN_LUI:
					decode_u_insn("lui");
				INSN_AUIPC:
					decode_u_insn("auipc");
				INSN_JAL:
					decode_j_insn("jal");
				INSN_JALR:
					decode_i_jalr_insn("jalr");
				INSN_BEQ:
					decode_b_insn("beq");
				INSN_BNE:
					decode_b_insn("bne");
				INSN_BLT:
					decode_b_insn("blt");
				INSN_BGE:
					decode_b_insn("bge");
				INSN_BLTU:
					decode_b_insn("bltu");
				INSN_BGEU:
					decode_b_insn("bgeu");
				INSN_ADDI:
					if ((rvfi_insn == 32'h00_00_00_13))
						decode_i_insn("addi");
					else
						decode_i_insn("addi");
				INSN_SLTI:
					decode_i_insn("slti");
				INSN_SLTIU:
					decode_i_insn("sltiu");
				INSN_XORI:
					decode_i_insn("xori");
				INSN_ORI:
					decode_i_insn("ori");
				INSN_ANDI:
					decode_i_insn("andi");
				INSN_SLLI:
					decode_i_shift_insn("slli");
				INSN_SRLI:
					decode_i_shift_insn("srli");
				INSN_SRAI:
					decode_i_shift_insn("srai");
				INSN_ADD:
					decode_r_insn("add");
				INSN_SUB:
					decode_r_insn("sub");
				INSN_SLL:
					decode_r_insn("sll");
				INSN_SLT:
					decode_r_insn("slt");
				INSN_SLTU:
					decode_r_insn("sltu");
				INSN_XOR:
					decode_r_insn("xor");
				INSN_SRL:
					decode_r_insn("srl");
				INSN_SRA:
					decode_r_insn("sra");
				INSN_OR:
					decode_r_insn("or");
				INSN_AND:
					decode_r_insn("and");
				INSN_CSRRW:
					decode_csr_insn("csrrw");
				INSN_CSRRS:
					decode_csr_insn("csrrs");
				INSN_CSRRC:
					decode_csr_insn("csrrc");
				INSN_CSRRWI:
					decode_csr_insn("csrrwi");
				INSN_CSRRSI:
					decode_csr_insn("csrrsi");
				INSN_CSRRCI:
					decode_csr_insn("csrrci");
				INSN_ECALL:
					decode_mnemonic("ecall");
				INSN_EBREAK:
					decode_mnemonic("ebreak");
				INSN_MRET:
					decode_mnemonic("mret");
				INSN_DRET:
					decode_mnemonic("dret");
				INSN_WFI:
					decode_mnemonic("wfi");
				INSN_PMUL:
					decode_r_insn("mul");
				INSN_PMUH:
					decode_r_insn("mulh");
				INSN_PMULHSU:
					decode_r_insn("mulhsu");
				INSN_PMULHU:
					decode_r_insn("mulhu");
				INSN_DIV:
					decode_r_insn("div");
				INSN_DIVU:
					decode_r_insn("divu");
				INSN_REM:
					decode_r_insn("rem");
				INSN_REMU:
					decode_r_insn("remu");
				INSN_LOAD:
					decode_load_insn;
				INSN_STORE:
					decode_store_insn;
				INSN_FENCE:
					decode_fence;
				INSN_FENCEI:
					decode_mnemonic("fence.i");
				default: decode_mnemonic("INVALID");
			endcase
	end
	function [19:0] sv2v_cast_20;
		input [19:0] inp;
		sv2v_cast_20 = inp;
	endfunction
	function [31:0] sv2v_cast_32;
		input [31:0] inp;
		sv2v_cast_32 = inp;
	endfunction
endmodule
