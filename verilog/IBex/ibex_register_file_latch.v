module ibex_register_file (
	clk_i,
	rst_ni,
	test_en_i,
	raddr_a_i,
	rdata_a_o,
	raddr_b_i,
	rdata_b_o,
	waddr_a_i,
	wdata_a_i,
	we_a_i
);
	parameter RV32E = 0;
	parameter [31:0] DataWidth = 32;
	input wire clk_i;
	input wire rst_ni;
	input wire test_en_i;
	input wire [4:0] raddr_a_i;
	output wire [(DataWidth - 1):0] rdata_a_o;
	input wire [4:0] raddr_b_i;
	output wire [(DataWidth - 1):0] rdata_b_o;
	input wire [4:0] waddr_a_i;
	input wire [(DataWidth - 1):0] wdata_a_i;
	input wire we_a_i;
	localparam [31:0] ADDR_WIDTH = (RV32E ? 4 : 5);
	localparam [31:0] NUM_WORDS = (2 ** ADDR_WIDTH);
	reg [(DataWidth - 1):0] mem [0:(NUM_WORDS - 1)];
	reg [(NUM_WORDS - 1):1] waddr_onehot_a;
	wire [(NUM_WORDS - 1):1] mem_clocks;
	reg [(DataWidth - 1):0] wdata_a_q;
	wire [(ADDR_WIDTH - 1):0] raddr_a_int;
	wire [(ADDR_WIDTH - 1):0] raddr_b_int;
	wire [(ADDR_WIDTH - 1):0] waddr_a_int;
	assign raddr_a_int = raddr_a_i[(ADDR_WIDTH - 1):0];
	assign raddr_b_int = raddr_b_i[(ADDR_WIDTH - 1):0];
	assign waddr_a_int = waddr_a_i[(ADDR_WIDTH - 1):0];
	wire clk_int;
	assign rdata_a_o = mem[raddr_a_int];
	assign rdata_b_o = mem[raddr_b_int];
	prim_clock_gating cg_we_global(
		.clk_i(clk_i),
		.en_i(we_a_i),
		.test_en_i(test_en_i),
		.clk_o(clk_int)
	);
	always @(posedge clk_int or negedge rst_ni) begin : sample_wdata
		if (!rst_ni)
			wdata_a_q <= 1'sb0;
		else if (we_a_i)
			wdata_a_q <= wdata_a_i;
	end
	always @(*) begin : wad
		begin : sv2v_autoblock_6
			reg signed [31:0] i;
			for (i = 1; (i < NUM_WORDS); i = (i + 1))
				begin : wad_word_iter
					if ((we_a_i && (waddr_a_int == i)))
						waddr_onehot_a[i] = 1'b1;
					else
						waddr_onehot_a[i] = 1'b0;
				end
		end
	end
	generate
		genvar gen_cg_word_iter_x;
		for (gen_cg_word_iter_x = 1; (gen_cg_word_iter_x < NUM_WORDS); gen_cg_word_iter_x = (gen_cg_word_iter_x + 1)) begin : gen_cg_word_iter
			prim_clock_gating cg_i(
				.clk_i(clk_int),
				.en_i(waddr_onehot_a[gen_cg_word_iter_x]),
				.test_en_i(test_en_i),
				.clk_o(mem_clocks[gen_cg_word_iter_x])
			);
		end
	endgenerate
	always @(*) begin : latch_wdata
		mem[0] = 1'sb0;
		begin : sv2v_autoblock_7
			reg signed [31:0] k;
			for (k = 1; (k < NUM_WORDS); k = (k + 1))
				begin : latch_wdata_word_iter
					if (mem_clocks[k])
						mem[k] = wdata_a_q;
				end
		end
	end
endmodule
