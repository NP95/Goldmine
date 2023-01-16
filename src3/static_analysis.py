import networkx as nx
from networkx.drawing.nx_agraph import *
import numpy as np
import pprint as pp
import itertools as itools
import regex as re
import multiprocessing as mps
import pygraphviz as pgv


from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

NUMBER_OF_PROCESSES = mps.cpu_count()

from verilog import get_rhs_cond_nodes, get_comp_nodes, get_lvalue, get_rhs_constants, analyze_pagerank, \
        get_ports
from configuration import current_path, remove_directory, make_directory
from helper import exec_command, print_warning
from formal_verifier import worker

#### This Node Type Dictionary is for the Graph
Type = {'IfStatement': 'IF',
        'CaseStatement': 'CS',
        'CasexStatement': 'CX',
        'Case': 'CA',
        'Block': 'BL',
        'NonblockingSubstitution': 'NS',
        'BlockingSubstitution': 'BS',
        'Assign': 'AS',
        'Always': 'AL',
        'SingleStatement': 'SS',
        'EventStatement':'ES'
        }

FillColor = {
        'IfStatement': 'springgreen',
        'CaseStatement': 'linen',
        'CasexStatement': 'lightgray',
        'Case': 'lightcyan',
        'Block': 'turquoise',
        'NonblockingSubstitution': 'firebrick',
        'BlockingSubstitution': 'cadetblue',
        'Assign': 'deepskyblue',
        'Always': 'gold',
        'SingleStatement': 'aquamarine',
        'EventStatement': 'azure',
        'Default': 'white'
        }

def generate_code(ast):
    
    codegen = ASTCodeGenerator()
    code = codegen.visit(ast)
    return code


def fill_color(typ):
    try:
        return FillColor[typ]
    except KeyError:
        return FillColor['Default']


def get_port_type(module_name, mod_inst_chains):

    mports = [] 
    mtyps = []

    for mod_inst_chain in mod_inst_chains:
        root_node = get_root_node(mod_inst_chain)[0]
        if root_node == module_name:
            mports = mod_inst_chain.node[root_node]['port']
            mtyps = mod_inst_chain.node[root_node]['typ']
            break

    return mports, mtyps

def construct_Mod_Inst_Chain(ast, mod_inst_chains):

    if (ast.__class__.__name__ == 'ModuleDef'):
        ModuleGraph = nx.DiGraph()

        port = []
        typ = []

        node_name = ast.name
        
        ports = get_ports(ast, node_name)

        for key in list(ports.keys()):
            port.extend(ports[key])
            if key == 'IPort':
                typ_ = ['inp'] * len(ports[key])
                typ.extend(typ_)
                del typ_
            elif key == 'OPort':
                typ_ = ['oup'] * len(ports[key])
                typ.extend(typ_)
                del typ_
    
        print(node_name)
        #print port
        #print typ
        
        ModuleGraph.add_node(node_name, ast=ast, \
                                        port=port, \
                                        typ=typ)

        mod_inst_chains.append(ModuleGraph)

    for c in ast.children():
        construct_Mod_Inst_Chain(c, mod_inst_chains)

    return

        
def add_nodes_Mod_Inst_Chain(ast, mod_inst_chain):
    
    NodeQueue = mod_inst_chain.nodes()
    top_node = NodeQueue[0]

    while NodeQueue:
        p_node_name = NodeQueue.pop()
        p_node_ast = mod_inst_chain.node[p_node_name]['ast']
        if (p_node_ast.__class__.__name__ == 'Instance'):
            portname = []
            argname = []
            
            inst_node_name = p_node_ast.name
            inst_module_name = p_node_ast.module
            print('Instance name: ' + inst_node_name)

            portlist = p_node_ast.portlist
            
            for port in portlist:
                portname_ = port.portname
                argname_ = []
                get_rhs_cond_nodes(port.argname, argname_)
                portname.append(portname_)
                argname.append(argname_)
            
            mod_inst_chain.add_node(inst_node_name, module_name=inst_module_name,\
                                                    portname=portname, \
                                                    argname=argname)
            mod_inst_chain.add_edge(top_node, inst_node_name)
            
            #print inst_node_name
            #print portname
            #print argname
            #print '\n' * 2

        for c in p_node_ast.children():
            try:
                node_name = str(c.lineno) + ':' + c.name
            except AttributeError:
                node_name = str(c.lineno) + ':' + c.__class__.__name__
            NodeQueue.append(node_name)

            mod_inst_chain.add_node(node_name, ast=c)
    
    nodes = mod_inst_chain.nodes()
    # Cleanup all the nodes that are not related via Module_Instantiation relationship
    for node in nodes:
        if mod_inst_chain.in_degree(node) == 0 and \
           mod_inst_chain.out_degree(node) == 0 and \
           node != top_node:
            mod_inst_chain.remove_node(node)
    
    #print 'Final nodes: ' + str(mod_inst_chain.nodes())
    return mod_inst_chain


def construct_CDFG(ast, CDFGS, MODINSTS, clks, indent):
    # ast: returned by the PyVerilog Parser after parsing the Verilog Files(s)
    
    if (ast.__class__.__name__ == 'Always'):
        ALGraph = nx.DiGraph()
        typ = ast.__class__.__name__
        node_name = str(ast.lineno) + ':' + Type[typ]

        sens_list = []
        get_rhs_cond_nodes(ast.sens_list, sens_list)
        clk_name = list(clks.keys())[0]
        
        ALGraph.add_node(node_name, typ=typ, \
                                    sens=sens_list, \
                                    clk_sens=True if clk_name in sens_list else False, \
                                    statements=[], \
                                    fillcolor=fill_color(typ), \
                                    style='filled', \
                                    ast=ast, \
                                    use_var=[], \
                                    label=node_name)
        CDFGS.append(ALGraph)

    elif (ast.__class__.__name__ == 'Assign'):
        ASGraph = nx.DiGraph()
        typ = ast.__class__.__name__
        def_var = get_lvalue(ast.left)
        node_name = str(ast.lineno) + ':' + Type[typ]
        ASGraph.add_node(node_name, typ='Assign', \
                                    statements=[], \
                                    ast=ast, \
                                    fillcolor=fill_color(typ), \
                                    style='filled', \
                                    use_var=[], \
                                    def_var=[], \
                                    label=node_name + '\n' + generate_code(ast.left) + ' = ' + \
                                    generate_code(ast.right) + ';'
                                    )
    

        CDFGS.append(ASGraph)

    elif (ast.__class__.__name__ == 'Instance'):
        instance_name = ast.name
        module_name = ast.module

        portmap = {}
        portlist = ast.portlist
        for port in portlist:
            # portname is an attribute and usally a name of the port. Hence it is a string
            # On the other hand, argname, can be a concatenation of ports of the instantiated modules
            # hence, it is an Identifier class that has to be parsed for all formal argument port
            # names.
            pname = port.portname
            aname = []
            get_rhs_cond_nodes(port.argname, aname) 
            #print(pname + ' ' + ', '.join(aname))
            portmap[pname] = aname
        
        MODINSTS[instance_name] = [module_name, portmap]

    for c in ast.children():
        #print '-' * indent + ': ' + c.__class__.__name__ + ' ' + str(c.lineno)
        construct_CDFG(c, CDFGS, MODINSTS, clks, indent + 2)
    

    return

