import csv
import pandas as pd
from pyverilog.vparser.parser import parse as pyparse
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer as VDfA


def find_word_level_target(analyzer):

    # Phase 1: Discovering word level targets
    # Word level target will be 
    word_level_targets = {}
    
    analyzer.generate()
    terms = analyzer.getTerms()
    for tk, tv in sorted(terms.items(), key=lambda x:str(x[0])):
        termtype = tv.termtype
        if termtype == 'Output' or termtype == 'Reg':
            MSB = int(tv.msb.value)
            LSB = int(tv.lsb.value)
            width = MSB - LSB + 1
            if width >= 2:
                termname = str(tv.name)
                target = termname[termname.rfind('.') + 1:]
                word_level_targets[target] = [width, termtype]

    return word_level_targets

def find_word_level_assignments(word_level_targets, ast):

    
    return word_level_targets

def find_coi_word_level_target(verilog_ast, target):

    return coi_word_level_target

def find_weakest_precondition(coi, target, sim_paths):

    return weakest_precondition

def parse_verilog_data(verilog_file, topmodule, noreorder, nobind, include, define):
   
    ast, directives = pyparse(verilog_file, preprocess_include=include, preprocess_define=define)
    analyzer = VDfA(verilog_file, topmodule, noreorder=noreorder, nobind=nobind, preprocess_include=include, preprocess_define=define)

    return ast, analyzer

#    IPort, OPort, Reg, Wire = Get_Ports(ast)
#    def_vars = OPort + Reg + Wire 
#    use_vars = IPort + OPort + Reg + Wire
#    
#    predicates = {}
#
#    var_def_chain = var_definition(ast, def_vars, predicates) 
#    #pp.pprint(var_def_chain)
#    #pp.pprint(predicates)
#    var_use_chain = var_use(ast, use_vars, predicates)
#    #pp.pprint(var_use_chain)
#    #pp.pprint(predicates)
#    analyze_pagerank(var_use_chain, var_def_chain, use_vars)
#    
#    pp.pprint(predicates)

def analyze_pagerank(var_use_chain, var_def_chain, use_vars):

    #print(use_vars)
    
    global_graph_prank = nx.DiGraph()
    
    # Adding the nodes in the graph. Node consists of Input Port, Output Port, Registers
    # FIXED: Do we need to add the wires? Yes
    for var in use_vars:
        global_graph_prank.add_node(var)
        #global_graph_prank[var]['state'] = var

    # Constructing PageRank graph for the Data Dependency among variables
    for indep_var in var_use_chain.keys():
        #print('Indep var: ' + indep_var)
        uses = var_use_chain[indep_var]
        for use in uses:
            dep_var = use[2]
            #print('Dep var: ' + dep_var)
            if not global_graph_prank.has_edge(indep_var, dep_var):
                global_graph_prank.add_edge(indep_var, dep_var, weight=1.0)
            else:
                global_graph_prank[indep_var][dep_var]['weight'] += 1.0

    # Constructing PageRank graph for the Control Dependency among variables
    for dep_var in var_def_chain.keys():
        indep_vars = var_def_chain[dep_var][1]
        for indep_var in indep_vars:
            if not global_graph_prank.has_edge(indep_var, dep_var):
                global_graph_prank.add_edge(indep_var, dep_var, weight=1.0)
            else:
                global_graph_prank[indep_var][dep_var]['weight'] += 1.0

    pos = nx.spring_layout(global_graph_prank)
    nx.draw(global_graph_prank)
    #node_labels = nx.get_node_attributes(global_graph_prank, 'state')
    #nx.draw_network_labels(global_graph_prank, pos, labels = node_labels)
    plt.savefig('global_graph_prank.pdf')
    plt.close()

    PageRank = nx.pagerank(global_graph_prank, alpha=0.5)

    #print(PageRank)

    return PageRank


def Get_Ports(ast):
    IPort = []
    OPort = []
    Reg = []
    Wire = []
    Get_Ports_Name(ast, IPort, OPort, Reg, Wire)

    return IPort, OPort, Reg, Wire

