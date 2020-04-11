import networkx as nx
import pickle
import os
import itertools as itools
import pprint as pp
import regex as re
from collections import OrderedDict as ODict
from datetime import datetime as dt

from configuration import current_path, make_directory, remove_file
from verilog import get_rhs_cond_nodes
from formal_verifier import passed_assertions, failed_assertions, vacuous_assertions
from helper import printTable
from plotter import x_y_plot
from verilog import generate_coverage

def analyze(Assertion_Results, top_module, target, rank_assertion, cone, aggregate, engine, verilog_files, include_directory):
    
    #print current_path()
    
    if not aggregate:
        IRank, AImportance, AComplexity = analyze_for_rank(target, rank_assertion, cone, engine)

        for key in Assertion_Results.keys():
            results = Assertion_Results[key]
            
            aimportance_ = {'Importance':round(AImportance[key], 5)}
            acomplexity_ = {'Complexity':AComplexity[key]}
            irank_ = {'IRank':round(IRank[key], 5)}
                
            results.update(aimportance_)
            results.update(acomplexity_)
            results.update(irank_)

            Assertion_Results[key] = results

            del aimportance_
            del acomplexity_
            del irank_
            del results

        gold_file = current_path() + '/verif/' + engine + '/' + target + '/' + target + '.gold'
        remove_file(gold_file)
        
        Assertion_Results = ODict(sorted(Assertion_Results.items(), key=lambda t: t[1]['IRank'], reverse=True))
        
        passed = passed_assertions(Assertion_Results)
        failed = failed_assertions(Assertion_Results)
        vacuous = vacuous_assertions(Assertion_Results)
        total = len(Assertion_Results.keys())

        dreport = ' Detailed Assertion Report '
        treport = ' Tabularized Assertion Report '
        sreport = ' Summarized Assertion Report '

        gfile = open(gold_file, 'w')

        gfile.write('Report file generated at: ' + dt.now().strftime('%b-%d-%Y %I:%M:%S %p') + '\n\n')
        
        gfile.write('#' * (len(dreport) + 2) + '\n')
        gfile.write('#' + dreport + '#' + '\n')
        gfile.write('#' * (len(dreport) + 2) + '\n')
        gfile.write('\n\n')
        
        Report = {}

        for key in Assertion_Results.keys():
            list_ = []
            results = Assertion_Results[key]
            
            gfile.write(key + ': ' + results['Assertion'] + '\n')
            
            gfile.write('IRank: ' + ': ' + str(results['IRank']) + '\n')
            list_.append(results['IRank'])
            
            gfile.write('Importance: ' + ': ' + str(results['Importance']) + '\n')
            list_.append(results['Importance'])
            
            gfile.write('Complexity: ' + ': ' + str(results['Complexity']) + '\n')
            list_.append(results['Complexity'])

            gfile.write('Triggered: ' + ': ' + str(results['Triggered']) + '\n')
            list_.append(results['Triggered'])
            
            gfile.write('Vacuous: ' + ': ' + str(results['Vacuous']) + '\n')
            list_.append(results['Vacuous'])
            
            gfile.write('Verification status: ' + ': ' + str(results['Status']) + '\n')
            list_.append(results['Status'])
            gfile.write('\n')
            
            Report[key] = list_
            del list_
        
        
        gfile.write('\n')
        gfile.write('#' * (len(treport) + 2) + '\n')
        gfile.write('#' + treport + '#' + '\n')
        gfile.write('#' * (len(treport) + 2) + '\n')
        gfile.write('\n\n')
        Report = ODict(sorted(Report.items(), key=lambda t: t[1][0], reverse=True))
        tcontent = printTable(Report, ['Assertion Index', 'IRank', 'Importance', 'Complexity', 'Triggered', \
                'Vacuous', 'Verif Status'])
        gfile.write(tcontent)
        gfile.write('\n')

        gfile.write('\n')
        gfile.write('#' * (len(sreport) + 2) + '\n')
        gfile.write('#' + sreport + '#' + '\n')
        gfile.write('#' * (len(sreport) + 2) + '\n')
        gfile.write('\n\n')

        gfile.write('Total number of mined assertions: ' + str(total) + '\n')
        gfile.write('Total number of passed assertions: ' + str(passed) + '\n')
        gfile.write('Total number of failed assertions: ' + str(failed) + '\n')
        gfile.write('Total number of vacuous / unexplored assertions: ' + str(vacuous) + '\n')
        gfile.write('Hit rate: ' + str(1.0 * passed / total) + '\n')
        gfile.write('Miss rate: ' + str(1.0 * (failed + vacuous) / total))
        
        assertion_index_list = Report.keys()
        irank_list = [Report[key][0] for key in Report.keys()]
        imp_list = [Report[key][1] for key in Report.keys()]
        complx_list = [Report[key][2] for key in Report.keys()]

        PICPATH = current_path() + '/pic/' + target
        make_directory(PICPATH)

        x_y_plot(imp_list, complx_list, top_module, target, 'Importace', 'Complexity', PICPATH)
        x_y_plot(imp_list, irank_list, top_module, target, 'Importace', 'IRank', PICPATH)
        x_y_plot(complx_list, irank_list, top_module, target, 'Complexity', 'IRank', PICPATH)

        gfile.close()

    else:
        ARank, IRank, SRank, AImportance, AComplexity = analyze_for_aggregation(target, \
                rank_assertion, cone, engine, verilog_files, include_directory, top_module, Assertion_Results)
        


        for key in Assertion_Results.keys():
            results = Assertion_Results[key]

            aimportance_ = {'Importance': round(AImportance[key], 5)}
            acomplexity_ = {'Complexity': AComplexity[key]}
            irank_ = {'IRank': round(IRank[key], 5)}
            srank_ = {'SRank': round(SRank[key][0], 5)}
            arank_ = {'ARank': ARank.index(int(key.split("a")[1]))}

            results.update(aimportance_)
            results.update(acomplexity_)
            results.update(irank_)
            results.update(srank_)
            results.update(arank_)

            Assertion_Results[key] = results

            del aimportance_
            del acomplexity_
            del irank_
            del srank_
            del arank_
            del results

        gold_file = current_path() + '/verif/' + engine + '/' + target + '/' + target + '.gold'
        remove_file(gold_file)

        Assertion_Results = ODict(sorted(Assertion_Results.items(), key=lambda t: t[1]['ARank'], reverse=True))

        passed = passed_assertions(Assertion_Results)
        failed = failed_assertions(Assertion_Results)
        vacuous = vacuous_assertions(Assertion_Results)
        total = len(Assertion_Results.keys())

        dreport = ' Detailed Assertion Report '
        treport = ' Tabularized Assertion Report '
        sreport = ' Summarized Assertion Report '

        gfile = open(gold_file, 'w')

        gfile.write('Report file generated at: ' + dt.now().strftime('%b-%d-%Y %I:%M:%S %p') + '\n\n')

        gfile.write('#' * (len(dreport) + 2) + '\n')
        gfile.write('#' + dreport + '#' + '\n')
        gfile.write('#' * (len(dreport) + 2) + '\n')
        gfile.write('\n\n')
        
        Report = {}

        for key in Assertion_Results.keys():
            list_ = []
            results = Assertion_Results[key]
            
            gfile.write(key + ': ' + results['Assertion'] + '\n')
            
            gfile.write('ARank: ' + ': ' + str(results['ARank']) + '\n')
            list_.append(results['ARank'])
            
            gfile.write('IRank: ' + ': ' + str(results['IRank']) + '\n')
            list_.append(results['IRank'])

            gfile.write('SRank: ' + ': ' + str(results['SRank']) + '\n')
            list_.append(results['SRank'])
            gfile.write('Importance: ' + ': ' + str(results['Importance']) + '\n')
            list_.append(results['Importance'])
            
            gfile.write('Complexity: ' + ': ' + str(results['Complexity']) + '\n')
            list_.append(results['Complexity'])

            gfile.write('Triggered: ' + ': ' + str(results['Triggered']) + '\n')
            list_.append(results['Triggered'])
            
            gfile.write('Vacuous: ' + ': ' + str(results['Vacuous']) + '\n')
            list_.append(results['Vacuous'])
            
            gfile.write('Verification status: ' + ': ' + str(results['Status']) + '\n')
            list_.append(results['Status'])
            gfile.write('\n')
            
            Report[key] = list_
            del list_
        
        
        gfile.write('\n')
        gfile.write('#' * (len(treport) + 2) + '\n')
        gfile.write('#' + treport + '#' + '\n')
        gfile.write('#' * (len(treport) + 2) + '\n')
        gfile.write('\n\n')
        Report = ODict(sorted(Report.items(), key=lambda t: t[1][0], reverse=True))
        tcontent = printTable(Report, ['Assertion Index', 'ARank', 'IRank', 'SRank', 'Importance', \
                'Complexity', 'Triggered', 'Vacuous', 'Verif Status'])
        gfile.write(tcontent)
        gfile.write('\n')

        gfile.write('\n')
        gfile.write('#' * (len(sreport) + 2) + '\n')
        gfile.write('#' + sreport + '#' + '\n')
        gfile.write('#' * (len(sreport) + 2) + '\n')
        gfile.write('\n\n')

        gfile.write('Total number of mined assertions: ' + str(total) + '\n')
        gfile.write('Total number of passed assertions: ' + str(passed) + '\n')
        gfile.write('Total number of failed assertions: ' + str(failed) + '\n')
        gfile.write('Total number of vacuous / unexplored assertions: ' + str(vacuous) + '\n')
        gfile.write('Hit rate: ' + str(1.0 * passed / total) + '\n')
        gfile.write('Miss rate: ' + str(1.0 * (failed + vacuous) / total))
        
        assertion_index_list = Report.keys()
        arank_list = [Report[key][0] for key in Report.keys()]
        irank_list = [Report[key][1] for key in Report.keys()]
        srank_list = [Report[key][2] for key in Report.keys()]
        imp_list = [Report[key][3] for key in Report.keys()]
        complx_list = [Report[key][4] for key in Report.keys()]

        PICPATH = current_path() + '/pic/' + target
        make_directory(PICPATH)

        x_y_plot(imp_list, complx_list, top_module, target, 'Importace', 'Complexity', PICPATH)
        x_y_plot(imp_list, irank_list, top_module, target, 'Importace', 'IRank', PICPATH)
        x_y_plot(imp_list, srank_list, top_module, target, 'Importace', 'SRank', PICPATH)
        x_y_plot(imp_list, arank_list, top_module, target, 'Importace', 'ARank', PICPATH)
        x_y_plot(complx_list, irank_list, top_module, target, 'Complexity', 'IRank', PICPATH)
        x_y_plot(complx_list, srank_list, top_module, target, 'Complexity', 'SRank', PICPATH)
        x_y_plot(complx_list, arank_list, top_module, target, 'Complexity', 'ARank', PICPATH)
        
        x_y_plot(irank_list, arank_list, top_module, target, 'IRank', 'ARank', PICPATH)
        x_y_plot(irank_list, srank_list, top_module, target, 'IRank', 'SRank', PICPATH)
        x_y_plot(arank_list, srank_list, top_module, target, 'ARank', 'SRank', PICPATH)

        gfile.close()


    return Assertion_Results