def add_nodes_to_CDFG(ast, CDFG):
    
    NodeQueue = list(CDFG.nodes())
    
    while NodeQueue:
        p_node_name = NodeQueue.pop()
        p_node_ast = CDFG.nodes[p_node_name]['ast']
        if (p_node_ast.__class__.__name__ == 'Always'):
            '''
            for c in p_node_ast.children():
                if (c.__class__.__name__ == 'IfStatement'):
                    c_node_name = str(c.lineno)
                    NodeQueue.append(c_node_name)
                    CDFG.add_node(c_node_name, typ='IfStatement', \
                                               statements=[], \
                                               ast=c)
                    CDFG.add_edge(p_node_name, c_node_name, cond=[])

                elif (c.__class__.__name__ == 'BlockingSubstitution' or
                      c.__class__.__name__ == 'NonblockingSubstitution'):
                    CDFG.node[p_node_name]['statements'].append(c)

                elif (c.__class__.__name__ == 'CaseStatement' or
                      c.__class__.__name__ == 'CaseXStatement'):
                    c_node_name = str(c.lineno)
                    NodeQueue.append(c_node_name)
                    CDFG.add_node(c_node_name, typ='CaseStatement', \
                                               statements=[], \
                                               ast=c)
                    CDFG.add_edge(p_node_name, c_node_name, cond=[])
                # Consider Block
            '''
            stmt_ast = p_node_ast.statement
            typ_ = stmt_ast.__class__.__name__
            stmt_node_name = str(stmt_ast.lineno) + ':' + Type[typ_]

            #print 'Always child name: ' + stmt_node_name

            NodeQueue.append(stmt_node_name)
            CDFG.add_node(stmt_node_name, typ=typ_, \
                                          statements=[], \
                                          ast=stmt_ast, \
                                          fillcolor=fill_color(typ_), \
                                          style='filled', \
                                          label=stmt_node_name)
            CDFG.add_edge(p_node_name, stmt_node_name, cond=[], \
                                                       lineno=None, \
                                                       label='')

        elif (p_node_ast.__class__.__name__ == 'IfStatement'):
            condition = []
            get_rhs_cond_nodes(p_node_ast.cond, condition)
            
            true_ast = p_node_ast.true_statement
            true_typ = true_ast.__class__.__name__
            
            false_ast = p_node_ast.false_statement

            true_node_name = str(true_ast.lineno) + ':' + Type[true_typ]
            #print 'IfStatement true child name: ' + true_node_name

            try:
                false_typ = false_ast.__class__.__name__
                false_node_name = str(false_ast.lineno) + ':' + Type[false_typ]
                #print 'IfStatement false child name: ' + false_node_name
            except AttributeError:
                false_node_name = ''

            NodeQueue.append(true_node_name)
            CDFG.add_node(true_node_name, typ=true_typ, \
                                          statements=[], \
                                          ast=true_ast, \
                                          fillcolor=fill_color(true_typ), \
                                          style='filled', \
                                          label=true_node_name)
            true_label = generate_code(p_node_ast.cond)
            false_label = '!(' + true_label + ')'
            CDFG.add_edge(p_node_name, true_node_name, cond=condition, \
                                                       lineno=p_node_ast.lineno, \
                                                       label=true_label)

            if false_node_name:
                NodeQueue.append(false_node_name)
                CDFG.add_node(false_node_name, typ=false_typ, \
                                               statements=[], \
                                               ast=false_ast, \
                                               fillcolor=fill_color(false_typ), \
                                               style='filled', \
                                               label=false_node_name
                                               )
                CDFG.add_edge(p_node_name, false_node_name, cond=condition, \
                                                            lineno=p_node_ast.lineno, \
                                                            label=false_label)
    

        elif (p_node_ast.__class__.__name__ == 'CaseStatement' or
              p_node_ast.__class__.__name__ == 'CasexStatement'):
            comp = []
            get_comp_nodes(p_node_ast.comp, comp)
            caselist_ast = p_node_ast.caselist

            for case_ast in caselist_ast:
                case_typ = case_ast.__class__.__name__
                case_node_name = str(case_ast.lineno) + ':' + Type[case_typ]
                #print 'CaseStatement/CaseXStatement true child name: ' + case_node_name
                case_statement_ast = case_ast.statement

                NodeQueue.append(case_node_name)
                CDFG.add_node(case_node_name, typ=case_typ, \
                                              statements=[], \
                                              ast=case_ast, \
                                              fillcolor=fill_color(case_typ), \
                                              style='filled', \
                                              label=case_node_name
                                              )
                CDFG.add_edge(p_node_name, case_node_name, cond=comp, \
                                                           lineno=p_node_ast.lineno, \
                                                           label=generate_code(p_node_ast.comp))

        elif (p_node_ast.__class__.__name__ == 'Block'):
            stmts = p_node_ast.statements
            for c in stmts:
                if (c.__class__.__name__ == 'IfStatement'):
                    c_typ = c.__class__.__name__
                    c_node_name = str(c.lineno) + ':' + Type[c_typ]
                    #print 'Block-IfStatement child name: ' + c_node_name
                    NodeQueue.append(c_node_name)
                    CDFG.add_node(c_node_name, typ=c_typ, \
                                               statements=[], \
                                               ast=c, \
                                               fillcolor=fill_color(c_typ), \
                                               style='filled', \
                                               label=c_node_name
                                               )
                    CDFG.add_edge(p_node_name, c_node_name, cond=[], \
                                                            lineno=None, \
                                                            label='')

                elif (c.__class__.__name__ == 'BlockingSubstitution' or
                      c.__class__.__name__ == 'NonblockingSubstitution'):
                    CDFG.nodes[p_node_name]['statements'].append(c)
                    CDFG.nodes[p_node_name]['label'] = CDFG.nodes[p_node_name]['label'] + '\n' + \
                            generate_code(c)

                elif (c.__class__.__name__ == 'CaseStatement' or
                      c.__class__.__name__ == 'CasexStatement'):
                    c_typ = c.__class__.__name__
                    c_node_name = str(c.lineno) + ':' + Type[c_typ]
                    #print 'Block-CaseStatement/CaseXStatement child name: ' + c_node_name
                    NodeQueue.append(c_node_name)
                    CDFG.add_node(c_node_name, typ=c_typ, \
                                               statements=[], \
                                               ast=c, \
                                               fillcolor=fill_color(c_typ), \
                                               style='filled', \
                                               label=c_node_name
                                               )
                    CDFG.add_edge(p_node_name, c_node_name, cond=[], \
                                                            lineno=None, \
                                                            label='')
        
        elif (p_node_ast.__class__.__name__ == 'Case'):
            stmt_ast = p_node_ast.statement
            stmt_typ = stmt_ast.__class__.__name__
            stmt_node_name = str(stmt_ast.lineno) + ':' + Type[stmt_typ]
            #print 'Case child name: ' + stmt_node_name

            NodeQueue.append(stmt_node_name)
            CDFG.add_node(stmt_node_name, typ=stmt_typ, \
                                          statements=[], \
                                          ast=stmt_ast, \
                                          fillcolor=fill_color(stmt_typ), \
                                          style='filled', \
                                          label=stmt_node_name
                                          )
            CDFG.add_edge(p_node_name, stmt_node_name, cond=[], \
                                                       lineno=None, \
                                                       label='')

        elif (p_node_ast.__class__.__name__ == 'NonblockingSubstitution' or
              p_node_ast.__class__.__name__ == 'BlockingSubstitution'):  
            CDFG.nodes[p_node_name]['statements'].append(p_node_ast)
            CDFG.nodes[p_node_name]['label'] = CDFG.nodes[p_node_name]['label'] + '\n' + \
                    generate_code(p_node_ast)
            #        CDFG.node[p_node_name]['label']
    
    root_node = get_root_node(CDFG)[0]
    leaf_nodes = get_leaf_nodes(CDFG)
    
    #print root_node
    #print leaf_nodes

    joint_node = 'Leaf_' + str(root_node)
    CDFG.add_node(joint_node, def_var=[], label=joint_node)
    for lnode in leaf_nodes:
        CDFG.add_edge(lnode, joint_node, cond=[], \
                                         lineno=None)

    return

