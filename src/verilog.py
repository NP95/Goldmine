from datetime import datetime

from parse_assertions import parse_assertion, parse_assertion_file
import copy


import multiprocessing as mps

from Queue import Queue


import glob
import os # Various os operations
import sys # For various things
import re # To search for variable names
import random # To randomize values
import shutil # Delete directory
import json #dump the end dictionary
from configuration import current_path, make_directory, change_directory, \
        change_parent_directory, remove_directory, remove_file

from formal_verifier import worker, calculate

import time
# To pass arguments
from optparse import OptionParser

# Catch display errors
import networkx as nx
# For graph
import pygraphviz as gv
# import graphviz as gv

# For verilog executor
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf, ParseException)
import operator
import math


# Functions mainly for printing colors
from helper import parser_types as mc
from helper import bcolors as bc
from helper import figlet_print, exec_command, printTable
from helper import print_prefix, print_line_stars, print_current_time, print_start, print_info
from helper import print_fail, load_pickle, save_pickle
from pprint import pprint, pformat # For printing


#Parser for verilog
from pyverilog.vparser.parser import parse
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.dataflow.walker import VerilogDataflowWalker
from pyverilog.dataflow.graphgen import VerilogGraphGenerator
from pyverilog.utils.verror import DefinitionError

#Needed for ordered set
import collections
import inspect

#### Debug Switch ##############################################
debug = False
print_code = False
################################################################

################################################################
# Function: lineno
# Arguments: None
# Returns: None
# Message:
# Return current line no
################################################################
def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

class SignalException(Exception):
    pass