def importance(rank_assertion, cone):

    AImportance = {}

    literal_pattern = re.compile(r'(\[[0-9]*\])?([A-Za-z0-9_]+)(\[[0-9]*\])?')

    for key in rank_assertion.keys():
        assertion_component = rank_assertion[key]
        antecedent = assertion_component[0]
        importance = 0.0
        for var_val_pair in antecedent:
            variable = var_val_pair[0]
            match_n = re.search(literal_pattern, variable)
            if match_n:
                tstamp = match_n.group(1)
                node = match_n.group(2)
                if tstamp:
                    cone_node = tstamp + node
                else:
                    cone_node = node
                importance = cone.node[cone_node]['importance'] + importance
        AImportance[key] = importance

    return AImportance

def complexity(rank_assertion, cone):

    AComplexity = {}

    literal_pattern = re.compile(r'(\[[0-9]*\])?([A-Za-z0-9_]+)(\[[0-9]*\])?')

    for key in rank_assertion.keys():
        assertion_component = rank_assertion[key]
        antecedent = assertion_component[0]
        complexity = 0
        for var_val_pair in antecedent:
            variable = var_val_pair[0]
            match_n = re.search(literal_pattern, variable)
            if match_n:
                tstamp = match_n.group(1)
                node = match_n.group(2)
                if tstamp:
                    cone_node = tstamp + node
                else:
                    cone_node = node
                complexity = cone.node[cone_node]['complexity'] + complexity
        AComplexity[key] = complexity

    return AComplexity