def traverse_CDFG(CDFG):
    # Pre-Order Traversal
    root_node = get_root_node(CDFG)[0]
    leaf_node = get_leaf_nodes(CDFG)[0]

    nodes = CDFG.nodes()
    
    # It is a dictionary of lists. Each Key is a destination node and the lists are different paths from
    # root node to destination node
    # unique_paths_in_CDFG = {}

    #for dst_node in leaf_nodes:
    #    paths = all_unique_paths(CDFG, root_node, dst_node)
    #    unique_paths_in_CDFG[dst_node] = paths
    #    del paths

    unique_paths_in_CDFG = all_unique_paths(CDFG, root_node, leaf_node)

    return unique_paths_in_CDFG

def all_unique_paths(CDFG, src, dst):

    nodes = list(CDFG.nodes())
    visited = [False] * len(nodes)
    
    # List of nodes of one path from src --> dst
    path = []
    # List of all paths from src --> dst
    paths = []

    s = nodes.index(src)
    d = nodes.index(dst)

    all_unique_path_dfs(CDFG, nodes, s, d, visited, path, paths)
    
    del path 

    return paths

def all_unique_path_dfs(CDFG, nodes, u, d, visited, path, paths):
    
    visited[u] = True
    path.append(nodes[u])

    if u == d:
        # Be careful. Since we are popping path later, do slicing to make a true copy. Else
        # path will be all empty
        paths.append(path[:])
    else:
        for i in CDFG.neighbors(nodes[u]):
            if visited[nodes.index(i)] == False:
                all_unique_path_dfs(CDFG, nodes, nodes.index(i), d, visited, path, paths)

    path.pop()
    visited[u] = False

    return

def get_root_node(CDFG):
    root_node_index = [n for n, d in list(CDFG.in_degree()) if d == 0]
    return root_node_index

def get_leaf_nodes(CDFG):
    leaf_node_indices = [n for n, d in list(CDFG.out_degree()) if d == 0]
    return leaf_node_indices

def plot_digraph(digraphs, curr_path, root):
    for digraph in digraphs:
        if not root:
            root_node = get_root_node(digraph)
            root_node[0] = root_node[0].replace(':', '_')
        else:
            root_node = root

        '''
        A = to_agraph(digraph)
        A.layout()
        A.draw(file_name)
        '''
        dep_file = curr_path + '/' + root_node[0] + '.dep'
        edge_info = digraph.edges()
        econtent = [i[0] + '\t' + i[1] for i in edge_info]
        dep_handle = open(dep_file, 'w')
        dep_handle.write('\n'.join(econtent))
        dep_handle.close()
        dep_summary = curr_path + '/' + root_node[0] + '.summary'
        dep_summ_handle = open(dep_summary, 'w')
        dep_summ_handle.write(
                'Total number of nodes in the variable dependency graph: ' \
                        + str(len(digraph.nodes())) + '\n' \
                'Total number of edges in the variable dependency graph: ' \
                        + str(len(digraph.edges()))
                        )
        dep_summ_handle.close()

        if len(digraph.nodes()) < 600:
            file_name = curr_path + '/' + root_node[0] + '.dot'
            write_dot(digraph, file_name)
            pdf_file_name = file_name[:file_name.rfind('.')] + '.pdf'
            #dot_command = 'dot -Tpdf ' + file_name + ' -o ' + pdf_file_name + ' && rm -rfv ' + file_name
            dot_command = 'dot -Tpdf ' + file_name + ' -o ' + pdf_file_name
            #print dot_command
            exec_command(dot_command, 'PIPE', 'PIPE')
    return


def plot_digraphs(CDFGS, cdfg_dir_name):

    if not len(CDFGS):
        print_warning('No CDFG found to draw')
        return
    cdfg_per_core = []

    task_queue = mps.Queue()
    done_queue = mps.Queue()

    i = 0
    for id in range(NUMBER_OF_PROCESSES):
        cdfg_per_core.append([])
        
    for CDFG in CDFGS:
        cdfg_per_core[i % NUMBER_OF_PROCESSES].append(CDFG)
        i = i + 1
        if  i == NUMBER_OF_PROCESSES:
            i = 0

    if len(cdfg_per_core) > 0:
        TASKS = [(plot_digraph, (cdfg_per_core[i], cdfg_dir_name, [])) \
                for i in range(NUMBER_OF_PROCESSES) if cdfg_per_core[i]]
        #root_node = get_root_node(CDFG)
        #file_name = curr_path + '/static/graphs/' + root_node[0] + '.dot'
        #plot_digraph(CDFG, file_name)
    for task in TASKS:
        task_queue.put(task)

    for i in range(len(TASKS)):
        mps.Process(target=worker, args=(task_queue, done_queue)).start()
    
    for i in range(len(TASKS)):
        done_queue.get()

    for i in range(len(TASKS)):
        task_queue.put('STOP')

    return

def CDFG(ast, clks, Params, Ports):
    # List containing Control Data Flow Graph of each of the Always block
    # and Assign Block
    CDFGS = []
    MODINSTS = {} 
    # Construction of CDFG per procedural block
    construct_CDFG(ast, CDFGS, MODINSTS, clks, 2)

    for CDFG in CDFGS:
        cdfg_type = CDFG.nodes[list(CDFG.nodes())[0]]['typ']
        if cdfg_type == 'Always':
            cdfg_ast =  CDFG.nodes[list(CDFG.nodes())[0]]['ast']
            add_nodes_to_CDFG(cdfg_ast, CDFG)
    # Traversal of CDFG per procedural block
    PathSets = []
    for CDFG in CDFGS:
        cdfg_type = CDFG.nodes[get_root_node(CDFG)[0]]['typ']
        if cdfg_type == 'Always':
            PathSets.append(traverse_CDFG(CDFG))
  
    var_def_chain = get_var_def_chain(CDFGS, PathSets, Params)
    #pp.pprint(var_def_chain)
    var_use_chain = get_var_use_chain(CDFGS, PathSets, Params)
    #pp.pprint(var_use_chain)
    dep_g = construct_var_dep_graph(var_def_chain, var_use_chain)

    # Fusing all CDFGs that includes both Always blocks and Assign blocks
    fused_INFO = construct_fused_CDFG(CDFGS, Ports)

    return var_def_chain, var_use_chain, PathSets, dep_g, CDFGS, fused_INFO, MODINSTS