class signal(object):
    def __init__(self,name, sequential_info, signal_info):
        self.name = name
        self.sq_info = sequential_info
        self.sg_info = signal_info
        self.expanded = False
        self.value_table = dict()
        self.antecedent = False
        self.executed_statements = set()
        self.execute_path = []
        self.optimized_path = []
        self.executable_path = []
    def dump(self, linenum, othermessage):
        pass
        #raise SignalException(linenum + " " + self.name + othermessage, 0)
    def add_tree(self,tree):
        self.tree = tree
    def set_antecedent(self):
        self.antecedent = True
    def expand(self,verbose, directory_path):
        if (self.expanded):
            return []
        else:
            self.expanded = True
            if verbose:
                self.tree.layout(prog='dot')
                temp = self.tree.copy()
                temp.layout(prog='dot')
                for i in temp.iternodes():
                    try:
                        i.attr["label"] = i.split("_graph")[0] + " : " +i.split("_graphrename_")[1]
                    except:
                        i.attr["label"] = i.split("_graph")[0]
                temp.draw(directory_path + "/coverage_outputs/dataflow_graphs/" + self.name + ".png") 
            signals = [] 
            for edge in self.tree.edges():
                if (self.tree.out_degree(edge[1]) == 0):
                    if ("_graphrename" in edge[1]):
                        signals.append(str(edge[1]).split("_graph")[0])
                    else:
                        signals.append(str(edge[1])) 
            return signals

    def handle_branch(self, node, traversal, visited):
        # print("Handle branch " + str(node))
        iterate_list = []
        successors = self.tree.successors(node)
        for g in range(len(successors)):
            if (str(self.tree.get_edge(node, successors[g]).attr["label"]) == "COND"):
                con_index = g

            elif (str(self.tree.get_edge(node, successors[g]).attr["label"]) == "TRUE"):
                true_index = g
            elif (str(self.tree.get_edge(node, successors[g]).attr["label"]) == "FALSE"):
                false_index = g
        iterate_list.append(successors[con_index])
        iterate_list.append(successors[true_index])
        iterate_list.append(successors[false_index])
        for l in iterate_list:
            # print(str(lineno()) + " Iteration " + str(l))
            if (str(self.tree.get_edge(node, l).attr["label"]) == "COND"):
                traversal.append("IF")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                if (len(self.tree.successors(l)) == 0): # no children
                    traversal.append(l.split("_graph")[0])
                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                    nodes = []
                else:
                    nodes = [l]
                while (nodes):
                    # get the first node (-1 indicates dfs, 0 bfs)
                    cur_node = nodes.pop(0)
                    #if the node is new
                    if (cur_node not in visited):
                        # add to visited
                        # print(str(lineno()) + " Appending " + cur_node)
                        visited.add(cur_node)
                        #if this is a branch need to evaluate the branch first
                        count = 0
                        for g in self.tree.successors(cur_node):
                            nodes.append(g)
                            # print(str(lineno()) + " Label " + g.attr['label'])
                            if (g.attr['label'] == "Branch"):
                                #print(lineno())
                                (traversal, visited) = self.handle_branch(g,traversal, visited)
                            elif (g.attr['label'] == "PartSelect"):
                                (traversal, visited) = self.handle_part_select(g,traversal, visited)
                            elif (g.attr['label'] != "\N" and "'" not in g.attr['label']):
                                # print(str(lineno()) + " Calling OP")
                                (temp, visited) = self.handle_operator(g,visited)
                                if (len(temp.keys()) == 1):
                                    traversal.append(str(g.split("_graph")[0]))
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    traversal += temp.values()[0]
                                    # print(str(lineno()) + " Add to traversal " + str(temp.values()[0]))
                                else:
                                    # print(str(lineno()) + " Add to traversal " + str(temp['0']))
                                    traversal += temp['0']
                                    traversal.append(str(g.split("_graph")[0]))
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    traversal += temp['1']
                                    # print(str(lineno()) + " Add to traversal " + str(temp['1']))

                                if ((l.attr['label'] == "Land" or l.attr['label'] == "Lor") and count == 0):
                                    traversal.append(str(l.split("_graph")[0]))
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                            else:
                                if (count == 0):
                                    if "NOT" in l.upper():
                                        traversal.append(str(l.split("_graph")[0]))
                                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                        traversal.append(str(g).split("_graph")[0])
                                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    else:
                                        traversal.append(str(g).split("_graph")[0])
                                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                        traversal.append(str(l.split("_graph")[0]))
                                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                else:
                                    if (g not in visited):
                                        traversal.append(str(g).split("_graph")[0])
                                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                            count += 1
            elif (str(self.tree.get_edge(node, l).attr["label"]) == "TRUE"):
                traversal.append("BEGIN")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                if ("Branch" not in l and len(self.tree.successors(l)) == 0):
                    traversal.append(str(l.split("_graph")[0]))
                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                elif (l.split("_graph")[0].upper() in mc.OPERATORS):
                    if (l not in visited):
                        (temp, visited) = self.handle_operator(l,visited)
                        # pprint(temp)
                        traversal += temp['0']
                        # print(str(lineno()) + " Add to traversal " + str(temp['0']))
                        traversal.append(str(l.split("_graph")[0]))
                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                        # print(str(lineno()) + " Add to traversal " + str(temp['1']))
                        traversal += temp['1']
                else:
                    (traversal, visited) = self.handle_branch(l,traversal, visited)
                nodes = [l]
                while (nodes):
                    # get the first node (-1 indicates dfs, 0 bfs)
                    cur_node = nodes.pop(0)
                    #if the node is new
                    if (cur_node not in visited):
                        # add to visited
                        # print(str(lineno()) + " Appending " + cur_node)
                        visited.add(cur_node)
                        #if this is a branch need to evaluate the branch first
                        for g in self.tree.successors(cur_node):
                            nodes.append(g)
                            if (g.attr['label'] == "Branch"):
                                (traversal, visited) = self.handle_branch(g,traversal, visited)
                            elif (g.attr['label'] == "PartSelect"):
                                (traversal, visited) = self.handle_part_select(g,traversal, visited)
                            elif (g.attr['label'] != "\N" and "'" not in g.attr['label']):
                                # print(lineno())
                                (temp, visited) = self.handle_operator(g,visited)
                                if (len(temp.keys()) == 1):
                                    pass
                                    #print(lineno())
                                    #traversal.append(str(g.split("_graph")[0]))
                                    #print(str(lineno()) + " Add to traversal " + str(temp.values()))
                                    #traversal += temp.values()[0]
                                    #print(str(lineno()) + " Add to traversal " + str(temp.values()[0]))
                                else:
                                    traversal += temp['0']
                                    # print(str(lineno()) + " Add to traversal " + str(temp['0']))
                                    traversal.append(str(g.split("_graph")[0]))
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    # print(str(lineno()) + " Add to traversal " + str(temp['1']))
                                    traversal += temp['1']
                            else:
                                if (g not in visited):
                                    traversal.append(str(g).split("_graph")[0])
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                traversal.append("ENDIF")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))

            elif (str(self.tree.get_edge(node, l).attr["label"]) == "FALSE"):
                traversal.append("ELSE")
                traversal.append("BEGIN")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                if ("Branch" not in l and len(self.tree.successors(l)) == 0):
                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                    traversal.append(str(l.split("_graph")[0]))
                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                elif (l.split("_graph")[0].upper() in mc.OPERATORS):
                    if (l not in visited):
                        (temp, visited) = self.handle_operator(l,visited)
                        traversal += temp['0']
                        # print(str(lineno()) + " Add to traversal " + str(temp['0']))
                        traversal.append(str(l.split("_graph")[0]))
                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                        # print(str(lineno()) + " Add to traversal " + str(temp['1']))
                        traversal += temp['1']
                else:
                    (traversal, visited) = self.handle_branch(l,traversal, visited)
                nodes = [l]
                while (nodes):
                    # get the first node (-1 indicates dfs, 0 bfs)
                    cur_node = nodes.pop(0)
                    #if the node is new
                    if (cur_node not in visited):
                        # add to visited
                        # print(str(lineno()) + " Appending " + cur_node)
                        visited.add(cur_node)
                        #if this is a branch need to evaluate the branch first
                        #print(str(lineno()) + " cur " + cur_node)
                        for g in self.tree.successors(cur_node):
                            # print("Iter " + str(g))
                            nodes.append(g)
                            if (g.attr['label'] == "Branch"):
                                (traversal, visited) = self.handle_branch(g,traversal, visited)
                            elif (g.attr['label'] == "PartSelect"):
                                (traversal, visited) = self.handle_part_select(g,traversal, visited)
                            elif (g.attr['label'] != "\N" and "'" not in g.attr['label']):
                                # print(lineno())
                                (temp, visited) = self.handle_operator(g,visited)
                                if (len(temp.keys()) == 1):
                                    pass
                                    #traversal.append(str(g.split("_graph")[0]))
                                    #print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    #traversal += temp.values()[0]
                                    #print(str(lineno()) + " Add to traversal " + str(temp.values()[0]))
                                else:
                                    traversal += temp['0']
                                    # print(str(lineno()) + " Add to traversal " + str(temp['0']))
                                    traversal.append(str(g.split("_graph")[0]))
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                    traversal += temp['1']
                                    # print(str(lineno()) + " Add to traversal " + str(temp['1']))
                            else:
                                if (g not in visited):
                                    traversal.append(str(g).split("_graph")[0])
                                    # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                traversal.append("ENDELSE")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
        #pprint(traversal)
        return (traversal, visited)

    def handle_operator(self, node, visited):
        # pprint(visited)
        # print("Handle op " + str(node))
        # pprint(self.tree.successors(node))
        nodes = [node]
        op_queue = []
        returns = dict()
        returns[str(0)] = []
        returns[str(1)] = []
        while (nodes):
            # get the first node (-1 indicates dfs, 0 bfs)
            cur_node = nodes.pop(-1)
            #if the node is new
            if (cur_node not in visited):
                # add to visited
                visited.add(cur_node)
                #if this is a branch need to evaluate the branch first
                length  = len(list(self.tree.successors(node)))
                count = 0
                for g in self.tree.successors(cur_node):
                    # print(str(lineno()) + " " + str(g))
                    # print(str(lineno()) + " Appending " + cur_node)
                    nodes.append(g)
                    if (g.attr['label'] == "Branch"):
                        (returns[str(count)], visited) = self.handle_branch(g,returns[str(count)], visited)
                        # print(str(lineno()) + " Add to returns " + str(returns[str(count)][-1]))
                    elif (g.attr['label'] == "PartSelect"):
                        (returns[str(count)], visited) = self.handle_part_select(g,returns[str(count)], visited)
                        # print(str(lineno()) + " Add to returns " + str(returns[str(count)][-1]))
                    elif (g.attr['label'] != "\N" and "'" not in g.attr['label']):
                        if length == count:
                            continue
                        else:
                            # print(lineno())
                            (temp, visited) = self.handle_operator(g,visited)
                            if (len(temp) < 2 or str(g.split("_graph")[0]).upper() == "ULNOT"):
                                returns[str(count)] = [str(g.split("_graph")[0])] + temp['0']
                                # print(str(lineno()) + " Add to returns " + str(returns[str(count)][-1]))
                            else:
                                returns[str(count)] = temp['0'] + [str(g.split("_graph")[0])] + temp['1']
                                # print(str(lineno()) + " Add to returns " + str(returns[str(count)][-1]))
                    else:
                        returns[str(count)].append(str(g).split("_graph")[0])
                        # print(str(lineno()) + " Add to returns " + str(returns[str(count)][-1]))
                    count += 1
        if (not returns[str(1)]):
            del returns[str(1)]
        # print(lineno())
        # pprint(returns)
        return (returns, visited)

    def handle_concat(self, node, traversal,  visited):
        nodes = [node]
        op_queue = []
        while (nodes):
            # get the first node (-1 indicates dfs, 0 bfs)
            node = nodes.pop(-1)
            #if the node is new
            if (node not in visited):
                # add to visited
                visited.add(node)
                #if this is a branch need to evaluate the branch first
                temp = []
                for g in self.tree.successors(node):
                    nodes.append(g)
                    if (g.attr['label'] == "PartSelect"):
                        (temp, visited) = self.handle_part_select(g,temp, visited)
                    else:
                        temp.append(str(g).split("_graph")[0])
                count = 0
                line = ""
                for i in temp:
                    line += "(" + i + "<<" + str(count) + ")"
                    line += "+"
                    count += 1
                line = line[:-1]
                traversal.append(line)
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
        return (traversal, visited)
    def handle_part_select(self, node, traversal, visited):
        nodes = [node]
        while (nodes):
            # get the first node (-1 indicates dfs, 0 bfs)
            node = nodes.pop(-1)
            #if the node is new
            if (node not in visited):
                # add to visited
                visited.add(node)
                #if this is a branch need to evaluate the branch first
                select = dict()
                for l in self.tree.successors(node):
                    if (str(self.tree.get_edge(node, l).attr["label"]) == "MSB" or str(self.tree.get_edge(node, l).attr["label"]) == "LSB"):
                        select[str(self.tree.get_edge(node, l).attr["label"])] = convert_constant(l.split("_graph")[0])
                    else:
                        select["name"] = str(l).split("_graph")[0]
                traversal.append("PART(" + select["name"] +  "&" + str(calculate_max(select["MSB"], select["LSB"])) + ")")
                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))

        return (traversal, visited)

    def generate_execute_path(self):
        # to get around weird naming
        if (self.antecedent):
            return []
        for l in self.tree.nodes_iter(): 
            name = l
            break
        nodes = [name]
        traversal = []
        visited = set()
        while (nodes):
            # get the first node (-1 indicates dfs, 0 bfs)
            node = nodes.pop(0)
            #if the node is new
            if (node not in visited):
                # add to visited
                #if this is a branch need to evaluate the branch first
                visited.add(node)
                for g in self.tree.successors(node):
                    nodes.append(g)
                    if (g.attr['label'] == "Branch"):
                        # print(lineno())
                        (traversal, visited) = self.handle_branch(g,traversal, visited)
                    elif (g.attr['label'] == "PartSelect"):
                        (traversal, visited) = self.handle_part_select(g,traversal, visited)
                    elif (g.attr['label'] == "Concat"):
                        (traversal, visited) = self.handle_concat(g,traversal, visited)
                    elif (g.attr['label'] != "\N" and "'" not in g.attr['label']):
                        # print(lineno())
                        (temp, visited) = self.handle_operator(g,visited)
                        if (len(temp.keys()) == 1):
                            if (len(temp['0']) > 0):
                                traversal += temp['0']
                                traversal.append(str(g.split("_graph")[0]))
                                # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                                traversal += temp.values()[0]
                        else:
                            traversal += temp['0']
                            traversal.append(str(g.split("_graph")[0]))
                            # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
                            traversal += temp['1']
                    else:
                        traversal.append(str(g).split("_graph")[0])
                        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
        traversal.append("END EXECUTION: " + self.sq_info["lhs"])
        # print(str(lineno()) + " Add to traversal " + str(traversal[-1]))
        self.execute_path = traversal
        # pprint(traversal)
        return (traversal, visited)

    def get_count(self):
        count = 0
        for x in list(self.executed_statements):
            if "_rn" in self.optimized_path[x].split("=")[0]:
                continue
            count += 1
        return count

    def get_code(self):
        executed_code = []
        for i in sorted(list(self.executed_statements)):
            executed_code.append(self.optimized_path[i])
        return executed_code

    def add_value(self, cycle, value):
        self.value_table[str(cycle)] = value

    def get_value(self, cycle):
        return self.value_table[str(cycle)]

    def randomize_value(self, cycle):
        random = generate_random(self.sg_info[1], self.sg_info[2])
        self.value_table[str(cycle)] = random
    def print_signal(self):
        print_info(print_prefix(str(lineno()) + ":SIG") + str(self.name))
        print_info(print_prefix(str(lineno()) + ":ANTECEDENT") + str(self.antecedent))
        for cycle, value in iter(sorted(self.value_table.iteritems())):
            print_info(print_prefix(str(lineno()) + ": VAL") + "Cycle: " + str(cycle) + " Value: " + str(value))
        self.value_table = dict()

    
    def optimize_path(self):
        iterator = iter(self.executable_path)
        var_iterator = iter(self.execute_path)
        statement = str(next(iterator))
        var_statement = str(next(var_iterator))
        new_path = [] 
        new_variable_path = []
        converge_map = []
        while "END EXECUTION" not in statement:
            line_w_variables = ""
            line = ""
            if (statement.isdigit() or statement in mc.OPERATORS.values() or statement in mc.SINGLE_OPS.values() or "PART" in statement):
                while (statement.isdigit() or statement in mc.OPERATORS.values() or statement in mc.SINGLE_OPS.values() or "PART" in statement):
                    line += statement.replace("PART","")
                    line_w_variables += str(var_statement)
                    statement = iterator.next()
                    var_statement = var_iterator.next()
            else:
                line = statement
                line_w_variables = statement
                statement = iterator.next()
                var_statement = var_iterator.next()
            new_path.append(line)
            new_variable_path.append(line_w_variables)
        new_path.append(statement)
        new_variable_path.append(var_statement)
        self.executable = new_path
        self.optimized_path = new_variable_path


    def replace_signals(self, cycle, value_table, nodes):
        self.executable_path = copy.deepcopy(self.execute_path)
        for index in range(len(self.executable_path)):
            if ("END EXECUTION" in self.executable_path[index]):
                continue
            # print(self.executable_path[index])
            if (isinstance(self.executable_path[index],list)):
                self.executable_path[index] = self.executable_path[index][0]
            if (self.executable_path[index].upper() in mc.SINGLE_OPS):
                self.executable_path[index] = mc.SINGLE_OPS[self.executable_path[index].strip().upper()]
                self.execute_path[index] = mc.SINGLE_OPS[self.execute_path[index].strip().upper()]
            elif (self.executable_path[index].upper() in mc.OPERATORS):
                self.executable_path[index] = copy.deepcopy(mc.OPERATORS[self.executable_path[index].strip().upper()])
                self.execute_path[index] = copy.deepcopy(mc.OPERATORS[self.execute_path[index].strip().upper()])
            elif ("\'" in self.executable_path[index]):
                    value = convert_constant(self.executable_path[index].strip())
                    self.executable_path[index] =  str(value).strip()
            for signal, item in value_table.iteritems():
                if (isinstance(item, int)):
                    continue
                if (str(item.sq_info["rhs"]) == str(self.executable_path[index])):
                    value = item.get_value(cycle)
                    self.executable_path[index] =  self.executable_path[index].replace(item.sq_info["rhs"], str(value)).strip()
            # pprint(self.executable_path)
            if (not self.executable_path[index].isdigit()):
                for node in nodes:
                    if (str(node.replace(".", "_")) == str(self.executable_path[index])):
                        random_val = generate_random(nodes[node][1],nodes[node][2])
                        value_table[(node.replace(".", "_"), cycle)] = random_val
                        self.executable_path[index] =  self.executable_path[index].replace(node.replace(".","_"), str(random_val).strip())
                    if (str(node.replace(".", "_")) in str(self.executable_path[index])):
                        random_val = generate_random(nodes[node][1],nodes[node][2])
                        value_table[(node.replace(".", "_"), cycle)] = random_val
                        self.executable_path[index] =  self.executable_path[index].replace(node.replace(".","_"), str(random_val).strip())
        return self.executable_path


    def run_executable(self, cycle):
        self.optimize_path()
        # pprint(self.executable)
        if (len(self.executable_path) != 2):
            pass
            # print(lineno())
            # pprint(self.executable)
            # pprint(self.executable_path)
            # pprint(self.optimized_path)
        iterator = iter(self.executable)
        linenum = 0
        statement = str(next(iterator))
        nsp = NumericStringParser()
        result = None
        #pprint(self.executable)
        while "END EXECUTION:" not in statement:
            #print(str(lineno()) + " Statement " + str(statement))
            #break_point()
            if (statement == "IF"):
                statement = str(next(iterator))
                linenum += 1
                self.executed_statements.add(linenum)
                self.optimized_path[linenum] = "if " + self.optimized_path[linenum]
                try:
                    #print(str(lineno()) + " Eval " + str(statement.strip()))
                    branch_result = nsp.eval(statement, True)
                except:
                    self.dump(str(lineno()), ":" + statement)
                    branch_result = random.randint(0,1)
                #print(str(lineno()) + " Branch Result " + str(branch_result))
                if (not branch_result):
                    while statement != "ELSE":
                        #print(str(lineno()) + " Statement " + str(statement))
                        statement = str(next(iterator))
                        linenum += 1
                        # print(statement, linenum)
                    #print(str(lineno()) + " Statement " + str(statement))
                    self.executed_statements.add(linenum)
            elif (statement == "ELSE"):
                statement = str(next(iterator))
                linenum += 1
                # print(statement, linenum)
                while statement != "ENDELSE":
                    #print(str(lineno()) + " Statement " + str(statement))
                    statement = str(next(iterator))
                    linenum += 1
                    # print(statement, linenum)
            elif (statement == "ENDELSE" or statement == "ENDIF" or statement == "BEGIN"):
                pass
            else:
                self.executed_statements.add(linenum)
                self.optimized_path[linenum] = self.name + "="  + self.optimized_path[linenum]
                try:
                    #print(str(lineno()) + " Eval " + str(statement.strip()))
                    result = nsp.eval(statement.strip())
                    break
                except:
                    self.dump(str(lineno()), " | " + statement + " | " + self.optimized_path[linenum])
                    branch_result = random.randint(0,1)
                    result = 0
            statement = str(next(iterator))
            linenum += 1
        if result is None:
            self.randomize_value(cycle)
            #print(str(lineno()) + " Random ")
        else:
            self.add_value(cycle, result)
            #print(str(lineno()) + " Result " + str(result))
        self.optimized_path = filter(None, self.optimized_path) # fastest
        return self.optimized_path
        
    