def analyze_for_rank(target, rank_assertion, cone, engine):

    AImportance = importance(rank_assertion, cone)

    AComplexity = complexity(rank_assertion, cone)

    cone_file = current_path() + '/verif/' + engine + '/' + target + '/' + target + '.cone'

    remove_file(cone_file)

    cfile = open(cone_file, 'w')
    for node in cone.nodes():
        imp = round(cone.node[node]['importance'], 5)
        complx = cone.node[node]['complexity']
        cfile.write(node + '\n')
        cfile.write('Importance: ' + str(imp) + '\n')
        cfile.write('Complexity: ' + str(complx) + '\n')
        cfile.write('Rank: ' + str(round(cone.node[node]['rank'], 5)) + '\n\n')
    
    cfile.close()
    

    IRank = {}
    for key in rank_assertion.keys():
        Importance = AImportance[key]
        Complexity = AComplexity[key]
        Rank = Importance / Complexity
        IRank[key] = Rank

    return IRank, AImportance, AComplexity

def analyze_for_aggregation(target, rank_assertion, cone, engine, verilog_files, include_directory, top_module, Assertion_Results):

    # FIXME: Ranking absolute and position index value for SRank.
        

    # Statement coverage based Ranking
    # FIXME Spencer needs to fill in here.
    directory = os.getcwd()
    SRank = generate_coverage(verilog_files, include_directory, Assertion_Results, directory, top_module)
    
    # Importance / Complexity Ranking
    IRank, AImportance, AComplexity = analyze_for_rank(target, rank_assertion, cone, engine)

    # FIXME: IRank is absolute values. I need the rank indices
    IRank = ODict(sorted(IRank.items(), key=lambda t: t[1], reverse=True))

    Ranking = {}
    Ranking['IRank'] = IRank.keys()
    Ranking['SRank'] = SRank.keys()
    
    # ARank: Aggrgated Rank
    ARank = aggregation(Ranking)

    return ARank, IRank, SRank, AImportance, AComplexity