def construct_fused_CDFG(CDFGS, Ports):
    
    fused_CDFG = nx.DiGraph()
    p_input_to_be_connected = {}
    p_output_to_be_connected = {}

    use_var_proc = {}
    def_var_proc = {}

    for CDFG in CDFGS:
        fused_CDFG = nx.compose(fused_CDFG, CDFG)
        root_node = get_root_node(CDFG)[0]
        cdfg_type = CDFG.nodes[root_node]['typ']
        
        if cdfg_type == 'Assign':
            use_var = CDFG.nodes[root_node]['use_var']
            def_var = CDFG.nodes[root_node]['def_var']

            for uvar in use_var:
                if uvar not in list(use_var_proc.keys()):
                    use_var_proc[uvar] = [root_node]
                else:
                    use_var_proc[uvar].append(root_node)
            for dvar in def_var:
                if dvar not in list(def_var_proc.keys()):
                    def_var_proc[dvar] = [root_node]
                else:
                    def_var_proc[dvar].append(root_node)

        elif cdfg_type == 'Always':
            leaf_node = get_leaf_nodes(CDFG)[0]
            use_var = CDFG.nodes[root_node]['use_var']
            def_var = CDFG.nodes[leaf_node]['def_var']

            for uvar in use_var:
                if uvar not in list(use_var_proc.keys()):
                    use_var_proc[uvar] = [root_node]
                else:
                    use_var_proc[uvar].append(root_node)
            for dvar in def_var:
                if dvar not in list(def_var_proc.keys()):
                    def_var_proc[dvar] = [leaf_node]
                else:
                    def_var_proc[dvar].append(leaf_node)


    for dvar in list(def_var_proc.keys()):
        srcs = def_var_proc[dvar]
        try:
            dests = use_var_proc[dvar]
        except KeyError:
            dests = []
            p_output_to_be_connected[dvar] = srcs
        
        if dvar in list(Ports['OPort'].keys()):
            p_output_to_be_connected[dvar] = srcs

        if dests:
            for src in srcs:
                for dest in dests:
                    if not fused_CDFG.has_edge(src, dest):
                        fused_CDFG.add_edge(src, dest)
    
    for uvar in list(use_var_proc.keys()):
        dests = use_var_proc[uvar]
        try:
            srcs = def_var_proc[uvar]
        except KeyError:
            srcs = []
            p_input_to_be_connected[uvar] = dests

        if srcs:
            for dest in dests:
                for src in srcs:
                    if not fused_CDFG.has_edge(src, dest):
                        fused_CDFG.add_edge(src, dest)

    ## FIXED: If output feeds to some internal signal as well, then that wont be recorded
    ##       into the p_output_to_be_connected as it will have a use_var_proc entry. So
    ##       please fix that.

    del use_var_proc
    del def_var_proc

    return tuple([fused_CDFG, \
                  p_input_to_be_connected, \
                  p_output_to_be_connected])


def get_var_use_chain(CDFGS, PathSets, Params):

    var_use_chain = {}

    path_index = 0

    for idx1 in range(len(CDFGS)):
        try:
            PathSet = PathSets[path_index]
        except:
            PathSet = []

        CDFG = CDFGS[idx1]

        path_key_set = set(itools.chain(*PathSet))
        CDFG_key_set = set(CDFG.nodes())

        if list(set.intersection(path_key_set, CDFG_key_set)):
            path_index = path_index + 1

        cdfg_type = CDFG.nodes[get_root_node(CDFG)[0]]['typ']
        if cdfg_type == 'Assign':
            node_name = list(CDFG.nodes())[0]
            ast = CDFG.nodes[node_name]['ast']
            def_var = get_lvalue(ast.left)
            use_vars = []
            if not get_rhs_constants(ast.right):
                get_rhs_cond_nodes(ast.right, use_vars)
                for use_var in use_vars:
                    if use_var in list(Params.keys()):
                        use_vars.remove(use_var)
            if use_vars:
                for use_var in use_vars:
                    if use_var not in list(var_use_chain.keys()):
                        var_use_chain[use_var] = {'Sensitivities': [ast],
                                                  'Lines': [str(ast.lineno) + ':D'],
                                                  'DefVars': [def_var]
                                                  }
                    else:
                        var_use_chain[use_var]['Sensitivities'].append(ast)
                        var_use_chain[use_var]['Lines'].append(str(ast.lineno) + ':D')
                        var_use_chain[use_var]['DefVars'].append(def_var)
            CDFG.nodes[node_name]['def_var'].append(def_var)
            CDFG.nodes[node_name]['use_var'].extend(use_vars)

        elif cdfg_type == 'Always':
            root_node = get_root_node(CDFG)[0]
            clocked = CDFG.nodes[root_node]['clk_sens']
            is_sens_empty = True if not CDFG.nodes[root_node]['sens'] else False
            for Path in PathSet:
                cond = []
                for idx2 in range(1, len(Path)):
                    edge = (Path[idx2 - 1], Path[idx2])
                    statements = CDFG.nodes[Path[idx2 - 1]]['statements']
                    if statements:
                        for statement in statements:
                            def_var = get_lvalue(statement.left)
                            use_vars = []
                            if not get_rhs_constants(statement.right):
                                get_rhs_cond_nodes(statement.right, use_vars)
                                for use_var in use_vars:
                                    if use_var in list(Params.keys()):
                                        use_vars.remove(use_var)

                            for use_var in use_vars:
                                if use_var not in list(var_use_chain.keys()):
                                    var_use_chain[use_var] = {'Sensitivities': [statement],
                                                              'Lines': [str(statement.lineno) + ':D'],
                                                              'DefVars': [def_var]
                                                              }
                                else:
                                    var_use_chain[use_var]['Sensitivities'].append(statement)
                                    var_use_chain[use_var]['Lines'].append(str(statement.lineno) + ':D')
                                    var_use_chain[use_var]['DefVars'].append(def_var)
                            # Set operation: To make sure that root node has an unique use var
                            # as accumulated from the different paths of an Always CDFG. Same variable
                            # can be used in different paths to define different varuiables.
                            use_vars_ = list(set(use_vars + CDFG.nodes[root_node]['use_var']))
                            CDFG.nodes[root_node]['use_var'] = use_vars_
                            
                            # Verilog syntax sens_vars are the only ones that are on the rvalue
                            sens_vars = []
                            if not clocked and is_sens_empty:
                                sens_vars = list(set(use_vars + CDFG.nodes[root_node]['sens']))
                                CDFG.nodes[root_node]['sens'] = sens_vars

                            del use_vars
                            del sens_vars
                            del use_vars_

                    cond.append(tuple([CDFG.get_edge_data(*edge)['cond'], \
                                       CDFG.get_edge_data(*edge)['lineno']]))

                    #cond.append(CDFG.get_edge_data(*edge)['cond'])
                 

                for cond_ in cond:
                    if cond_[0]:
                        for use_var in cond_[0]:
                            if use_var not in list(var_use_chain.keys()):
                                var_use_chain[use_var] = {'Sensitivities': [cond_[0]],
                                                          'Lines': [str(cond_[1]) + ':C' if cond_[1] else \
                                                                  cond_[1]],
                                                          'DefVars': [None]
                                                          }
                            else:
                                var_use_chain[use_var]['Sensitivities'].append(cond_[0])
                                var_use_chain[use_var]['Lines'].append(str(cond_[1]) + ':C' if cond_[1] else \
                                        cond_[1])
                                var_use_chain[use_var]['DefVars'].append(None)
                        # Set operation: To make sure that root node has an unique use var
                        # as accumulated from the different paths of an Always CDFG. Same variable
                        # can be used in different paths to define different varuiables.
                        use_vars = list(set(cond_[0] + CDFG.nodes[root_node]['use_var']))
                        CDFG.nodes[root_node]['use_var'] = use_vars
                        del use_vars

                del cond

    #pp.pprint(var_use_chain)

    return var_use_chain


