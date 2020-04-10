import sys, os
from argparse import ArgumentParser
from datetime import datetime as dt
from collections import OrderedDict as ODict
import pprint as pp
from decimal import Decimal


# Importing necessary helper functions
from helper import printTable, figlet_print, center_print, print_info, \
        print_newline, parse_cmdline_options, fatal_error, memory_usage, \
        goldmine_logger
# Importing Configuration file parsing function
from configuration import set_config_file_path, current_path, make_directory, change_directory, \
        summarize_report, remove_directory
# Importing Verilog parsing function
from verilog import parse_verilog, get_modules, get_top_modules, get_ports, getDefUseTarget, rank, \
        get_params, analyze_pagerank
from static_analysis import CDFG, Linking, process_targets, plot_digraphs, plot_digraph,\
        get_targets_of_manual_assertions
from static_analysis import cone_of_influence as COI
# Importing Simulation function
from simulation import simulate, parse, write_csv, summary_report
#Importing mining function from miner, and analyze_manual_assertions
from assertion_miner.miner import miner, analyze_manual_assertions


if __name__ == "__main__":

    #css()

    parser = ArgumentParser()

    parser.add_argument("-a", "--aggregate", action="store_true",
                      help="Aggregate rankings for assertion importance, complexity, coverage and complexity",
                      dest="aggregate")
    parser.add_argument("-m", "--module", help="Top module of the design", dest="top", required=True)
    # NOTE: Changing required=True. If no clock name supplied, a default clock with posedge would \
    #       be assumed by GoldMine.
    parser.add_argument("-c", "--clock", help="Clock signal", dest="clock", default='DEFAULT_CLOCK:1')
    # NOTE: Changing required=True. If no reset name supplied, a default clock with posedge would \
    #       be assumed by GoldMine.
    parser.add_argument("-r", "--reset", help="Reset signal", dest="reset", default='DEFAULT_RESET:1')
    parser.add_argument("-p", "--parse", action="store_true", \
                      help="Parse the verilog file(s) and exit", dest="parse")
    parser.add_argument("-e", "--engine", help="Assertion mining engine", dest="engine", default='')
    parser.add_argument("-u", "--configuration_file_loc", help="GoldMine configuration file \
                      location", dest="config_loc", required=True)
    parser.add_argument("-v", "--vcd", help="VCD File(s)", dest="vcd", default='')
    parser.add_argument("-t", "--targets", help="Target variables seperated by comma \
                      for assertions mining", dest="targetv")
    parser.add_argument("-T", "--target_vectors", action="store_true", \
                      help="Target vector variables", default=False, dest="vectorf")
    parser.add_argument("-I", "--include", dest="include", action="append", \
                        default=[], help="Include Path")
    parser.add_argument("-V", "--verification", action="store_false", \
                      help="Specify to skip formal verification", dest="verif")
    parser.add_argument("-S", "--static_dump", action="store_true",\
                      help="Specify to dump static analysis info and graphics and exit", dest="staticgraph")
    parser.add_argument("-N", "--inter_modular", action="store_true",\
                      help="Specify to mine inter modular assertions (significantly slow)", dest="intermodular")
    parser.add_argument("-M", "--manual_assertion", help="File containing user specified assertions", \
            dest="man_assertion_file", default='')

    # Specifying mutually exclusive command line options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--files", help="Location containing source Verilog files", dest="file_loc")
    group.add_argument("-F", "--file_list", help="A file containing name of verilog files with absolute path \
                        , one file in every line" , dest="lfile")

    Resource_Stat = ODict()

    work_directory_path = current_path() + '/goldmine.out'
    make_directory(work_directory_path)
    
    logname = work_directory_path + '/goldmine.log'
    glogger = goldmine_logger('goldmine', logname)

    args = parser.parse_args()
   
    figlet_print('GoldMine')
    
    # If no options are given, check the system sanity, print options and then exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)
    
    # Parse Command Line Options
    CMD_LINE_OPTIONS = parse_cmdline_options(args)
    # pp.pprint(CMD_LINE_OPTIONS)

    # Parse GoldMine Config File
    CONFIG = set_config_file_path(CMD_LINE_OPTIONS['CFG'], CMD_LINE_OPTIONS['VCD'] != '', \
            CMD_LINE_OPTIONS['CLK'].keys()[0] == 'DEFAULT_CLOCK')
    # pp.pprint(CONFIG)

    center_print('Mining for design: ' + CMD_LINE_OPTIONS['TOP'])

    
    # Noting the time when the tool actually starts working, starting from simulation
    start_time = dt.now()
    
    figlet_print('Parsing')
    
    # PARSING DONE
    vparse_start_time = dt.now()
    
    # Info storage dictionary
    PARSE_INFO = {}
    ModuleDefs = []
    ModuleInstances = {}

    for vfile in CMD_LINE_OPTIONS['VFILES']:
        fname = vfile[vfile.rfind('/') + 1:-2] 
        PARSE_INFO[fname] = {}
        print('Parsing: ' + fname + '.v' + '.' * 3)
        ast, directives, preprocessed_code = parse_verilog([vfile], \
                CMD_LINE_OPTIONS['INCLUDE'], [])
        # GET MODULE NAMES
        ModuleDefs_ = {}
        get_modules(ast, ModuleDefs_, ModuleInstances)
        if not ModuleDefs_.keys():
            fatal_error('No module definition found in the source verilog file(s)')
        ModuleDefs = ModuleDefs + ModuleDefs_.keys()
        
        PARSE_INFO[fname]['directives'] = directives
        PARSE_INFO[fname]['pcode'] = preprocessed_code
        PARSE_INFO[fname]['moduledefs'] = ModuleDefs_

        del ModuleDefs_
    
    '''    
    tmp_file = open('code.v', 'w')
    tmp_file.write(PARSE_INFO[PARSE_INFO.keys()[0]]['pcode'])
    tmp_file.close()
    '''
    
    undefined_modules = list(set(ModuleInstances.keys()) - set(ModuleDefs))
    if undefined_modules:
        fatal_error('Please include definitions for the following modules: ' + \
                ', '.join(undefined_modules))
    
    # CONFIRM TOP MODULE EXISTS IN THE AST
    #Top_Modules = get_top_modules(ModuleInstances)
    #top_module = ''
    #if not Top_Modules:
    #    fatal_error('No top module found')
    if CMD_LINE_OPTIONS['TOP'] in ModuleDefs:
        top_module = CMD_LINE_OPTIONS['TOP']
    else:
        fatal_error('Specified top module not found in parse tree. Exiting..')

    print_newline()

    figlet_print('Elaborating')

    # STORE CLOCKS, AND RESETS FROM COMMAND LINE SPECIFICATION. 
    # AUTOMATED CLOCK AND RESET IDENTIFICATION
    # NOT ENABLED AT THIS POINT OF TIME. THIS IS A TODO
    clks = CMD_LINE_OPTIONS['CLK']
    rsts = CMD_LINE_OPTIONS['RST']

    # CAPTURE THE MAXIMUM TEMPORAL LENGTH ALLOWED FOR AN ASSERTION
    temporal_depth = CONFIG['num_cycles']

    
    ELABORATE_INFO = {}
    
    for fname in PARSE_INFO.keys():
        moduledefs = PARSE_INFO[fname]['moduledefs']
        # Ports: Dictionary where Key := Port Type, Val := Corresponding port name
        for moduledef in moduledefs.keys():
            print('Elaborating: ' + moduledef)
            
            ELABORATE_INFO[moduledef] = {}
            
            ast = moduledefs[moduledef]
            Params = get_params(ast, moduledef)
            Ports =  get_ports(ast, moduledef, Params)
            def_vars, use_vars, targets = getDefUseTarget(Ports)
            var_def_chain, var_use_chain, PathSets, dep_g, CDFGS, fused_INFO, MODINSTS = CDFG(ast, \
                    clks, Params, Ports)

            #if moduledef == 'ibex_id_stage':
            #    ast.show()

            ELABORATE_INFO[moduledef]['params'] = Params
            ELABORATE_INFO[moduledef]['ports'] = Ports
            ELABORATE_INFO[moduledef]['targets'] = targets
            ELABORATE_INFO[moduledef]['var_def_chain'] = var_def_chain
            ELABORATE_INFO[moduledef]['var_use_chain'] = var_use_chain
            ELABORATE_INFO[moduledef]['PathSets'] = PathSets
            ELABORATE_INFO[moduledef]['dep_g'] = dep_g
            ELABORATE_INFO[moduledef]['CDFGS'] = CDFGS
            ELABORATE_INFO[moduledef]['fused_INFO'] = fused_INFO
            ELABORATE_INFO[moduledef]['MODINSTS'] = MODINSTS

            del Params
            del Ports
            del targets
            del var_def_chain
            del var_use_chain
            del PathSets
            del dep_g
            del CDFGS
            del fused_INFO
            del MODINSTS

    figlet_print('Linking')
    # During linking we connect the different modules in a depth first
    # manner. At the same time we create a scope_module_map that stores the
    # scope of an instantiated module as the key and the value of the key is the 
    # module to which the scope refers to. This is important during recursive COI calculation
    # at the next step.
    complete_dep_g, complete_fused_CDFG, scope_module_map = Linking(ELABORATE_INFO, top_module)

    figlet_print('C Ranking')
    
    if CMD_LINE_OPTIONS['TARGETS']:
        targets = CMD_LINE_OPTIONS['TARGETS']
    else:
        targets = ELABORATE_INFO[top_module]['targets']
    complete_pagerank = analyze_pagerank(complete_dep_g)
    complete_cones = COI(targets, ELABORATE_INFO, complete_dep_g, \
            complete_pagerank, temporal_depth, top_module, scope_module_map) 
    
    target_cones = process_targets(complete_cones, top_module, ELABORATE_INFO, scope_module_map)
    
    vparse_end_time = dt.now()
    
    print_newline()
    ######################
    mem_usage = memory_usage(os.getpid())
    print_info('Total time for parsing, ranking: ' + str(vparse_end_time - vparse_start_time))
    print_info('Peak Memory Usage for parsing, ranking: ' + str(round(Decimal(mem_usage / 1048576), 2)) + ' MB')
    Resource_Stat['V Parse & Ranking'] = [str(vparse_end_time - vparse_start_time), \
            str(round(Decimal(mem_usage / 1048576), 2))]
    ######################

    change_directory(work_directory_path)

    #PageRank, graph, var_def_chain, var_use_chain = rank(ast, def_vars, use_vars)

    make_directory(top_module)
    change_directory(top_module)
    
    preprocessed_code_loc = current_path() + '/preprocessed_code'
    make_directory(preprocessed_code_loc)
    for fname in PARSE_INFO.keys():
        ph = open(preprocessed_code_loc + '/' + fname + '_preprocessed_code.v', 'w')
        ph.write(PARSE_INFO[fname]['pcode'])
        ph.close()
    
    if CMD_LINE_OPTIONS['STATICGRAPH']:
        figlet_print('Saving')
        static_dir = current_path() + '/static'
        make_directory(static_dir)
        for t_module in ELABORATE_INFO.keys():
            print('Saving static analysis info for: ' + t_module)
            # Dump all static analysis reports in the static directory

            dep_g = ELABORATE_INFO[t_module]['dep_g']
            dep_dir = static_dir + '/dep'
            #remove_directory(dep_dir)
            make_directory(dep_dir)
            dep_file = dep_dir + '/' + t_module + '.dep'
            dep_handle = open(dep_file, 'w')
            edge_info = dep_g.edges(data='weight')
            econtent = [i[0] + '\t' + i[1] + '\t' + str(i[2]) for i in edge_info]
            dep_handle.write('\n'.join(econtent))
            dep_handle.close()
            dep_summary = dep_dir + '/' + t_module + '.summary'
            dep_summ_handle = open(dep_summary, 'w')
            dep_summ_handle.write(
                    'Total number of nodes in the variable dependency graph: ' \
                            + str(len(dep_g.nodes())) + '\n' \
                    'Total number of edges in the variable dependency graph: ' \
                            + str(len(dep_g.edges()))
                            )
            dep_summ_handle.close()
            vdg_dir_name =  static_dir + '/var_dep_graph'
            #remove_directory(vdg_dir_name)
            make_directory(vdg_dir_name)
            plot_digraph([dep_g], vdg_dir_name, [t_module])
            
            CDFGS = ELABORATE_INFO[t_module]['CDFGS']
            cdfg_dir_name = static_dir + '/cdfg/' + t_module
            #remove_directory(cdfg_dir_name)
            make_directory(cdfg_dir_name)
            plot_digraphs(CDFGS, cdfg_dir_name)
            fused_CDFG = ELABORATE_INFO[t_module]['fused_INFO'][0]
            plot_digraph([fused_CDFG], cdfg_dir_name, [t_module])
        

            var_def_chain = ELABORATE_INFO[t_module]['var_def_chain']
            def_dir = static_dir + '/def'
            #remove_directory(def_dir)
            make_directory(def_dir)
            def_file = def_dir + '/' + t_module + '.def'
            def_handle = open(def_file, 'w')
            pp.pprint(var_def_chain, def_handle)
            def_handle.close()
 
            var_use_chain = ELABORATE_INFO[t_module]['var_use_chain']
            use_dir = static_dir + '/use'
            #remove_directory(use_dir)
            make_directory(use_dir)
            use_file = use_dir + '/' + t_module + '.use'
            use_handle = open(use_file, 'w')
            pp.pprint(var_use_chain, use_handle)
            use_handle.close()

            PathSets = ELABORATE_INFO[t_module]['PathSets']
            path_dir = static_dir + '/path'
            #remove_directory(path_dir)
            make_directory(path_dir)
            path_file = path_dir + '/' + t_module + '.path'
            path_handle = open(path_file, 'w')
            pcontent = []
            for i in range(len(PathSets)):
                paths = PathSets[i]
                for path in paths:
                    pcontent.append('-->'.join(path))
            path_handle.write('\n'.join(pcontent))
            del pcontent
            #pp.pprint(PathSets, path_handle)
            path_handle.close()
        
            '''
            PageRankO =  ODict(sorted(PageRank.items(), key=lambda t: t[1], reverse=True))
            rank_file = current_path() + '/static/' + top_module + '.rank'
            content = printTable(PageRankO, ['Variable', 'Rank']) 
            rfile = open(rank_file, 'w')
            rfile.write(content)
            rfile.close()
            '''
        print_newline()

        print('Saving static analysis info for complete: ' + top_module)

        complete_dep_file = static_dir + '/complete_dep_g.dep' 
        complete_dep_handle = open(complete_dep_file, 'w')
        edge_info = complete_dep_g.edges(data='weight')
        econtent = [i[0] + '\t' + i[1] + '\t' + str(i[2]) for i in edge_info]
        complete_dep_handle.write('\n'.join(econtent))
        complete_dep_handle.close()
        complete_dep_summary = static_dir + '/complete_dep_g.summary'
        complete_dep_summ_handle = open(complete_dep_summary, 'w')
        complete_dep_summ_handle.write(
                'Total number of nodes in the variable dependency graph: ' \
                        + str(len(complete_dep_g.nodes())) + '\n' \
                'Total number of edges in the variable dependency graph: ' \
                        + str(len(complete_dep_g.edges()))
                        )
        complete_dep_summ_handle.close()

        complete_fused_CDFG_file = static_dir + '/complete_fused_CDFG.dep' 
        complete_fused_CDFG_handle = open(complete_fused_CDFG_file, 'w')
        edge_info = complete_fused_CDFG.edges()
        econtent = [i[0] + '\t' + i[1] for i in edge_info]
        complete_fused_CDFG_handle.write('\n'.join(econtent))
        complete_fused_CDFG_handle.close()
        complete_fused_CDFG_summary = static_dir + '/complete_fused_CDFG.summary'
        complete_fused_CDFG_summ_handle = open(complete_fused_CDFG_summary, 'w')
        complete_fused_CDFG_summ_handle.write(
                'Total number of nodes in the fused CDFG graph: ' \
                        + str(len(complete_fused_CDFG.nodes())) + '\n' \
                'Total number of edges in the variable dependency graph: ' \
                        + str(len(complete_fused_CDFG.edges()))
                        )
        complete_fused_CDFG_summ_handle.close()

        PageRankO = ODict(sorted(complete_pagerank.items(), key=lambda t: t[1], reverse=True))
        rank_file = static_dir + '/complete_pagerank.rank'
        content = printTable(PageRankO, ['Variable', 'Rank'])
        rfile = open(rank_file, 'w')
        rfile.write(content)
        rfile.close()

        cone_dir_name = static_dir + '/cone'
        remove_directory(cone_dir_name)
        make_directory(cone_dir_name)
        for key in complete_cones.keys():
            print('Saving cone for the target variable: ' + key)
            plot_digraph([complete_cones[key]], cone_dir_name, [key])

        plot_digraph([complete_dep_g], static_dir, [top_module])
        plot_digraph([complete_fused_CDFG], static_dir, [top_module + '_fused_CDFG'])


    figlet_print('Data Gen')

    vcd_file_path = CMD_LINE_OPTIONS['VCD'] if CMD_LINE_OPTIONS['VCD'] \
            else current_path() + '/' + top_module + '.vcd'
   

    if CMD_LINE_OPTIONS['MAN_ASSERTIONS']:
        # Assertion_dict is a dictionary where the key is the target of the specified assertions
        # and the value is a list containing all the assertions specified for that target variable
        mtargets = get_targets_of_manual_assertions(CMD_LINE_OPTIONS['MAN_ASSERTIONS'])
        targets = mtargets.keys()
        for target in targets:
            analyze_manual_assertions(target_cones[target], target, CONFIG, top_module, clks, rsts, \
                CMD_LINE_OPTIONS['VFILES'], CMD_LINE_OPTIONS['INCLUDE'], cones[target], \
                CMD_LINE_OPTIONS['AGGREGATE'], CMD_LINE_OPTIONS['VERIF'], mtargets[target], 'manual')
    
        end_time = dt.now()
        print_newline()
        print_info('Total Run Time: ' + str(end_time - start_time))
        exit(0)
    
    simulation_start_time = dt.now()

    if not CMD_LINE_OPTIONS['VCD']:
        # Iverilog get precedence over VCS
        if CONFIG['iverilog']:
            simulate(top_module, clks, rsts, CMD_LINE_OPTIONS['VFILES'], \
                    CMD_LINE_OPTIONS['INCLUDE'], CONFIG['max_sim_cycles'], 'iverilog', CONFIG, ELABORATE_INFO[top_module]['ports'])
        else:
            simulate(top_module, clks, rsts, CMD_LINE_OPTIONS['VFILES'], \
                    CMD_LINE_OPTIONS['INCLUDE'], CONFIG['max_sim_cycles'], 'vcs', CONFIG, ELABORATE_INFO[top_module]['ports'])
    
    simulation_end_time = dt.now()
    mem_usage = memory_usage(os.getpid())
    Resource_Stat['Simulation'] = [str(simulation_end_time - simulation_start_time), \
            str(round(Decimal(mem_usage / 1048576), 2))]
    
    # Either via Simulation or via Supplied VCD we have trace. Now its time to parse it 
    figlet_print('D Parse')
    vcdparse_start_time = dt.now() 
    # rows_ will be a Pandas DataFrame which has all the variables and its time stampped values upto
    # temporal_depth
    rows_, num_rows_, rows_invalid_type = parse(vcd_file_path, top_module, clks, \
            temporal_depth, ELABORATE_INFO, scope_module_map, CMD_LINE_OPTIONS['INTERMODULAR'])
    vcdparse_end_time = dt.now()
    mem_usage = memory_usage(os.getpid())
    
    summary_report(rows_invalid_type)
    print_info('Total time to parse VCD file: ' + str(vcdparse_end_time - vcdparse_start_time))
    Resource_Stat['D Parse'] = [str(vcdparse_end_time - vcdparse_start_time), \
            str(round(Decimal(mem_usage / 1048576), 2))]
    write_csv(rows_, top_module, '')

    # Time To Mine
    figlet_print('Mining')
    
    #tf = {'gnt1':['req1','req2','state','[1]req1','[1]req2','[1]state'],
    #      'gnt2':['req1','req2','state','[1]req1','[1]req2','[1]state']
    #      }

    targets = target_cones.keys()
    
    engine = CMD_LINE_OPTIONS['MENGINE'] if CMD_LINE_OPTIONS['MENGINE'] else CONFIG['engine']
    
    mined_assertion = []

    print_info('Engine used for mining: ' + engine)

    mine_start_time = dt.now()
    
    for target in targets:
        print_newline()
        center_print('Mining for target :--> ' + target)
        miner(target_cones[target], target, rows_, rows_invalid_type, CONFIG, top_module, \
                    clks, rsts, CMD_LINE_OPTIONS['VFILES'], CMD_LINE_OPTIONS['INCLUDE'], \
                    complete_cones[target], CMD_LINE_OPTIONS['AGGREGATE'], CMD_LINE_OPTIONS['VERIF'], engine)
    # Time to Verify
    mine_end_time = dt.now()
    mem_usage = memory_usage(os.getpid())

    print_info('Total time to mine: ' + str(mine_end_time - mine_start_time))
    Resource_Stat['Mining'] = [str(mine_end_time - mine_start_time), \
            str(round(Decimal(mem_usage / 1048576), 2))]

    # Noting the time when the tool actually stops working, ending at dumping all results
    end_time = dt.now()
    mem_usage = memory_usage(os.getpid())

    print_newline()
    print_info('Total Run Time: ' + str(end_time - start_time))

    Resource_Stat['Overall'] = [str(end_time - start_time), str(round(Decimal(mem_usage / 1048576), 2))]

    summarize_report(top_module, targets, Resource_Stat, engine)