class signal_tree(object):
    def __init__(self, top, modules, sequential_information, directory_path):
        self.top_signal = top
        self.signals = collections.OrderedDict()
        self.modules = modules
        self.sequential_information = sequential_information
        self.directory_path = directory_path
        self.nodes = None
        self.antecedents = None
        self.number_signals_traversed = 1
        self.number_constants = 0
        self.number_to_execute = 1
        self.full_code = []
        self.executable = []
        self.executed_instruction = set()
        self.avg_count = [0,0,0,0]
    def print_value_table(self):
        for key, value in self.signals.iteritems():
            if (isinstance(value, int)):
                print_info(print_prefix(str(lineno()) + ": SIG") + str(key[0])) 
                print_info(print_prefix(str(lineno()) + ": VAL") + "Cycle: {0} Value: {1}".format(str(key[1]), value)) 
            else:
                value.print_signal()
    def add_signal(self, signal):
        self.signals[signal.name] = signal
    def add_nodes(self, nodes):
        self.nodes = nodes
    def propogate_tree(self, verbose, end_cycle, topmodule):
        exhausted = False
        cycles_back = -1
        while (not exhausted):
            new_signals = []
            one_cycle_back_round = False
            for name, sig in self.signals.iteritems():
                if (not one_cycle_back_round):
                    one_cycle_back_round = True
                    cycles_back += 1
                if (end_cycle > cycles_back or sig.sg_info[3][0] == "Rename"):
                    child_signals = sig.expand(verbose, self.directory_path)
                else:
                    child_signals = []
                for signal in child_signals:
                    if (signal not in self.signals and signal not in new_signals):
                        if ((cycles_back+1) < end_cycle or "rn" in signal):
                            new_signals.append(signal)
            if (len(new_signals) == 0):
                exhausted = True
            for signal in new_signals:
              	#print_info(print_prefix(str(lineno()) + ":" + "GEN") + "Generating {0}...".format(signal))
                self.number_signals_traversed += 1
                if (signal.replace("_", ".") in self.signals):
                    self.number_signals_traversed -= 1
                    continue
                if ("'d" in signal or "'b" in signal):
                    self.number_signals_traversed -= 1
                    self.number_constants += 1
                    continue
                self = generate_graph(signal, self, self.directory_path, topmodule)
        self.number_to_execute = len(self.signals)
        self.signals = collections.OrderedDict(reversed(list(self.signals.items())))

    def randomize_all(self, cycle):
        for signal, graph in self.signals.iteritems():
            if (isinstance(graph, int)):
                continue
            if not graph.antecedent:
                graph.randomize_value(cycle)

    def execute_cycle(self, cycle):
        for signal, graph in self.signals.iteritems():
            if (isinstance(graph, int)):
                continue
            if not graph.antecedent:
                cur_executable = graph.replace_signals((cycle-1), self.signals, self.nodes)
                graph.run_executable(cycle)
                
    def get_code(self):
        full_code = []
        for signal, graph in self.signals.iteritems():
            if (isinstance(graph, int)):
                continue
            if not graph.antecedent:
                full_code += graph.get_code()
        return full_code
    def get_count(self):
        total_count = 0
        for signal, graph in self.signals.iteritems():
            if (isinstance(graph, int)):
                continue
            if not graph.antecedent:
                total_count += graph.get_count()
        return total_count

    def execute(self, print_code, iterations, assertion_value_table, end_cycle, assertion, num_lines):
        #randomize first variables
        number_of_runs = 0
        i = 0
        for signal, graph in self.signals.iteritems():
            graph.generate_execute_path()
        while (i < int(iterations)):
            counters = [0,0,0,0]
            full_code = []
            for cycle in range((end_cycle + 1)):
                if (cycle == 0):
                    self.randomize_all(cycle)
                else:
                    self.execute_cycle(cycle)
            i += 1
        full_code = self.get_code()
        total_count = float(self.get_count())/float(num_lines)
        i -= 1
        self.print_value_table()
        print_info(print_prefix(str(lineno()) + " FULL CODE") + "\n".join(full_code) + "\n")
        print_info(print_prefix("MESS") + "{0} Iterations went through".format(str(i)))
        print_info(print_prefix(str(lineno()) + ":" + "MESS") + "Number of Signals Traversed (including consequent)...{0}{1}{2}\n".format(bc.OKBLUE, self.number_signals_traversed, bc.ENDC))
        print_info(print_prefix(str(lineno()) + ":" + "MESS") + "Number of Signals To Execute...{0}{1}{2}\n".format(bc.OKBLUE, self.number_to_execute, bc.ENDC))
        print_info(print_prefix(str(lineno()) + ":" + "MESS") + "Number of Constants Traversed...{0}{1}{2}\n".format(bc.OKBLUE, self.number_constants, bc.ENDC))
        print_info(print_prefix("MESS") + "Final Count {0}".format(str(total_count)))


        return (total_count, full_code)