def get_var_def_chain(CDFGS, PathSets, Params):

    var_def_chain = {}

    path_index = 0
    
    #print 'Length of CDFG: ' + str(len(CDFGS))
    #print 'Length of PathSets: ' + str(len(PathSets))

    for idx1 in range(len(CDFGS)):
        try:
            PathSet = PathSets[path_index]
        except IndexError:
            PathSet = []

        CDFG = CDFGS[idx1]
        
        path_key_set = set(itools.chain(*PathSet))
        CDFG_key_set = set(CDFG.nodes())

        if list(set.intersection(path_key_set, CDFG_key_set)):
            path_index = path_index + 1
        
        cdfg_type = CDFG.nodes[get_root_node(CDFG)[0]]['typ']
        if cdfg_type == 'Always':
            #for key in PathSet.keys():
            #    Paths = PathSet[key]
            #    print Paths
            leaf_node = get_leaf_nodes(CDFG)[0]
            clocked = CDFG.nodes[get_root_node(CDFG)[0]]['clk_sens']
            for Path in PathSet:
                #print Path
                cond = []
                clines = []
                for idx2 in range(1, len(Path)):
                    edge = (Path[idx2 - 1], Path[idx2])
                    #print edge
                    statements = CDFG.nodes[Path[idx2 - 1]]['statements']
                    #print statements
                    ##def_vars_ann_string = ''
                    if statements:
                        #The following list of def_vars is meant for edge annotation.
                        #Will be deleted as soon as edge annotation info is embedded in the 
                        #CDFG
                        def_vars = []
                        #c_dep = list(itools.chain(*cond))
                        c_dep = cond[:]
                        c_lines = clines[:]
                        for statement in statements:
                            def_var = get_lvalue(statement.left)
                            def_vars.append(def_var)
                            d_dep = []
                            if not get_rhs_constants(statement.right):
                                get_rhs_cond_nodes(statement.right, d_dep)
                                for dep in d_dep:
                                    if dep in list(Params.keys()):
                                        d_dep.remove(dep)
    
                            if def_var not in list(var_def_chain.keys()):
                                var_def_chain[def_var] = {'CDeps': [c_dep],
                                                          'DDeps': [d_dep],
                                                          'Clocked': clocked,
                                                          'Expressions': [statement],
                                                          'CLines': [c_lines],
                                                          'DLines': [str(statement.lineno) + ':D']
                                                          }
                            else:
                                var_def_chain[def_var]['CDeps'].append(c_dep)
                                var_def_chain[def_var]['DDeps'].append(d_dep)
                                var_def_chain[def_var]['Expressions'].append(statement)
                                var_def_chain[def_var]['CLines'].append(c_lines),
                                var_def_chain[def_var]['DLines'].append(str(statement.lineno) + ':D')
                            del d_dep
                        del c_dep

                        ##def_vars_ann_string = ',\n'.join(def_vars)

                        # Set operation: To make sure that leaf node has an unique def var
                        # as accumulated from the different paths of an Always CDFG. Same variable
                        # can be defined in different paths.
                        def_vars = list(set(def_vars + CDFG.nodes[leaf_node]['def_var']))
                        CDFG.nodes[leaf_node]['def_var'] = def_vars

                        del def_vars
                    ##if def_vars_ann_string:
                        #The attribute name needs to be label else dot will not
                        #intepret correctly. Weird no? :(
                        ##CDFG[Path[idx2 - 1]][Path[idx2]]['label'] = def_vars_ann_string
                    cond.append(CDFG.get_edge_data(*edge)['cond'])
                    clines.append(str(CDFG.get_edge_data(*edge)['lineno']) + ':C' \
                            if CDFG.get_edge_data(*edge)['lineno'] else CDFG.get_edge_data(*edge)['lineno'])
                    #print cond
                #print '\n' * 2
        elif cdfg_type == 'Assign':
            ast = CDFG.nodes[list(CDFG.nodes())[0]]['ast']
            def_var = get_lvalue(ast.left)
            d_dep = []
            get_rhs_cond_nodes(ast.right, d_dep)
            if def_var not in list(var_def_chain.keys()):
                var_def_chain[def_var] = {'CDeps': [],
                                          'DDeps': [d_dep],
                                          'Clocked': False,
                                          'Expressions': [ast],
                                          'CLines': [],
                                          'DLines': [str(ast.lineno) + ':D']
                                          }
            else:
                var_def_chain[def_var]['CDeps'].append([])
                var_def_chain[def_var]['DDeps'].append(d_dep)
                var_def_chain[def_var]['Expressions'].append(ast)
                var_def_chain[def_var]['CLines'].append([]),
                var_def_chain[def_var]['DLines'].append(str(ast.lineno) + ':D')

            del d_dep
    
    #pp.pprint(var_def_chain)

    return var_def_chain

def construct_var_dep_graph(var_def_chain, var_use_chain):
    
    dep_g = nx.DiGraph()

    use_vars = list(var_use_chain.keys())

    for use_var in use_vars:
        # use_lines: a list of the line numbers of usage of the current use_vars that have been
        #            already analyzed. No need to analyze it and over constrain the graph
        use_lines = []
        # Add node to the dependency graph
        if use_var not in dep_g.nodes():
            dep_g.add_node(use_var)
        # Capturing Data Dependencies
        DefVars = var_use_chain[use_var]['DefVars']
        Lines = var_use_chain[use_var]['Lines']

        '''
        for DefVar in DefVars:
            if not DefVar:
                continue
            if DefVar not in dep_g.nodes():
                dep_g.add_node(DefVar)

            if not dep_g.has_edge(use_var, DefVar):
                # print 'Addine New Edge from: ' + use_var + ' to: ' + DefVar
                dep_g.add_edge(use_var, DefVar, weight=1.0)
            else:
                # print 'Increasing Edge weight from: ' + use_var + ' to: ' + DefVar
                dep_g[use_var][DefVar]['weight'] += 1.0
        '''
        # This has been done instead of the above commented code to avoid adding edges for the same
        # usage of a variable to define another variable reached via a different path. Adding weight for
        # the same definition over-constraints the variable dependency graph
        for idx1 in range(len(DefVars)):
            DefVar = DefVars[idx1]
            Line = Lines[idx1]

            if not DefVar:
                continue
            if DefVar not in dep_g.nodes():
                dep_g.add_node(DefVar)

            if not dep_g.has_edge(use_var, DefVar):
                dep_g.add_edge(use_var, DefVar, weight=1.0)
                use_lines.append(Line)
            else:
                if Line not in use_lines:
                    dep_g[use_var][DefVar]['weight'] += 1.0

    def_vars = list(var_def_chain.keys())

    for def_var in def_vars:
        # Add node to the dependency graph
        if def_var not in dep_g.nodes():
            dep_g.add_node(def_var)

        CDeps = var_def_chain[def_var]['CDeps']
        for CDep in CDeps:
            CDep_flatened = list(itools.chain(*CDep))
            for ele in CDep_flatened:
                if not ele:
                    continue
                if ele not in dep_g.nodes():
                    dep_g.add_node(ele)

                if not dep_g.has_edge(ele, def_var):
                    dep_g.add_edge(ele, def_var, weight=1.0)
                else:
                    dep_g[ele][def_var]['weight'] += 1.0
    
    '''
    for mod_inst_chain in mod_inst_chains:
        root_module = get_root_node(mod_inst_chain)[0]

        instance_modules = mod_inst_chain.nodes()
        instance_modules.remove(root_module)
        
        if not instance_modules:
            continue
        
        print instance_modules
        for instance in instance_modules:
            portname = mod_inst_chain.node[instance]['portname']
            argname = mod_inst_chain.node[instance]['argname']
            module_name = mod_inst_chain.node[instance]['module_name']

            mports, mtyps = get_port_type(module_name, mod_inst_chains)

            for idx in range(len(portname)):
                #if portname[idx] == argname[idx]:
                #    continue
                p_index = mports.index(portname[idx])
                typ = mtyps[p_index]

                if typ == 'inp':
                    for arg in argname[idx]:
                        if arg != portname[idx]:
                            if not dep_g.has_edge(arg, portname[idx]):
                                dep_g.add_edge(arg, portname[idx], weight=1.0)
                elif typ == 'oup':
                    for arg in argname[idx]:
                        if arg != portname[idx]:
                            if not dep_g.has_edge(portname[idx], arg):
                                dep_g.add_edge(portname[idx], arg, weight=1.0)
    '''
    

    return dep_g