def kemeny_young_approx(Ranking):
    # Ranking:  It is expected as a dictionary where each key of the dictionary is a ranking metric
    #           and the element of each of the key is the ranked indices of the set of mined assertions.
    # Example: Ranking = {'Importance' : [a0, a1, a2, a3], 'Complexity': [a1, a2, a3, a0], 
    #                    'Expectedness': [a2, a3, a0, a1], 'Ideality': [a3, a0, a1, a2]}
    # Returns Weighted Bipartite graphs

    Metrics = Ranking.keys()
    # Total number of assertions
    AName = sorted(Ranking[Metrics[0]], key=lambda t: int(t[1:]))

    R = len(AName)
    
    Matrix = []

    for A in AName:
        Matrix_ = []
        for r in range(R):
            Weight = 0
            for Metric in Metrics:
                ARank = Ranking[Metric].index(A)
                Weight = Weight + abs(ARank - r)
            Matrix_.append(Weight)
        Matrix.append(Matrix_)

    return Matrix

def kuhn_munkres(Matrix):
    # B: a weighted bipartite graph resulted from Kemenny Young Approximation
    # Returns a list with assertion name as the element and the index of the assertions name
    # is the rank of the assertion

    # KMList = [''] * len(B.nodes()) / 2

    # As of now it is implemented using Munkres library which uses the cost matrix

    m = Munkres()
    indices = m.compute(Matrix)
    KMList = [''] * len(indices)
    #print indices
    for row, column in indices:
        KMList[row] = column

    return KMList

def locally_kemenize(KMList, Ranking):

    # Golden Kendall Tau Distance after Kuhn-Munkres Algorithm
    KTauDistance = kendall_tau_distance(KMList, Ranking)
    #print KTauDistance
    
    PrevKTauDistance = KTauDistance
    CurrKTauDistance = 0
    
    # https://stackoverflow.com/questions/2612802/how-to-clone-or-copy-a-list
    '''
    With new_list = my_list, you don't actually have two lists. The assignment 
    just copies the reference to the list, not the actual list, so both new_list 
    and my_list refer to the same list after the assignment
    '''
    swapped = True
    
    while swapped:
        RunningList = KMList[:]
        for i in range(len(RunningList) - 1):
            RunningList[i], RunningList[i + 1] = RunningList[i + 1], RunningList[i]
            CurrKTauDistance = kendall_tau_distance(RunningList, Ranking)
            if CurrKTauDistance < PrevKTauDistance:
                PrevKTauDistance = CurrKTauDistance
                swapped = True
                KMList = RunningList[:]
                del RunningList
                break
            else:
                swapped = False
    
    return KMList

def kendall_tau_distance(KMList, Ranking):
    
    Metrics = Ranking.keys()
    KTauDistance = 0
    
    for Metric in Metrics:
        RMList = Ranking[Metric]
        #print 'Metric: ' + Metric + ' Rank list: ' + str(RMList)
        pairs = itools.combinations(range(0, len(KMList)), 2)
        for x, y in pairs:
            #a = RMList[x] - RMList[y]
            #b = KMList[x] - KMList[y]
            #print 'Combination: (' + str(x) + ', ' + str(y) + ')'
            a = RMList.index('a' + str(x)) - RMList.index('a' + str(y))
            b = KMList.index(x) - KMList.index(y)
            #print 'a: ' + str(a) + ' b: ' + str(b)

            # if different signs
            if a * b < 0:
                KTauDistance = KTauDistance + 1

    return KTauDistance

def aggregation(Ranking):

    Matrix = kemeny_young_approx(Ranking)
    # print(Matrix)
    KMList = kuhn_munkres(Matrix)
    # print('Old KMList: ' + str(KMList))
    KMList = locally_kemenize(KMList, Ranking)
    # print('New KMList: ' + str(KMList))
    
    return KMList

#### Test Code ##
#t0 = ['a0', 'a1', 'a2']
#t1 = ['a1', 'a0', 'a2']
#t2 = ['a2', 'a1', 'a0']
#
#Ranking = {}
#Ranking['Imp'] = t0
#Ranking['Cov'] = t1
#Ranking['Exp'] = t2
#
#aggregation(Ranking)