def Get_Ports_Name(ast, IPort, OPort, Reg, Wire):
    if (ast.__class__.__name__ == 'Input'):
        IPort.append(getNodeName(ast))
    elif (ast.__class__.__name__ == 'Output'):
        OPort.append(getNodeName(ast))
    elif (ast.__class__.__name__ == 'Reg'):
        Reg.append(getNodeName(ast))
    elif (ast.__class__.__name__ == 'Wire'):
        Wire.append(getNodeName(ast))
    else:
        for c in ast.children():
            Get_Ports_Name(c, IPort, OPort, Reg, Wire)
    return

def getNodeName(ast):
    nvlist = [(n, getattr(ast, n)) for n in ast.attr_names]
    return nvlist[0][1]

def var_use(ast, use_vars, predicates):
    var_use_chain = {}
    parse_ast_find_use(ast, use_vars, var_use_chain, predicates)
    return var_use_chain

def parse_ast_find_use(ast, use_vars, var_use_chain, predicates):
    
    """
    parse_ast_find_use: For a particular variable, finds it all possible usages. Also find to which it assigns
                        value, and records the line number. DATA DEPENDENCY

    """

    #FIXME: Usage of a variable in Case, If-Else and other Control Statements need to be found

    if (ast.__class__.__name__ == 'CaseStatement' or
        ast.__class__.__name__ == 'CasexStatement'):
        comp = ast.comp
        caselist = ast.caselist
        comp_nodes = []
        get_comp_nodes(comp, comp_nodes)
        get_case_predicates(caselist, comp_nodes, predicates)
        #print('CaseStatement: ' + str(comp_nodes) + ' ' + str(ast.lineno))
        for c in ast.children():
            parse_ast_find_use(c, use_vars, var_use_chain, predicates)

#    elif (ast.__class__.__name__ == 'Case'):
#        cond = ast.cond
#        #print('Case: ' + str(cond) + ' ' + str(ast.lineno))
#        #if 
#        for c in ast.children():
#            parse_ast_find_use(c, use_vars, var_use_chain, predicates)

    elif (ast.__class__.__name__ == 'NonblockingSubstitution' or
        ast.__class__.__name__ == 'BlockingSubstitution' or
        ast.__class__.__name__ == 'Assign'):

        typ = ast.__class__.__name__
        left_var = get_lvalue(ast.left)
        right = ast.right
        curr_use_vars = []
        get_rhs_cond_nodes(right, curr_use_vars)
        for use_var in curr_use_vars:
            if use_var in use_vars and use_var in var_use_chain.keys():
                var_use_chain[use_var].append(tuple([ast, typ, left_var, ast.lineno]))
            elif use_var in use_vars and use_var not in var_use_chain.keys():
                var_use_chain[use_var] = [tuple([ast, typ, left_var, ast.lineno])]
    else:
        for c in ast.children():
            parse_ast_find_use(c, use_vars, var_use_chain, predicates)

    return

def get_case_predicates(caselist, comp_nodes, predicates):

    key = ', '.join(x for x in comp_nodes)
    if key not in predicates.keys():
        predicates[key] = []

    for case in caselist:
        if (case.__class__.__name__ == 'Case'):
            cond = case.cond
            predicates[key].append(cond[0])

    predicates[key] = list(set(predicates[key]))

    return

def get_rhs_cond_nodes(ast, curr_use_vars):
    # Taking care of Non-constants
    if ast.__class__.__name__ == 'Identifier':
        try:
            curr_use_vars.append(ast.name)
            return curr_use_vars
        except AttributeError:
            curr_use_vars.append(str(ast.var))
            return curr_use_vars
    # TODO: Need to take care of Constants for the Word Level Output predicates
    else:
        for c in ast.children():
            get_rhs_cond_nodes(c, curr_use_vars)

def var_definition(ast, def_vars, predicates):
    var_def_chain = {}
    #print(def_vars)
    parse_ast_find_def(ast, def_vars, var_def_chain, [], predicates)
    #pp.pprint(var_def_chain)
    return var_def_chain