#def cone_of_influence(vtargets, var_def_chain, var_use_chain, \
#                      dep_g, PageRank, temp_length_max):
def cone_of_influence(vtargets, ELABORATE_INFO, \
                      dep_g, PageRank, temp_length_max, top_module, scope_module_map):

    # vtargets: list of target variables from top module identified. 
    # Primarily it contains the primary outputs and register variables

    # ELABORATE_INFO: has all the var_def_chain and the var_use_chain for all the modules
    # dep_g: variable dependency graph

    # Basic depth first search has beene employed

    # COI:  a directed graph where the root node is the target variable and each leaf node is the variable
    #       on which target variable depends on

    cones = {}

    for vtarget in vtargets:
        print(('Statically analyzing target variable: ' + vtarget))
        cone = nx.DiGraph()
        target_importance = PageRank[vtarget]
        target_complexity = tcomplexity(vtarget, top_module, scope_module_map, \
                ELABORATE_INFO)
        # vtarget is a Triplet (cycle, scope, var_name)
        # each cone node is a join of 
        vtarget_ = ['', '', vtarget]
        #$
        cone.add_node(gvn(vtarget_, 0), importance=target_importance,\
                               complexity=target_complexity, \
                               rank = 0.0 # We initialize rank of the target node
                               )
        temporal_cone(vtarget_, 0, temp_length_max, vtarget, PageRank, dep_g, \
                ELABORATE_INFO, scope_module_map, top_module, cone)
        #print coi.nodes()
        for n in cone.nodes():
            try:
                cone.nodes[n]['rank'] = cone.nodes[n]['importance'] / cone.nodes[n]['complexity']
            except ZeroDivisionError:
                cone.nodes[n]['rank'] = 0.0

        cones[vtarget] = cone
        #print cone.nodes() 
        #print nx.get_node_attributes(cone, 'importance')
        #print nx.get_node_attributes(cone, 'complexity')
        #print nx.get_node_attributes(cone, 'rank')
    return cones

def temporal_cone(var, temp_length, temp_length_max, vtarget, PageRank, dep_g, \
        ELABORATE_INFO, scope_module_map, top_module, cone):

    # helper function for cone_of_influence
    # vtarget is a Triplet (cycle, scope, var_name)

    if temp_length < temp_length_max:
        # TODO: import dependencies / move it from assertion_analyzer.py
        V = dependencies(var, ELABORATE_INFO, scope_module_map, top_module, \
                dep_g, temp_length, temp_length_max)
        # TODO: import expressions / move it from assertion_analyzer.py
        #var_name = var[var.find(']') + 1:] if '.' not in var \
        #        else var[var.rfind('.') + 1:]
        X = expressions(var, top_module, scope_module_map, ELABORATE_INFO)
        X_Keys = list(X.keys())

        for v in V:
            # Done to remove the time stamp from the true var name
            #$
            v_name = gvn(v, 1)#'.'.join(filter(None, v[1:]))
            # Relative Importance Calculation Part
            Ig_v = PageRank[v_name]
            #$
            Ir_vtarget = cone.nodes[gvn(var, 0)]['importance']
            v_vtarget_weight = dep_g.get_edge_data(v_name, gvn(var, 1))['weight']
            Ir_v_vtarget = Ig_v + v_vtarget_weight * Ir_vtarget

            # Relative Complexity Calculation Part. 
            # TODO: import sensitivities / move it from assertion_analyzer.py
            S = sensitivities(v, top_module, scope_module_map, ELABORATE_INFO)
            S_Keys = list(S.keys())
            Cr_v_target = 0
            Comm_Expr_Keys = list(set(X_Keys).intersection(set(S_Keys)))
            for key in Comm_Expr_Keys:
                Comm_Expr = X[key]
                #print(key)
                Cr_v_target = Cr_v_target + expr_length(Comm_Expr)

            # On my hunch
            #$
            Cr_v_target = Cr_v_target + cone.nodes[gvn(var, 0)]['complexity']

            # Add the variable nodes with all the information
            # Node_Name = '[' + str(temp_length) + ']' + v if temp_length > 0 else v
            # cone.add_node(Node_Name, importance=Ir_v_vtarget, \
            #$
            cone.add_node(gvn(v, 0), importance=Ir_v_vtarget, \
                                     complexity=Cr_v_target, \
                                     rank=0.0)
            # cone.add_edge(Node_Name, var)
            #$
            cone.add_edge(gvn(v, 0), gvn(var, 0))

        for v in V:
            # TODO: import temporal / move it from assertion_analyzer.py
            #v_name = v[v.find(']') + 1:]
            if temporal(var, top_module, scope_module_map, ELABORATE_INFO):
                # v = '[' + str(temp_length) + ']' + v if temp_length > 0 else v
                temporal_cone(v, temp_length + 1, temp_length_max, vtarget, PageRank, dep_g, \
                        ELABORATE_INFO, scope_module_map, top_module, cone)
            else:
                # v = '[' + str(temp_length) + ']' + v if temp_length > 0 else v
                temporal_cone(v, temp_length, temp_length_max, vtarget, PageRank, dep_g, \
                        ELABORATE_INFO, scope_module_map, top_module, cone)

    return

def find(dep, DDeps):
    for i, Dep in enumerate(DDeps):
        try:
            j = Dep.index(dep)
        except ValueError:
            continue
        return (i, j)

    return (None, None)