################################################################
# Function: NumericStringParser
# Arguments: 
# Returns: 
# Message:
# This is the object that can execute the verilog code. See the 
# message on the functions for more detail
# credit: https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string/9558001
#
#
################################################################
class NumericStringParser(object):
    # push the data on to the stack
    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    # push a minus onto the stack
    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        # input operators
        """
        expop   :: ':['
        multop  :: '*' | '/'
        addop   :: '+' | '-' | '&' | '$' | '|' | '@' | '^' | '<<' | '>>' | '~' | '<' | '>' | '=>'| '<=' | '!=' | '==' 
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                    Optional(point + Optional(Word(nums))) +
                    Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        # define the operations
        plus = Literal("+")
        minus = Literal("-")
        op_and = Literal("&")
        op_nand = Literal("$")
        op_nor = Literal("@")
        op_not = Literal("~")
        op_or = Literal("|")
        op_xor = Literal("^")
        op_shft_l = Literal("<<")
        op_shft_r = Literal(">>")
        op_lt = Literal("<")
        op_gt = Literal(">")
        op_ge = Literal("=>")
        op_le = Literal("<=")
        op_ne = Literal("!=")
        op_eq = Literal("==")
        expop = Literal(":[")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus | op_and | op_or | op_xor | op_shft_l | op_shft_r | op_not | op_nand | op_nor | op_lt | op_gt | op_ge | op_le | op_ne | op_eq
        multop = mult | div
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
             (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.pushFirst))
            | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
            ).setParseAction(self.pushUMinus)
        factor = Forward()
        factor << atom + \
            ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor+ \
            ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
            ZeroOrMore((addop + term).setParseAction(self.pushFirst))

        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        self.opn = {"+": operator.add,
               "-": operator.sub,
               "*": operator.mul,
               "/": operator.truediv,
               "&": operator.and_,
               "~": operator.inv,
               "|": operator.or_,
               "<<": operator.lshift,
               ">>": operator.rshift,
               "^": operator.xor,
               "<": operator.lt,
               ">": operator.gt,
               "=>": operator.ge,
               "<=": operator.le,
               "!=": operator.ne,
               "==": operator.eq
               }
        self.fn = {}

   ################################################################
   # Function: evaluate_stack 
   # Arguments: self, verilog_string
   # Returns: 
   # Message:
   # Replace the operators in the statement.
   #
   #
   #
   ################################################################
    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
             return -self.evaluateStack(s)
        if op in "+-*/^&|>><<<>=><=!===":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "~":
            op1 = self.evaluateStack(s)
            op2 = self.evaluateStack(s)
            if (op1 == 0):
                size = 1
            else:
                size = int(math.log(op1, 2)) + 1
            raw_inv = self.opn[op](op1)
            return raw_inv & size
        elif op == "$":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            and_res = operator.and_(op1, op2)
            if (and_res == 0):
                size1 = 0
                size2 = 0
                if (op1 != 0):
                    size1 = int(math.log(op1, 2)) + 1
                if (op2 != 0):
                    size2 = int(math.log(op2, 2)) + 1
                size = max(size1, size2)
            else:
                size = int(math.log(and_res, 2)) + 1
            raw_result = operator.inv(and_res)
            return raw_result & size
        elif op == "@":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            or_res = operator.or_(op1, op2)
            if (or_res == 0):
                size1 = 0
                size2 = 0
                if (op1 != 0):
                    size1 = int(math.log(op1, 2)) + 1
                if (op2 != 0):
                    size2 = int(math.log(op2, 2)) + 1
                size = max(size1, size2)
            else:
                size = int(math.log(or_res, 2)) + 1
            raw_result = operator.inv(or_res)
            return raw_result & size
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return int(op)

   ################################################################
   # Function: eval 
   # Arguments: The string to be parsed, condition which if true
   # will return all booleans
   # Returns: The value of the statement 
   # Message:
   # This is the statement called to run the verilog statements &
   # return the value.
   #
   #
   ################################################################
    def eval(self, num_string, condition=False, parseAll=True):
        self.exprStack = []
        if len(num_string) == 1:
            val = int(num_string)
            if (condition):
                if (val == 0 or val == False):
                    return False
                elif (val == 1 or val == True):
                    return True
                else:
                    print_fail("Expected condition but got non 0/1 or False/True") 
            else:
                if (val == False):
                    return 0
                elif (val == True):
                    return 1
                else:
                    return val
        num_string = num_string.replace("~&", "$")
        num_string = num_string.replace("~|", "@")
        num_string = num_string.replace("~", "(" + str(sys.maxint) + "^")
        num_string = num_string.replace("&&", "&")
        num_string = num_string.replace("||", "&")
        first = True
        not_replace = set()
        for i in num_string.split("(" + str(sys.maxint) + "^"):
            if (first):
                first = False
                continue
            for g in i:
                replace_string = ""
                if (not g.isdigit()):
                    break
                replace_string += g
            not_replace.add(g)
        for i in list(not_replace):
            num_string = num_string.replace("(" + str(sys.maxint) + "^" + i, "(" + str(sys.maxint) + "~" + i + ")")

            
        if ("\'" in num_string):
            first = True
            for g in num_string.split("\'"):
                complete_value = ""
                if (first):
                    first = False
                    prev_value = g
                    continue
                for x in prev_value[::-1]: #Look backwards through string
                    if not x.isdigit():
                        break
                    complete_value += x
                complete_value += "\'" + g[0]
                g = g.replace(g[0],"")
                for x in g:
                    if not x.isdigit():
                        break
                    complete_value += x
                value = convert_constant(complete_value)
                num_string = num_string.replace(complete_value, str(value), 1)
                prev_value = g
        if ("[" in num_string):
            first = True
            for g in num_string.split("["):
                if (first):
                    first = False
                    prev_value = g
                    continue
                prev_signal = ""
                for x in prev_value[::-1]: #Look backwards through string
                    if not x.isdigit():
                        break
                prev_signal += x
            temp = g.split("]")[0]
            (msb,lsb) = temp.split(":")
            complete_value += "\'" + g[0]
            value = calculate_max(int(msb),int(lsb))
            num_string = num_string.replace(prev_signal + "["+ str(temp) + "]", "(" + prev_signal + "&" + str(value) + ")", 1)
            prev_value = g

        if ("?" in num_string):
            cond_statements = []
            true_statements = []
            false_statements = [];
            for g in num_string.split("?"):
                if (":" not in g):
                    cond_statements.append(g)
                else:
                    true_statements.append(g.split(":")[0])
                    false_statements.append(g.split(":")[1])
                condition_results = []
                for l in cond_statements:
                    while (l.count("(") != l.count(")")):
                        if (l.count("(") > l.count(")")):
                            l = l.replace("(","",1)
                        else:
                            l = l.replace(")","",1)
                    results = self.bnf.parseString(l, parseAll)
                    val = self.evaluateStack(self.exprStack[:])
                    if (val == 0):
                        val = False
                    elif (val == 1):
                        val = True
                    else:
                        bc.print_fail("LAND condition not working")
                    condition_results.append(val)

                    if (condition):
                        return condition_results
                        
        if len(num_string) == 1:
            results = int(num_string)
        else:
            results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluateStack(self.exprStack[:])
        if (condition):
            if (val == 0 or val == False):
                return False
            elif (val == 1 or val == True):
                return True
            else:
                print_fail("Expected condition but got non 0/1 or False/True") 
        else:
            if (val == False):
                return 0
            elif (val == True):
                return 1
        return val


################################################################
# Function: generate_random
# Arguments: msb and lsb of a value
# Returns: random generator within these constraints
# Message:
# This function will generate a random value for a given number
#
#
#
################################################################
def generate_random(msb, lsb):
    try:
        val = int(msb.value)-int(lsb.value)
    except:
        print_info(print_prefix(str(lineno()) + ":FAIL") + str(msb) + " is not number")
        # print_fail(str(lsb))
        return 0
    power = abs(val)
    max_val = 2**power
    if (max_val == 1):
        max_val = 1
    random.seed(datetime.now())
    return random.randint(0,max_val)


################################################################
# Function: break_point 
# Message:
# Wait for user to press enter to continue
#
################################################################
def break_point():
   a = raw_input("Press Enter")


################################################################
# Function: generate_paths
# Arguments: graph: a graph, variable: the signal to generate-path
# executed_signals: the signals in the walker for the variable
# Returns: signals: signals in the system, conditionals: all the 
# conditionals in system, execution: the dataflow of the system
# Message:
# This generates all the paths including conditions, dataflow &
# prints this stuff to html SPO add saving functionality
#
#
################################################################
def generate_paths(H, signal_name, verbose, directory_path):
   if verbose:
      H.layout(prog='dot')
      H.draw(directory_path + "/coverage_outputs/dataflow_graphs/" + signal_name + ".png")
   signals = []
   for g in H.edges():
      if (H.out_degree(g[1]) == 0):
         if ("_graphrename" in g[1]):
            signals.append(str(g[1]).split("_graph")[0])
         else:
            signals.append(str(g[1]))
   return signals


def count_lines(file_name):
    num_lines = 0
    skip_in = ["input", "output", "module", "always", "reg", "integer", "wire"]
    skip_if = ["endcase", "endmodule", "end"]
    if (".v" in file_name):
        for line in open(file_name):
            line = line.strip()
            if (line):
                if (line not in skip_if):
                    if (not any(skip in line for skip in skip_in)):
                        num_lines += 1 
    return num_lines

################################################################
# Function: analyze_tree
# Arguments: The original arguments
# Returns: Return the dataflow analyzer from pyverilog
# Message:
# This function returns the analyzer function for the top module
#
#
#
################################################################
def analyze_tree(verilog_files, include_directory, topmodule):
    temp = copy.deepcopy(verilog_files)
    for l in range(len(verilog_files)):
        temp[l] = verilog_files[l]
    filelist = temp
    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)
        num_lines = count_lines(f)
        
    analyzer = VerilogDataflowAnalyzer(filelist, topmodule,
                                       noreorder=False,
                                       nobind=False,
                                       preprocess_include=include_directory,
                                       preprocess_define=[])
    analyzer.generate()
    return (analyzer, num_lines)


def write_code(file_path, split_string, signal_name):
    with open(file_path, "w") as file:
        string = ""
        number_of_tabs = 0
        while ("?" in split_string):
            initial = split_string.split("?", 1)[0]
            split_string = split_string.split("?", 1)[1]
            string += (number_of_tabs * "   ") + "if " + "("+ initial.replace("(", "").replace(")", "").split(":")[0].replace(" ", "") + ") "  + "{\n"
            if ("?" in split_string.split(":",1)[0]):
                pass
            else:
                string += ((number_of_tabs+1)*"   ") + signal_name + " = " + split_string.split(":",1)[0].replace(" ", "") + ";\n" + number_of_tabs*"   " + "}\n"
                string += (number_of_tabs*"   ") + "else {\n"
                split_string = split_string.split(":", 1)[1]
            number_of_tabs += 1
        string +=  number_of_tabs * "   " + signal_name + " = " + split_string.replace(")", "").replace("(","") + ";\n"
        while (number_of_tabs != 0):
            string += (number_of_tabs-1) * "   " + "}\n"
            number_of_tabs -= 1
        file.write(string) 

################################################################
# Function: generate_graph
# Arguments: original command arguments, consequent the original
# consequent signal
# Returns: the graph generated from the walker of the signal
# Message:
# This generates the first graph that is the one that is just
# the walker of the consequent
#
#
################################################################
def generate_graph(consequent, full_signal_tree, directory_path, topmodule):
   dot_file_path = "/coverage_outputs/dataflow_graphs/"
   node_file_path = "/coverage_outputs/static_analysis_saved/nodes.pickle"
   if (not full_signal_tree.nodes):
      analyzer = full_signal_tree.modules["analyzer"] 
      terms = full_signal_tree.modules["terms"]
      nodes = load_pickle(directory_path + node_file_path)
      if not nodes:
         nodes = dict()
         for tk, tv in sorted(terms.items(), key=lambda x:str(x[0])):
            for a in tv.termtype:
               tp = str(a)
            if (tp != "pass"):
               nodes[str(tv.name)] = (str(tv.name), tv.msb, tv.lsb, list(tv.termtype))
         save_pickle(directory_path + node_file_path, nodes)
      full_signal_tree.add_nodes(nodes)


   sequential_info = full_signal_tree.sequential_information[consequent.replace("_", ".")]
   signal_info = full_signal_tree.nodes[sequential_info["lhs"]]
   cur_signal = signal(consequent, sequential_info, signal_info)
   if os.path.exists(directory_path + dot_file_path + consequent + ".dot"):
       result = [directory_path + dot_file_path + consequent + ".dot"]
   else:
       result = glob.glob(directory_path + dot_file_path + consequent.replace("_", "*") + ".dot")
   if (len(result) == 1):
      cur_signal.add_tree(gv.AGraph(result[0]))
      full_signal_tree.add_signal(cur_signal)
      return full_signal_tree
##################### Add all the signals as nodes #############################
   analyser = full_signal_tree.modules["analyzer"] 
   terms = full_signal_tree.modules["terms"] 
   binddict = full_signal_tree.modules["binddict"]
   optimizer = full_signal_tree.modules["optimizer"]
   resolved_terms = full_signal_tree.modules["resolved_terms"]
   resolved_binddict = full_signal_tree.modules["resolved_binddict"]
   constlist = full_signal_tree.modules["constlist"]
   graphgen = VerilogGraphGenerator(topmodule, terms, binddict,
                                   resolved_terms, resolved_binddict, constlist, directory_path + dot_file_path + consequent + ".png", withcolor=True)
   walker = VerilogDataflowWalker(topmodule, terms, binddict, resolved_terms,
                                      resolved_binddict, constlist)

   signal_name = None
   for key in full_signal_tree.nodes:
      if bool(re.search(str(key), consequent)):
         signal_name = str(key)
   if (signal_name):
      tree = walker.walkBind(signal_name)
      write_code(directory_path + dot_file_path + signal_name.replace(".", "_") + ".code", tree.tostr(), signal_name)
      try:
         graphgen.generate(signal_name, walk=False, identical=False, step=2, reorder=False,delay=True)
         graphgen.graph.write(directory_path + "/coverage_outputs/dataflow_graphs/" + consequent + ".dot")
         cur_signal.add_tree(graphgen.graph)
         full_signal_tree.add_signal(cur_signal)
      except DefinitionError:
         # if there is no graph make a one node one :)
         graph = gv.AGraph(directed=True)
         graph.add_node(str(signal_name))
         graph.write(directory_path + "/coverage_outputs/dataflow_graphs/" + consequent + ".dot")
         cur_signal.add_tree(graph)
         full_signal_tree.add_signal(cur_signal)
   return full_signal_tree


################################################################
# Function: convert_constant
# Arguments: constant: constant value
# Returns: int value
# Message:
# This takes 'd4 and converts to 4 etc
#
#
#
################################################################
def convert_constant(constant):
    value = None
    constant = str(constant)
    if ("?" in constant):
        value = -1
    elif ("'b" in constant):
        binary = constant.split("'b")[1].replace("_", "")
        if ("x" in binary or "z" in binary):
            value = "und"
        else:
            value = int(binary, 2)
    elif ("'h" in constant):
        binary = constant.split("'h")[1].replace("_", "")
        value = int(binary, 16)
    elif ("'d" in constant):
        binary = constant.split("'d")[1].replace("_", "")
        value = int(binary)
    else:
        try:
            value = int(constant)
        except:
            print("Value is probably a param check")

    return value

################################################################
# Function: get_number
# Arguments: G: is a digraph
# Returns: the maximum value in the graph
# Message:
# This gets the last number in the graphs.
#
#
#
################################################################
def get_number(G):
   max = 0
   for i in G.nodes():
      if (not i):
         continue
      number = i.split(":")[1]
      try:
         number = number.split(":")[0]
      except:
         pass
      number = int(number)
      if (number > max):
         max = number
   return max
   



################################################################
# Function: calculate_max 
# Arguments: msb, lsb
# Returns: The largest int value that can be for msb and lsb
# Message:
# Calculates the maximum value given msb and lsb.
#
#
#
################################################################
def calculate_max(msb,lsb):
    max_val = 0
    for g in range(int(msb) + 1):
        if (g >= int(lsb)):
            max_val += 2**g
    if (msb == 0):
        max_val = 1
    return max_val


################################################################
# Function: clean_up
# Arguments: none
# Returns: none
# Message:
# Clean the directory up of parsing files.
#
#
#
################################################################
def clean_up():
   try:
      os.remove("parser.out")
      os.remove("parsetab.py")
      os.remove("parsetab.pyc")
   except OSError:
      pass

################################################################
# Function: successful_exit
# Arguments: none
# Returns: none
# Message:
# Exit with positive message and return a 0.
#
#
#
################################################################
def successful_exit():
   clean_up()
   print(print_prefix(str(lineno()) + ":" + "MES") + bc.OKGREEN + "Exiting Successfully" + bc.ENDC)
   exit(0)
   
################################################################
# Function: incorrect_exit 
# Arguments: none
# Returns: none
# Message:
# Exit with negative message and return 1.
#
#
#
################################################################
def incorrect_exit():
   clean_up()
   print_info(bc.FAIL + print_prefix(str(lineno()) + ":" + "MES") + bc.FAIL + "Exiting Incorrectly" + bc.ENDC)
   # exit(1)



################################################################
# Function: clean directory
# Message: Cleans the directory after running (mainly worried about
# cleaning the parsing files that pyverilog creates
#
################################################################
def clean_directory(directory_path):
    print_info("Cleaning")
    if (os.path.exists(directory_path + "/coverage_outputs")):
        shutil.rmtree(directory_path + "/coverage_outputs")

################################################################
# Function: create_directory
# Message: Create all of the directories needed 
#
################################################################
def create_directory(args, directory_path):
    if os.path.exists(directory_path + "/.analysis_info"):
        with open(directory_path + "/.analysis_info", "r") as file:
            file_edited = file.readlines()
            file_times = dict()
            if (type(file_edited) == list):
                for g in file_edited:
                    top_name = g.split(":")[0]
                    last_edited = g.split(":")[1].replace("\n", "")
                    file_times[top_name] = last_edited
            else:
                top_name = file_edited.split(":")[0]
                last_edited = file_edited.split(":")[1].replace("\n", "")
                file_times[top_name] = last_edited
        if (type(args) == list):
            for g in args:
                if g in file_times:
                    if (str(os.path.getmtime(g)) != file_times[g]):
                        print_info("Modified")
                        print_info(g)
                        clean_directory(directory_path)
                else:
                    print_info("New Files")
                    clean_directory(directory_path)
        else:
            if args in file_times:
                if (str(os.path.getmtime(args)) != file_times[g]):
                    print_info("Modified")
                    print_info(args)
                    clean_directory(directory_path)
            else:
                print_info("New Files")
                clean_directory(directory_path)

    with open(directory_path + "/.analysis_info", "w") as file:
        try:
            if (type(args) == list):
                for g in args:
                    time = os.path.getmtime(g)
                    file.write(str(g) + ":" + str(time) + "\n")
            else:
                time = os.path.getmtime(g)
                file.write(str(g) + ":" + str(time) + "\n")
        except:
            os.remove(directory_path + "/.analysis_info")
    if not os.path.exists(directory_path + "/coverage_outputs"):
        os.makedirs(directory_path + "/coverage_outputs")
        with open(directory_path + "/coverage_outputs/README.me", "w") as file:
            file.write("This is automatically generated outputs of coverage generator")
    if not os.path.exists(directory_path + "/internal_data"):
        os.makedirs(directory_path + "/internal_data")
        with open(directory_path + "/internal_data/README.me", "w") as file:
            file.write("This stores the intermediate paths")
    if not os.path.exists(directory_path + "/coverage_outputs/dataflow_graphs"):
        os.makedirs(directory_path + "/coverage_outputs/dataflow_graphs")
        with open(directory_path + "/coverage_outputs/dataflow_graphs/README.me", "w") as file:
            file.write("This stores the intermediate paths")
    if not os.path.exists(directory_path + "/coverage_outputs/path_information"):
        os.makedirs(directory_path + "/coverage_outputs/path_information")
        with open(directory_path + "/coverage_outputs/path_information/README.me", "w") as file:
            file.write("This stores the htmls of the paths")
    if not os.path.exists(directory_path + "/coverage_outputs/static_analysis_saved"):
        os.makedirs(directory_path + "/coverage_outputs/static_analysis_saved")

def get_clock_nature(signal, sequential_information, clean_signal):
    if (sequential_information is None):
        return 0
    information = sequential_information[signal.replace("_",".")]
    if (information["combinational"]):
        return False
    else:
        return True 


def search_signal(operand, next_op, signal_info, value_table, cycle, print_code, sequential_information, clean_signal, cur_sequential):
    info = None
    value = None
    if ((operand.replace("_", "."),cycle) in value_table):
        signal_sequential = get_clock_nature(operand, sequential_information, clean_signal)
        if (cur_sequential and signal_sequential):
            cur_cycle = cycle - 1
        else:
            cur_cycle = cycle
        value = (value_table[(operand.replace("_","."),cur_cycle)], operand)
        if (print_code):
            print_info(print_prefix(str(lineno()) + ":" + "MESS") + operand + "," + str(cur_cycle) + "=" + str(value[0]) + "[" + str(value[1]) + "]") 
        return (value_table, value)
    elif ("'d" in next_op or "'b" in next_op):
        value = (convert_constant(next_op), next_op)
        return (value_table, value)
    for key in signal_info:
        if (str(key).replace("_", ".") == operand.replace("_", ".")):
            info = copy.deepcopy(signal_info[key])
            break
    if (info is None):
        print_fail("[1] Can't find variable {0}".format(operand))
        incorrect_exit()
    else:
        random = generate_random(info[1], info[2])
        value = (random, operand)
        value_table[(str(operand.replace("_", ".")), cycle)] = random
        if (print_code):
            print_info(print_prefix(str(lineno()) + ":" + "RAND") + operand + "," + str(cycle) + "=" + str(random)) 

    return (value_table, value)


def get_assertions(assertion, nodes):
    antecedents = []
    assertion_value_table = dict()
    end_cycle = int(assertion["max_cycle"])
    add_for_every_cycle = False
    if (end_cycle == 0):
        end_cycle += 1
        add_for_every_cycle = True
    for g in assertion:
        if (str(g) != "consequent" and str(g) != "max_cycle" and str(g[0]) is not assertion["consequent"][0]):
            antecedents.append(g[0].replace("_","."))
            for x in range(end_cycle + 1):
                if (g[1] != x and not add_for_every_cycle):
                    (assertion_value_table, value) = search_signal(str(g[0]), "", nodes, assertion_value_table, x, print_code,None, None, None)
                else:
                    assertion_value_table[(g[0].replace("_","."), x)] = assertion[g]
    return (assertion_value_table, antecedents, end_cycle)

def get_module(verilog_files, include_directory, topmodule):
    modules = dict()
    (modules["analyzer"], num_lines) = analyze_tree(verilog_files, include_directory, topmodule) 
    modules["terms"] = modules["analyzer"].getTerms()
    modules["binddict"] = modules["analyzer"].getBinddict()
    modules["optimizer"] = VerilogDataflowOptimizer(modules["terms"], modules["binddict"])
    modules["optimizer"].resolveConstant()
    sequential_information = dict()
    modules["signals"] = modules["analyzer"].getSignals()
    for key, item in modules["terms"].iteritems():
        sequential_information[str(key).replace("_",".")] = {"always": "INPUT ONLY", "clock_name": None, "combinational": True, "is_sequential": False, "clock_edge": None, "lhs": str(key), "rhs": str(key).replace(".","_")}
    for key, item  in modules["binddict"].iteritems():
        item = item[0]
        always_info = item.alwaysinfo
        clock_name = item.getClockName()
        combinational = item.isCombination()
        is_sequential = item.isClockEdge()
        clock_edge = item.getClockEdge()
        sequential_information[str(key).replace("_",".")] = {"always": always_info, "clock_name": clock_name, "combinational": combinational, "is_sequential": is_sequential, "clock_edge": clock_edge, "lhs": str(key), "rhs": str(key).replace(".","_")}
    modules["resolved_terms"] = modules["optimizer"].getResolvedTerms()
    modules["resolved_binddict"] = modules["optimizer"].getResolvedBinddict()
    modules["constlist"] = modules["optimizer"].getConstlist()
    return (modules, sequential_information, num_lines)



def parse_verilog(vfilelist, include, define):

    ast, directives, preprocessed_code = parse(vfilelist, 
                            preprocess_include=include,
                            preprocess_define=define)
    #ast.show() 
    return ast, directives, preprocessed_code


def get_modules(ast, ModuleDefs, ModuleInstances):
    # AST: Abstract syntax tree of the parsed verilog file(s)
    # Modules: Is a dictionary where Keys are the Module name and Val of the Key is a list containing
    #          instances of the Module.
    # Any module whose Instance list is empty is a potential candidate for top module. If the top module 
    # specified in the command line option is such a module with no instantiation, work on that
    # 
    if (ast.__class__.__name__ == 'ModuleDef'):
        module = ast.name
        #if module not in Modules.keys():
        #    Modules[module] = []
        ModuleDefs[module] = ast
    elif (ast.__class__.__name__ == 'Instance'):
        module = ast.module
        inst_name = ast.name
        if module not in ModuleInstances.keys():
            ModuleInstances[module] = [inst_name]
        else:
            ModuleInstances[module].append(inst_name)

    for c in ast.children():
        get_modules(c, ModuleDefs, ModuleInstances)

    return 

def get_top_modules(Modules):
    
    Top_Modules = []

    for Module in Modules.keys():
        if not Modules[Module]:
            Top_Modules.append(Module)

    return Top_Modules

def get_params(ast, top_module):
    params = {}
    module_stat = False
    get_params_(ast, top_module, params, module_stat)

    return params

def get_params_(ast, top_module, params, module_stat):
    if (ast.__class__.__name__ == 'ModuleDef'):
        if ast.name == top_module:
            module_stat = True
        else:
            module_stat = False
    elif (ast.__class__.__name__ == 'Parameter' and module_stat):
        param_name = ast.name
        param_value = get_rhs_constants(ast.value)
        params[param_name] = param_value

    for c in ast.children():
        get_params_(c, top_module, params, module_stat)

    return

def get_ports(ast, top_module, Params):
    ports = {'IPort': {}, 'OPort': {}, 'Reg': {}, 'Wire': {}}
    module_stat = False
    get_ports_(ast, top_module, ports, module_stat, Params)

    return ports

def get_ports_(ast, top_module, ports, module_stat, Params):

    if (ast.__class__.__name__ == 'ModuleDef'):
        if ast.name == top_module:
            module_stat = True
        else:
            module_stat = False
    elif (ast.__class__.__name__ == 'Input' and module_stat):
        ports['IPort'].update(getPortDetails(ast, Params))
    elif (ast.__class__.__name__ == 'Output' and module_stat):
        ports['OPort'].update(getPortDetails(ast, Params))
    elif (ast.__class__.__name__ == 'Reg' and module_stat):
        ports['Reg'].update(getPortDetails(ast, Params))
    elif (ast.__class__.__name__ == 'Wire' and module_stat):
        ports['Wire'].update(getPortDetails(ast, Params))
    
    for c in ast.children():
        if (c.__class__.__name__ == 'Function'):
            continue
        get_ports_(c, top_module, ports, module_stat, Params)

    return

def flatten_port_width(ast, Params):
    
    if ast.__class__.__name__ == 'Plus':
        left = flatten_port_width(ast.left, Params)
        right = flatten_port_width(ast.right, Params)
        result = left + right 
        return result
    elif ast.__class__.__name__ == 'Minus':
        left = flatten_port_width(ast.left, Params)
        right = flatten_port_width(ast.right, Params)
        result = left - right
        return result
    elif ast.__class__.__name__ == 'IntConst':
        return int(ast.value)
    elif ast.__class__.__name__ == 'Identifier':
        try:
            return int(Params[ast.name])
        except KeyError:
            print_fail('Port width cannot be determined. Aborting')

    return

def getPortDetails(ast, Params):
    name = ast.name
    #print name
    if ast.width != None:
        msb = flatten_port_width(ast.width.msb, Params)
        lsb = flatten_port_width(ast.width.lsb, Params)
        width = msb -lsb + 1
    else:
        width = 1

    port = {name:width}
    return port

def getDefUseTarget(Ports):

    inputs = Ports['IPort'].keys()
    outputs = Ports['OPort'].keys()
    regs = Ports['Reg'].keys()
    wires = Ports['Wire'].keys()

    def_vars = list(set(outputs + regs + wires))
    use_vars = list(set(inputs + outputs + regs + wires))
    #targets = list(set(outputs + regs))
    #NOTE: Need to change to outputs + regs again
    targets = list(set(outputs))

    return def_vars, use_vars, targets


def rank(ast, def_vars, use_vars):
    
    predicates = {}

    var_def_chain = var_definition(ast, def_vars, predicates)

    var_use_chain = var_use(ast, use_vars, predicates)

    graph = construct_var_dep_graph(var_use_chain, var_def_chain, use_vars)

    PageRank = analyze_pagerank(graph)
    
    # NOTE: Need to return all four since I need them during Assertion Analysis.
    return PageRank, graph, var_def_chain, var_use_chain

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
       cond_vars_ = []
       get_rhs_cond_nodes(cond, cond_vars_)
       #get_rhs_cond_nodes(cond, cond_vars)
       # Get the current Condition of the If Statement as a list and append it to the main cond list
       # FIXME: FIX the nesting If-Else condition issue. URGENT TODO,
       cond_vars.append(cond_vars_)
       ################

       #print(str(ast.lineno) + ' ' + str(cond_vars))
       #print(str(ast.lineno) +  ' Parent has: ' + str(len(ast.children())))
       #for x in ast.children():
       #    print('They are: ' + str(x.__class__.__name__))
       #print('\n')

       ################
       for c in ast.children():
           parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)
       # Once the analysis of the current IF Statement is done pop out its list of cond elements 
       cond_vars.pop()
     
        
    elif (ast.__class__.__name__ == 'CaseStatement' or
          ast.__class__.__name__ == 'CasexStatement'):
        #pp.pprint(str(ast.caselist) + ' ' + str(ast.comp) + ' ' + str(ast.lineno))
        caselist = ast.caselist
        #pp.pprint(caselist) 
        comp = ast.comp
        cond_vars_ = []
        get_comp_nodes(comp, cond_vars_)
        cond_vars_ = list(set(cond_vars_))
        # Get the current Condition of the If Statement as a list and append it to the main cond list
        cond_vars.append(cond_vars_)
        for c in ast.children():
            parse_ast_find_def(c, def_vars, var_def_chain, cond_vars, predicates)
    
        # Once the analysis of the current IF Statement is done pop out its list of cond elements 
        cond_vars.pop()

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
            #print(cond_vars)
            conds = list(itertools.chain(*cond_vars))
            var_def_chain[curr_def_var][1] = list(set(conds))
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
                conds = list(itertools.chain(*cond_vars))
                var_def_chain[curr_def_var] = [[tuple([ast, typ, ast.lineno])], list(set(conds))] 
                predicates[curr_def_var] = [rhs_constant]
            else:
                conds = list(itertools.chain(*cond_vars))
                var_def_chain[curr_def_var] = [[tuple([ast, typ, ast.lineno])], list(set(conds))]
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

def get_comp_nodes(ast, cond_vars):

    if ast.__class__.__name__ == 'Identifier':
        cond_vars.append(ast.name)
    elif ast.__class__.__name__ == 'Partselect':
        cond_vars.append(get_var_partselect(ast))
    else:
        for c in ast.children():
            get_comp_nodes(c, cond_vars)

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

    return

def construct_var_dep_graph(var_use_chain, var_def_chain, use_vars):
    
    #print(use_vars)
    
    graph = nx.DiGraph()
    
    # Adding the nodes in the graph. Node consists of Input Port, Output Port, Registers
    # FIXED: Do we need to add the wires? Yes
    for var in use_vars:
        graph.add_node(var)
        #global_graph_prank[var]['state'] = var

    # Constructing PageRank graph for the Data Dependency among variables
    for indep_var in var_use_chain.keys():
        #print('Indep var: ' + indep_var)
        uses = var_use_chain[indep_var]
        for use in uses:
            dep_var = use[2]
            #print('Dep var: ' + dep_var)
            if not graph.has_edge(indep_var, dep_var):
                graph.add_edge(indep_var, dep_var, weight=1.0, discovered=0)
            else:
                graph[indep_var][dep_var]['weight'] += 1.0

    # Constructing PageRank graph for the Control Dependency among variables
    for dep_var in var_def_chain.keys():
        indep_vars = var_def_chain[dep_var][1]
        for indep_var in indep_vars:
            if not graph.has_edge(indep_var, dep_var):
                graph.add_edge(indep_var, dep_var, weight=1.0, discovered=0)
            else:
                graph[indep_var][dep_var]['weight'] += 1.0

    return graph

def analyze_pagerank(graph):
    
    # Remember the \alpha paramater of the Networkx package is 1 - \epsilon of the PageRank algorithm.
    # Hence any modification to \epsilon will reflect to \alpha via \alpha = 1 - \epsilon
    PageRank = nx.pagerank(graph, alpha=0.5)

    return PageRank


def generate_coverage(verilog_files, include_directory, list_assertions, directory_path, topmodule):
    args = []
    verbose = True
    args += verilog_files
    assertion_result_dictionary = dict()
    create_directory(args, directory_path)
    assertion_dict = parse_assertion(list_assertions, topmodule)
    for key in assertion_dict:
        assertion_name = key
        assertion = assertion_dict[assertion_name][0]
        assertion_string = assertion_dict[assertion_name][1]
        print_info(print_prefix(str(lineno()) + " ASSERTION") + str(assertion_string))
        (modules, sequential_information, num_lines) = get_module(verilog_files, include_directory, topmodule)
        full_signal_tree = signal_tree(assertion["consequent"][0], modules, sequential_information, directory_path)
        try:
            full_signal_tree = generate_graph(assertion["consequent"][0], full_signal_tree, directory_path, topmodule)
        except ValueError:
            print_fail("parsing_error")
            assertion_result_dictionary[str(assertion_name)] = (0, "Parsing Error")
            continue
        (assertion_value_table, antecedents, end_cycle) = get_assertions(assertion, full_signal_tree.nodes)
        full_signal_tree.antecedents = antecedents
        full_signal_tree.propogate_tree(verbose, end_cycle,topmodule)
        for key, value in assertion_value_table.iteritems():
            if (key[0].replace("_", ".") not in full_signal_tree.signals):
                sq_info = full_signal_tree.sequential_information[key[0].replace("_",".")]
                name = sq_info["lhs"]
                new_signal = signal(key[0].replace("_","."), sq_info, full_signal_tree.nodes[name])
                new_signal.set_antecedent()
                full_signal_tree.signals[key[0].replace("_",".")] = new_signal
            full_signal_tree.signals[key[0].replace("_",".")].add_value(key[1], value)

        (total_count,full_code) = full_signal_tree.execute(print_code, 100, assertion_value_table, end_cycle, assertion, num_lines)
        try:
            os.remove(directory_path + "/internal_data/dictionary_results.json")
        except:
            pass
        assertion_result_dictionary[str(assertion_name)] = (total_count, '\n'.join(full_code))
        with open(directory_path + "/internal_data/dictionary_results.json", 'w') as file:
            json.dump(assertion_result_dictionary, file)
    return assertion_result_dictionary


'''
def worker(inputQ, outputQ):
    for func, args in iter(inputQ.get, 'STOP'):
        result = calculate(func, args)
        outputQ.put(result)
 
def calculate(func, args):
    result = func(*args)
    return result
'''

    
def run_coverage((options,args),target, assertion_per_core, i):
    directory_name = target + '/core' + str(i)
    make_directory(directory_name)
    parent_dir = change_directory(directory_name)
    cmd_to_execute = generate_coverage((options,args), assertion_per_core, directory_name, parent_dir)
    
    data, err, retcode, mem_usage = exec_command(cmd_to_execute, 'PIPE', 'PIPE')
    change_parent_directory(parent_dir)

    return

def write_output_files(assertion, ranking, top, signal):
    pretty_table = dict()
    for key in ranking:
        pretty_table[key] = ranking[key][0]
    with open("./goldmine.out/" + top + "/coverage/" + signal + "/output.cov", "w") as file:
        file.write("Report file generated at: " + datetime.now().strftime('%b-%d-%Y %I:%M:%S %p') + "\n\n")
        file.write("#############################\n")
        file.write("# Detailed Assertion Report #\n")
        file.write("#############################\n\n")
        for x in sorted(ranking.items(), key=operator.itemgetter(1), reverse=True):
            assert_key = str(x[0])
            file.write(str(assertion[assert_key][1]) + "\n")
            file.write("Coverage Value: " + str(x[1][0]) + "\n")
            file.write("Full Code: \n")
            file.write(str(x[1][1]))
            file.write("\n\n")
        temp = sorted(pretty_table.items(), key=operator.itemgetter(1), reverse=True)
        pretty_table = dict()
        for (key, item) in temp:
            pretty_table[key] = item
        final_table = printTable(pretty_table, ["Assertion", "Value"])
        file.write(final_table)
    print_info(print_prefix(str(lineno()) + " FILE") + bc.OKBLUE + "./goldmine.out/" + top + "/coverage/" + signal + "/output.cov" + bc.ENDC)


def create_main_directories(top, assertion_signal, directory_path="."):
    if not os.path.exists(directory_path + "/goldmine.out"):
        os.makedirs(directory_path + "/goldmine.out")
        with open(directory_path + "/goldmine.out/README.me", "w") as file:
            file.write("Output files held here")
    if not os.path.exists(directory_path + "/goldmine.out/" + top):
        os.makedirs(directory_path +  "/goldmine.out/" + top)
    if not os.path.exists(directory_path + "/goldmine.out/" + top + "/coverage"):
        os.makedirs(directory_path + "/goldmine.out/" + top + "/coverage")
    if not os.path.exists(directory_path + "/goldmine.out/" + top + "/coverage/" + assertion_signal):
        os.makedirs(directory_path + "/goldmine.out/" + top + "/coverage/" + assertion_signal)


def run_threaded((options,args)):
    print_start()
    assertion_files = os.listdir(options.assertion_dir)
    cwd = os.getcwd()
    for file_name in assertion_files:
        if (".cov" in file_name):
            continue

        assertion_file = options.assertion_dir + "/" + file_name
        file_name = file_name.split(".")[0]
        Assertions = parse_assertion_file(assertion_file,options.topmodule)
        Assertion_Results = {}
        create_main_directories(options.topmodule, file_name)

        if not len(Assertions):
            print('No assertions to verify')
            return


        assertion_per_core = []
        
        task_queue = mps.Queue()
        done_queue = mps.Queue()
        
        i = 0
        NUMBER_OF_PROCESSES = mps.cpu_count() 
        for i in range(NUMBER_OF_PROCESSES):
            try:
                shutil.rmtree(cwd + "/goldmine.out/{0}/coverage/{1}/core{2}/internal_data/dictionary_results.json".format(options.topmodule, file_name, i))
            except:
                pass
        for idx in range(NUMBER_OF_PROCESSES):
            assertion_per_core.append([])

        i = 0
        for assertion in Assertions.keys():
            a_ = {}
            a_[assertion] = Assertions[assertion]
            assertion_per_core[i % NUMBER_OF_PROCESSES].append(a_)
            del a_
            i = i + 1
            if i == NUMBER_OF_PROCESSES:
                i = 0
        i = 0
        if len(assertion_per_core) > 1:
            TASKS = [(run_coverage, ((options, args), cwd + "/goldmine.out/{0}/coverage/{1}".format(options.topmodule, file_name), assertion_per_core[i], str(i))) for i in range(NUMBER_OF_PROCESSES) if assertion_per_core[i]]
            
        if (not options.threading):
            run_coverage((options, args), cwd + "/coverage_outputs", assertion_per_core[0], str(0))
            exit(1)

        for i in range(len(TASKS)):
            mps.Process(target=worker, args=(task_queue, done_queue)).start()
        for task in TASKS:
            task_queue.put(task)
            
        total_mem = 0
            
        for i in range(len(TASKS)):
            result = done_queue.get()

        for i in range(len(TASKS)):
            task_queue.put('STOP')
            
        for i in range(NUMBER_OF_PROCESSES):
            try:
                with open (cwd + "/goldmine.out/{0}/coverage/{1}/core{2}/internal_data/dictionary_results.json".format(options.topmodule, file_name, i), "r") as file:
                    Assertion_Results.update(json.load(file))
            except IOError:
                pass
        write_output_files(Assertions, Assertion_Results, options.topmodule, file_name)

 
    
def main(path="."):
    INFO = "Verilog code parser"
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    optparser.add_option("-t","--top",dest="topmodule",
                         default="TOP",help="Top module, Default=TOP")
    optparser.add_option("-a","--assertion_file",dest="assertion_dir",
                         help="Assertion File", default=None)
    optparser.add_option("-d","--saved_dict",dest="saved_dict",
                         default=None,help="Use old dict")
    optparser.add_option("-n", "--number_iterations",dest="iterations",
                         default=100,help="Number Iteration")
    optparser.add_option("--nobind",action="store_true",dest="nobind",
                         default=False,help="No binding traversal, Default=False")
    optparser.add_option("--noreorder",action="store_true",dest="noreorder",
                         default=False,help="No reordering of binding dataflow, Default=False")
    optparser.add_option("--parseonly",action="store_true",dest="parseonly",
                         default=False,help="No assertions just parse the module, Default=False")
    optparser.add_option("--verbose", action="store_true", dest="verbose",
                       default=False, help="Print graphs")
    optparser.add_option("--debug", action="store_true", dest="debug",
                       default=False, help="Debug statements")
    optparser.add_option("--notthreaded", action="store_false", dest="threading",
                       default=True, help="Thread it")
    optparser.add_option("--print_code", action="store_true", dest="print_code",
                       default=False, help="Print code that is executed")
    (options, args) = optparser.parse_args()
    global debug
    global print_code
    if (options.debug):
        debug = True
    if (options.print_code and not options.threading):
        print_code = True
    start_time = time.time()
    run_threaded((options,args))
    # if (options.threading):
    # else:
        # if (not options.parseonly):
            # assertion_files = os.listdir(options.assertion_dir)
            # for assertion_file in assertion_files:
                # print_start()
                # print(print_prefix(str(lineno()) + " FILE") + assertion_file.split(".GOLD")[0])
                # assertion_file = options.assertion_dir + "/" + assertion_file
                # if (".cov" in assertion_file):
                    # continue
                # assertions = [parse_assertion_file(assertion_file, options.topmodule)] #using default filename "assertions.txt
                # generate_coverage((options, args), assertions, str(path), ".")
        # else:
            # create_directory((options,args), '.')
    #         generate_all((options, args), '.')
    print_info(print_prefix(str(lineno()) + "TIME ") + "--- %s seconds ---" % (time.time() - start_time))        

if __name__ == '__main__':
    main()