def parse_ast_find_def(ast, def_vars, var_def_chain, cond_vars, predicates):
    
    """
    parse_ast_find_def: For a particular variable, finds all the definitions. Also find the control variables
                        on which the defined variable depends on. CONTROL DEPENDENCY
    """

    # FIXED: Need to take care of variable usage in If-Else, Case statements
    # Taking care variable usages in nonblocking, blocking and assign statements
    if (ast.__class__.__name__ == 'Always'):
       cond_vars = []
       for c in ast.children():
           parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)

    elif (ast.__class__.__name__ == 'IfStatement'):
       cond = ast.cond
       get_rhs_cond_nodes(cond, cond_vars)
       for c in ast.children():
           parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)
    
    elif (ast.__class__.__name__ == 'CaseStatement' or
          ast.__class__.__name__ == 'CasexStatement'):
        #pp.pprint(str(ast.caselist) + ' ' + str(ast.comp) + ' ' + str(ast.lineno))
        comp = ast.comp
        get_comp_nodes(comp, cond_vars)
        cond_vars = list(set(cond_vars))
        for c in ast.children():
            parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)
    
    #
    #elif (ast.__class__.__name__ == 'Case'):
    #    pp.pprint(str(ast.cond) + ' ' + str(ast.statement) + ' ' + str(ast.lineno))
    #    for c in ast.children():
    #        parse_ast_find_def(c, def_vars, var_def_chain, cond_vars)
        
    elif (ast.__class__.__name__ == 'NonblockingSubstitution' or 
        ast.__class__.__name__ == 'BlockingSubstitution' or
        ast.__class__.__name__ == 'Assign'):
        
        typ = ast.__class__.__name__
        left = ast.left
        curr_def_var = get_lvalue(left)
        
        # Find the constants that are assigned to some of the defined variables.
        # Later just check whichone is Output or Reg to find out the Word Level Predicate and 
        # Word Level Target
        right = ast.right
        rhs_constant = get_rhs_constants(right)

        # The following check removes Partselect object. 
        # FIXME: Need to fix Partselect object
        if curr_def_var in def_vars and curr_def_var in var_def_chain.keys():
            var_def_chain[curr_def_var][0].append(tuple([ast, typ, ast.lineno]))
            var_def_chain[curr_def_var][1] = list(set(cond_vars))
            if rhs_constant:
                try:
                    curr_vals = predicates[curr_def_var]
                    curr_vals.extend(tuple([rhs_constant]))
                    curr_vals = list(set(curr_vals))
                    predicates[curr_def_var] = curr_vals
                except TypeError:
                    predicates[curr_def_var].extend(tuple([rhs_constant]))

        elif curr_def_var in def_vars and curr_def_var not in var_def_chain.keys():
            if rhs_constant:
                var_def_chain[curr_def_var] = [[tuple([ast, typ, ast.lineno])], list(set(cond_vars))] 
                predicates[curr_def_var] = [rhs_constant]
            else:
                var_def_chain[curr_def_var] = [[tuple([ast, typ, ast.lineno])], list(set(cond_vars))]
                #predicates[curr_def_var] = []
    else:
        for c in ast.children():
            parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)

    return

def get_lvalue(ast):
    
    if (ast.__class__.__name__ == 'Lvalue'):
        try:
            return ast.var.name
        except AttributeError:
            var_name = get_var_partselect(ast)
            return var_name
            
def get_var_partselect(ast):
    name = ''
    if ast.__class__.__name__ == 'Identifier':
        return ast.name
    else:
        for c in ast.children():
            name = get_var_partselect(c)
            if name:
                break
    return name


def get_comp_nodes(ast, cond_vars):

    if ast.__class__.__name__ == 'Identifier':
        cond_vars.append(ast.name)
    elif ast.__class__.__name__ == 'Partselect':
        cond_vars.append(get_var_partselect(ast))
    else:
        for c in ast.children():
            get_comp_nodes(c, cond_vars)

def get_rhs_constants(ast):
   
    value = ''
    child = ast.children()[0]
    
    # TODO: in RHS like next_state = IDLE etc, IDLE is treated as an Identifier class although they 
    # TODO: were defined as parameter in the Verilog file. Hence needs some way to fix this.
    # TODO: Not sure now how to do this
    if (child.__class__.__name__ == 'Constant' or
        child.__class__.__name__ == 'IntConst' or
        child.__class__.__name__ == 'FloatConst' or
        child.__class__.__name__ == 'StringConst' or
        child.__class__.__name__ == 'Parameter'):
        
        return child.value
    
    return value