def dependencies(var, ELABORATE_INFO, scope_module_map, top_module, dep_g, k, kmax):
    # Changes: var is now triplet
    # var is a Triplet (cycle, scope, var_name)
    
    deps = []
    #print('From dependencies: ', var)
    #$
    var_name = gvn(var, 1)
    deps_from_dep_g = dep_g.predecessors(var_name)
    #print('From dependencies: ', deps_from_dep_g)

    if not deps_from_dep_g:
        # var is a primary input and has no dependencies
        return deps
   
    scope = var[1]
    module = top_module if not scope else scope_module_map[scope]
    var_def_chain = ELABORATE_INFO[module]['var_def_chain']
    
    try:
        DDeps = var_def_chain[var[2]]['DDeps']
        Clocked = var_def_chain[var[2]]['Clocked']
        #print 'From dependencies: ' + str(DDeps)
        Expressions = var_def_chain[var[2]]['Expressions']
        #print 'From dependencies: ' + str(Expressions)
    except KeyError:
        # Handling the instantiation connection
        lookback_string = var[0]
        scope = ['' if '.' not in i else i[:i.rfind('.')] for i in deps_from_dep_g]
        var = [i if '.' not in i else i[i.rfind('.') + 1:] for i in deps_from_dep_g]
        for j in range(len(scope)):
            deps.append([lookback_string, scope[j], var[j]])

        return deps
    
    for dep in deps_from_dep_g:
        found = find(dep, DDeps)
        #print 'From dependencies: ' + str(found)

        ## Handling data dependencies ##
        if found[0] != None:
            expression = Expressions[found[0]]
            #print 'Fromd dependencies: ' + str(expression)
            exp_typ = expression.__class__.__name__
            #print exp_typ
            if exp_typ == 'NonblockingSubstitution':
                nxt_k = k + 1
                if nxt_k < kmax:
                    #lookback_string = '[' + str(nxt_k) + ']' + dep
                    lookback_string = '[' + str(nxt_k) + ']'
                    deps.append([lookback_string, \
                            '' if '.' not in dep else dep[:dep.rfind('.')], \
                            dep if '.' not in dep else dep[dep.rfind('.') + 1:]
                        ])
                    #print 'Fromd dependencies: ' + lookback_string
            else:
                lookback_string = '[' + str(k) + ']' if k > 0 else ''
                deps.append([lookback_string, \
                        '' if '.' not in dep else dep[:dep.rfind('.')], \
                        dep if '.' not in dep else dep[dep.rfind('.') + 1:]
                        ])
        
        ## Handling control dependencies ##
        else:
            if Clocked:
                nxt_k = k + 1
                if nxt_k < kmax:
                    lookback_string = '[' + str(nxt_k) + ']'
                    deps.append([lookback_string, \
                            '' if '.' not in dep else dep[:dep.rfind('.')], \
                            dep if '.' not in dep else dep[dep.rfind('.') + 1:]
                            ])
            else:
                lookback_string = '[' + str(k) + ']' if k > 0 else ''
                deps.append([lookback_string, \
                        '' if '.' not in dep else dep[:dep.rfind('.')], \
                        dep if '.' not in dep else dep[dep.rfind('.') + 1:]
                        ])

    #print 'From dependencies: ' + str(deps)

    del deps_from_dep_g

    #print '\n' * 2

    return deps

#def tcomplexity(var, var_def_chain, var_use_chain):
def tcomplexity(var, top_module, scope_module_map, ELABORATE_INFO):
    
    var_def_chain = ELABORATE_INFO[top_module]['var_def_chain']
    var_use_chain = ELABORATE_INFO[top_module]['var_use_chain']

    complexity = 0

    X = expressions(['', '', var], top_module, scope_module_map, ELABORATE_INFO)
    X_Keys = list(X.keys())

    S = sensitivities(['', '', var], top_module, scope_module_map, ELABORATE_INFO)
    S_Keys = list(S.keys())
    Comm_Expr_Keys = list(set(X_Keys).intersection(set(S_Keys)))
    for key in Comm_Expr_Keys:
        Comm_Expr = X[key]
        complexity = complexity + expr_length(Comm_Expr)

    return complexity

def expr_length(Comm_Expr):
    
    Length = 0

    if type(Comm_Expr) is list:
        Length = len(Comm_Expr)
    else:
        Expr_Var = []
        get_rhs_cond_nodes(Comm_Expr, Expr_Var)
        Length = len(Expr_Var)

    return Length
        

def temporal(var, top_module, scope_module_map, ELABORATE_INFO):
    
    scope = var[1]
    module = top_module if not scope else scope_module_map[scope]
    var_def_chain = ELABORATE_INFO[module]['var_def_chain'] 
    v = var[2]

    def_lists = []

    try:
        def_lists = var_def_chain[v]['Expressions']
    except KeyError:
        return False

    for defn in def_lists:
        if defn.__class__.__name__ == 'NonblockingSubstitution':
            return True

    return False

def dependencies_deprecated(v, dep_g):
    # This returns the immediate predecessors in the dep_g graph. But that does not associate the 
    # time stamp of the dependent variable. Hence this is too crude and wont worl. Writing a new dependencies
    # above. Renaming it as dependencies_deprecated
    return dep_g.predecessors(v)

def expressions(var, top_module, scope_module_map, ELABORATE_INFO):
    # FIXME: line no for control statements
    scope = var[1]
    module = top_module if not scope else scope_module_map[scope]
    var_def_chain = ELABORATE_INFO[module]['var_def_chain']
    v = var[2]

    X = {}
    try:
        cdeps = var_def_chain[v]['CDeps']
        clines = var_def_chain[v]['CLines']
        expression = var_def_chain[v]['Expressions']
        dlines = var_def_chain[v]['DLines']
    except KeyError:
        return X
    
    # Adding data dependency expressions
    for idx in range(len(expression)):
        expr = expression[idx]
        lineno = dlines[idx]
        X[lineno] = expr

    # Adding control dependency expressions
    for idx in range(len(cdeps)):
        cdep = cdeps[idx]
        cline = clines[idx]
        for i in range(len(cdep)):
            if cdep[i]:
                expr = cdep[i]
                lineno = cline[i]
                X[lineno] = expr
    return X

def sensitivities(var, top_module, scope_module_map, ELABORATE_INFO):
    scope = var[1]
    module = top_module if not scope else scope_module_map[scope]
    var_use_chain = ELABORATE_INFO[module]['var_use_chain']
    v = var[2]

    S = {}

    try:
        sensitivity = var_use_chain[v]['Sensitivities']
        line = var_use_chain[v]['Lines']
    except KeyError:
        return S
    
    for idx in range(len(sensitivity)):
        sens = sensitivity[idx]
        lineno= line[idx]
        S[lineno] = sens

    return S


def process_targets(cones, top_module, ELABORATE_INFO, scope_module_map):
    # The signal dictionary for keeping track of the signals in the cone and to 
    # expand them further
    signals = {}
    
    # Regardless of the scopr module mop, the top level module signal has to be in 
    # the signals dictionary
    signals.update(ELABORATE_INFO[top_module]['ports']['IPort'])
    signals.update(ELABORATE_INFO[top_module]['ports']['OPort'])
    signals.update(ELABORATE_INFO[top_module]['ports']['Reg'])
    signals.update(ELABORATE_INFO[top_module]['ports']['Wire'])

    for key in list(scope_module_map.keys()):
        module_name = scope_module_map[key]
        for iport in list(ELABORATE_INFO[module_name]['ports']['IPort'].keys()):
            signals[key + '.' + iport] = ELABORATE_INFO[module_name]['ports']['IPort'][iport]

        for oport in list(ELABORATE_INFO[module_name]['ports']['OPort'].keys()):
            signals[key + '.' + oport] = ELABORATE_INFO[module_name]['ports']['OPort'][oport]

        for reg in list(ELABORATE_INFO[module_name]['ports']['Reg'].keys()):
            signals[key + '.' + reg] = ELABORATE_INFO[module_name]['ports']['Reg'][reg]

        for wire in list(ELABORATE_INFO[module_name]['ports']['Wire'].keys()):
            signals[key + '.' + wire] = ELABORATE_INFO[module_name]['ports']['Wire'][wire]

    target_cones = {}

    signals_keys = list(signals.keys())
    cone_keys = list(cones.keys())
    
    sig_name_pattern = re.compile(r'(\[[0-9]*\])?([A-Za-z0-9_]+)')

    for ckey in cone_keys:
        if ckey in signals_keys:
            # only for bit level target signal
            if signals[ckey] == 1:
                cnodes = list(cones[ckey].nodes())
                cnodes.remove(ckey)
                target_cones[ckey] = []
                for node in cnodes:
                    match_s = re.search(sig_name_pattern, node)
                    if match_s:
                        signal_name = match_s.group(2)
                        try:
                            if signals[signal_name] == 1:
                                target_cones[ckey].append(node)
                            else:
                                nodes = [node + '[' + str(i) + ']' for i in range(signals[signal_name])]
                                target_cones[ckey].extend(nodes)
                                del nodes
                        except KeyError:
                            pass
            # Still need to process whne the targets are the bus signals

    tkeys = list(target_cones.keys())

    for ckey in tkeys:
        if not target_cones[ckey]:
            try:
                del target_cones[ckey]
            except KeyError:
                pass

    return target_cones

