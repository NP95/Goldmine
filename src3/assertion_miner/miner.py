from formal_verifier import verify
from helper import figlet_print, print_info
from assertion_analyzer import analyze

from simulation import mine_data_valid, is_target_constant, erase_and_reindex_data, write_csv
from .miner_helper import construct_dframe, induct_assertion, print_assertion, set_containment

# Importing Mining functions
from configuration import make_directory
from .decision_tree import decision_tree as dtmine
from .best_gain_decision_forest import best_gain_decision_forest as bgdfmine
from .prism import prism as pmine


def analyze_manual_assertions(features, target, CONFIG, top_module, clks, rsts, \
        verilog_files, inc_dir_path, cone, aggregate, fverif, assertion_component, engine):
    
    verify_assertion = {}
    rank_assertion = {}

    index = 0
    for component in assertion_component:
        antecedent_feature = component[0]
        consequent_target = component[1]
        verify_assertion['a' + str(index)] = induct_assertion(antecedent_feature, consequent_target)
        rank_assertion['a' + str(index)] = component
        index = index + 1
    
    if not fverif:
        figlet_print('Verify')
        Assertion_Results = verify(target, verify_assertion, CONFIG, top_module, clks, rsts, \
                verilog_files, inc_dir_path, engine)
    else:
        print_info('Formal verification of mined assertions was skipped as per user request')
        Assertion_Results = {}
        for key in list(verify_assertion.keys()):
            Assertion_ = {}
            Assertion_['Status'] = 'Unknown'
            Assertion_['Vacuous'] = 'Unknown'
            Assertion_['Verified'] = 'Unknown'
            Assertion_['Assertion'] = verify_assertion[key]
            Assertion_Results[key] = Assertion_

            del Assertion_
    
    
    figlet_print('A Ranking')
    Assertion_Results = analyze(Assertion_Results, top_module, target, rank_assertion, cone, aggregate, engine)

    return verify_assertion


def miner(features, target, rows_, rows_invalid_type, CONFIG, top_module, clks, rsts, \
        verilog_files, inc_dir_path, cone, aggregate, fverif, engine):

    csv_dframe, signal_not_found = construct_dframe(features, target, rows_)

    if csv_dframe.empty:
        print_info('Failed to create mining data frame as signal: ' + signal_not_found + \
                ' not found in data set. Possibly ' + signal_not_found + ' is an Lvalue \
                of an Assign statement')
        return

    # Check for the validity of the data frames for mining
    if not mine_data_valid(csv_dframe):
        print_info('Sufficient valid data rows not found for mining.')
        return
    else:
        csv_dframe = erase_and_reindex_data(csv_dframe, target)
    
    # Check if the target value changes in the valid mining data frame. If target value is constant,
    # Mining cannot be done. Return
    if is_target_constant(csv_dframe, target):
        print_info('Target value did not change in valid data rows. Mining cannot continue')
        return
    

    # Indexed assertion to verify
    verify_assertion = {}
    # Indexed assertion component to rank
    rank_assertion = {}
    assertion_component = []

    if engine == 'dtree':
        dtmine(features, target, csv_dframe, [], assertion_component)
    elif engine == 'bgdf':
        bgdfmine(features, target, csv_dframe, [], assertion_component)
        assertion_component = set_containment(assertion_component)
    else:
        assertion_component = pmine(features, target, csv_dframe)

    if not assertion_component:
        print_info('Mining failed for target: ' + target)
        return
    #constructing indexed assertion for verification --> to pass to verify routine
    index = 0
    for component in assertion_component:
        antecedent_feature = component[0]
        consequent_target = component[1]
        verify_assertion['a' + str(index)] = induct_assertion(antecedent_feature, consequent_target)
        rank_assertion['a' + str(index)] = component
        index = index + 1
    
    if not fverif:
        figlet_print('Verify')
        Assertion_Results = verify(target, verify_assertion, CONFIG, top_module, clks, rsts, \
                verilog_files, inc_dir_path, engine)
    else:
        print_info('Formal verification of mined assertions was skipped as per user request')
        directory_name = 'verif/' + engine + '/' + target
        make_directory(directory_name)
        Assertion_Results = {}
        for key in list(verify_assertion.keys()):
            Assertion_ = {}
            Assertion_['Status'] = 'Unknown'
            Assertion_['Vacuous'] = 'Unknown'
            Assertion_['Verified'] = 'Unknown'
            Assertion_['Triggered'] = 'Unknown'
            Assertion_['Assertion'] = verify_assertion[key]
            Assertion_Results[key] = Assertion_

            del Assertion_
    
    
    figlet_print('A Ranking')
    Assertion_Results = analyze(Assertion_Results, top_module, target, rank_assertion, cone, aggregate, engine, verilog_files, inc_dir_path)

    return verify_assertion