def get_targets_of_manual_assertions(massertions):
    mtargets = {}

    for ele in massertions:
        mtarget = ele[-1][0]
        if mtarget not in list(mtargets.keys()):
            mtargets[mtarget] = [ele]
        else:
            mtargets[mtarget].append(ele)


    return mtargets
'''
def find_COI(dep_g, node, coi, p_node):

    if node not in coi.nodes():
        coi.add_node(node)
        if p_node:
            coi.add_edge(p_node, node)

        for n in dep_g.predecessors(node):
            find_COI(dep_g, n, coi, node)

    return
'''

def Linking(ELABORATE_INFO, top_module):

    scope = []
    complete_dep_g = ELABORATE_INFO[top_module]['dep_g']
    complete_fused_CDFG = ELABORATE_INFO[top_module]['fused_INFO'][0]
    InstanceQueue = [(scope, top_module, ELABORATE_INFO[top_module]['MODINSTS'])]
    scope_module_map = {}

    excess_nodes_added_in_fused_CDFG = []

    while InstanceQueue:
        curr = InstanceQueue.pop()
        curr_scope = curr[0]
        src_module = curr[1]
        curr_modinsts = curr[2]

        for inst in list(curr_modinsts.keys()):
            print(('Linking: '  + ' --> '.join([src_module, inst])))
            dep_g = ELABORATE_INFO[curr_modinsts[inst][0]]['dep_g']
            fused_CDFG = ELABORATE_INFO[curr_modinsts[inst][0]]['fused_INFO'][0]

            nxt_scope = curr_scope + [inst]
            nxt_MODINSTS = ELABORATE_INFO[curr_modinsts[inst][0]]['MODINSTS']
            InstanceQueue.append((nxt_scope, inst, nxt_MODINSTS))
            
            scope_module_map['.'.join(nxt_scope)] = curr_modinsts[inst][0]

            mapping = {}
            for onode in dep_g.nodes():
                mapping[onode] = '.'.join(nxt_scope) + '.' + onode

            dep_g = nx.relabel_nodes(dep_g, mapping)
            del mapping

            mapping = {}
            for cnode in fused_CDFG.nodes():
                mapping[cnode] = '.'.join(nxt_scope) + '.' + cnode
            fused_CDFG = nx.relabel_nodes(fused_CDFG, mapping)
            ##### This is a hack to tackle the labels. Cant think a better one now.
            ##### FIX it later if possible
            for node_ in fused_CDFG.nodes():
                l = fused_CDFG.nodes[node_]['label']
                l_split = l.split('\n')
                l_split[0] = node_
                fused_CDFG.nodes[node_]['label'] = '\n'.join(l_split)
            ##### This is a hack to tackle the labels. Cant think a better one now.
            ##### FIX it later if possible
            del mapping
            
            # NOTE: Linking the variable dependency graph of the top module
            #       and any other instantiated modules
            # NOTE: Linking the CDFG of the top_module 
            #       and any other instantiated module
            complete_dep_g = nx.compose(complete_dep_g, dep_g)
            portmap = curr_modinsts[inst][1]
            Ports = ELABORATE_INFO[curr_modinsts[inst][0]]['ports']

            complete_fused_CDFG = nx.compose(complete_fused_CDFG, fused_CDFG)
            p_input_to_be_connected = ELABORATE_INFO[curr_modinsts[inst][0]]['fused_INFO'][1]
            p_output_to_be_connected = ELABORATE_INFO[curr_modinsts[inst][0]]['fused_INFO'][2]

            for pname in list(portmap.keys()):
                node2s = portmap[pname]
                # NOTE: For variable dependency graph
                node1 = '.'.join(nxt_scope) + '.' + pname
                for node2 in node2s:
                    if pname in list(Ports['IPort'].keys()):
                        curr_scope = curr_scope + [node2]
                        src = '.'.join(curr_scope)
                        curr_scope.pop()
                        #print('1. Adding node: ' + src + ' ' + node1)
                        complete_dep_g.add_edge(src, node1, weight=1.0)
                    elif pname in list(Ports['OPort'].keys()):
                        curr_scope = curr_scope + [node2]
                        dest = '.'.join(curr_scope)
                        curr_scope.pop()
                        #print('2. Adding node: ' + node1 + ' ' + dest)
                        complete_dep_g.add_edge(node1, dest, weight=1.0)
                
                # NOTE: For CDFG
                if pname in list(p_output_to_be_connected.keys()):
                    onodes = p_output_to_be_connected[pname]
                    node3 = ['.'.join(nxt_scope) + '.' + onode for onode in onodes]
                elif pname in list(p_input_to_be_connected.keys()):
                    inodes = p_input_to_be_connected[pname]
                    node3 = ['.'.join(nxt_scope) + '.' + inode for inode in inodes]
                
                p_input_to_be_connected_src = ELABORATE_INFO[top_module if not curr_scope \
                        else scope_module_map['.'.join(curr_scope) \
                        ]]['fused_INFO'][1]
                p_output_to_be_connected_src = ELABORATE_INFO[top_module if not curr_scope \
                        else scope_module_map['.'.join(curr_scope) \
                        ]]['fused_INFO'][2]
                for node2 in node2s:
                    if pname in list(Ports['IPort'].keys()):
                        try:
                            srcs_ = p_output_to_be_connected_src[node2]
                        except KeyError:
                            srcs_ = [node2]
                        for src_ in srcs_:
                            curr_scope = curr_scope + [src_]
                            src = '.'.join(curr_scope)
                            curr_scope.pop()
                            if not complete_fused_CDFG.has_node(src):
                                excess_nodes_added_in_fused_CDFG.append(src)
                                complete_fused_CDFG.add_node(src)
                            for node3_ in node3:
                                complete_fused_CDFG.add_edge(src, node3_)
                    elif pname in list(Ports['OPort'].keys()):
                        try:
                            dests_ = p_input_to_be_connected_src[node2]
                        except KeyError:
                            dests_ = [node2]
                        for dest_ in dests_:
                            curr_scope = curr_scope + [dest_]
                            dest = '.'.join(curr_scope)
                            curr_scope.pop()
                            if not complete_fused_CDFG.has_node(dest):
                                excess_nodes_added_in_fused_CDFG.append(dest)
                                complete_fused_CDFG.add_node(dest)
                            for node3_ in node3:
                                complete_fused_CDFG.add_edge(node3_, dest)

    # NOTE: Clean up the complete_fused_CDFG graph to remove added extra nodes that are not 
    #       part of any CDFGs but some intermediate wire variable used to connect different CDFGs
    for enode in excess_nodes_added_in_fused_CDFG:
        predecessors = complete_fused_CDFG.predecessors(enode)
        successors = complete_fused_CDFG.successors(enode)
        for p in predecessors:
            complete_fused_CDFG.remove_edge(p, enode)
        for s in successors:
            complete_fused_CDFG.remove_edge(enode, s)

        for p in predecessors:
            for s in successors:
                complete_fused_CDFG.add_edge(p, s)

        complete_fused_CDFG.remove_node(enode)

    return complete_dep_g, complete_fused_CDFG, scope_module_map

def gvn(v, idx):

    var_name = ''
    if idx == 0:
        var_name = v[0] + '.'.join([_f for _f in v[1:] if _f])
    elif idx == 1:
        var_name = '.'.join([_f for _f in v[1:] if _f])

    return var_name

