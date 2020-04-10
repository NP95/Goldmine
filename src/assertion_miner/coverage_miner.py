import csv              # to read CSV file of the trace data
import pandas as pd     # to handle trace data efficiently# GoldMine Re-Implementation Code in Python
import math as mt       # to handle mathematical operations such as logarithm for Entroy 
                        # and Info Gain calculation
from formal_verifier import verify
from helper import figlet_print

def coverage_gain(feature_val_pair):

    return 1.0 / mt.pow(2, len(feature_val_pair))

def gain_added(addl_row_covered, total_rows_in_trace):

    return 1.0 * addl_row_covered / total_rows_in_trace

def check_sim_data(feature_val_pair, target_features_df):

    #To_Include = ' & '.join('(target_features_df.' + x[0] + ' == ' + str(x[1]) + ')' for x in feature_val_pair)
    To_Include = ' & '.join('(target_features_df[\'' + x[0] + '\'] == ' + str(x[1]) + ')' for x in feature_val_pair)
    return target_features_df[eval(To_Include)]

def gen_candidate(feature_val, target, target_features_df, feature_val_pair, assertion_c, gmin):
    
    # F = [(a, 0), (a, 1), (b, 0), ..., ()]

    for fea_val in feature_val:
        fea = fea_val[0]
        val = fea_val[1]
        feature_val_pair_aug = feature_val_pair[:]
        feature_val_pair_aug.append(fea_val)
        if coverage_gain(feature_val_pair_aug) >= gmin:
            derived_df = check_sim_data(feature_val_pair_aug, target_features_df)
            target_vals = derived_df[target].drop_duplicates().tolist()
            if len(target_vals) == 1 and target_vals[0] == 0:
                # assertion_c_ is of the format [[], ()]
                assertion_c_ = [feature_val_pair_aug, tuple([target, 0])]
                # assertion_c is of the format [[[], ()], [[], ()], ...]
                assertion_c.append(assertion_c_)
            elif len(target_vals) == 1 and target_vals[1] == 1:
                # assertion_c_ is of the format [[], ()]
                assertion_c_ = [feature_val_pair_aug, tuple([target, 1])]
                # assertion_c is of the format [[[], ()], [[], ()], ...]
                assertion_c.append(assertion_c_)
            elif len(target_vals) > 1:
                feature_val.remove(fea_val)
                gen_candidate(feature_val, target, target_features_df, feature_val_pair_aug, assertion_c, gmin)

    return assertion_c


def recalibrate_add(assertion_sol, assertion_s, assertion_c, target_features_df, total_rows_in_trace, gmin):

    # assertion_sol: indices of the row of the truth table already covered
    # assertion_s  : solution set of assertions
    # assertion_c  : new set of [[], ()]. See gen_candidate for this
    # target_features_df : the whole simulation trace data frame
    # gmin : minimum coverage gain

    for candidate in assertion_c:
        antecedent_feature = candidate[0]
        consequent_target = candidate[1]
        #To_Include = ' & '.join('(target_features_df.' + x[0] + ' == ' + str(x[1]) + ')' for x in antecedent_feature) + ' & ' + '(target_features_df.' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'
        To_Include = ' & '.join('(target_features_df[\'' + x[0] + '\'] == ' + str(x[1]) + ')' for x in antecedent_feature) + ' & ' + '(target_features_df.' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'
        dataframe_rows = target_features_df[eval(To_Include)]
        rows_covered = dataframe_rows.index.tolist()
        print 'Rows covered: ' + str(rows_covered)
        additional_rows_covered = list(set(rows_covered).difference(set(assertion_sol)))
        print 'Additional rows covered: ' + str(additional_rows_covered)
        if gain_added(len(additional_rows_covered), total_rows_in_trace) >= gmin:
            assertion_sol.extend(additional_rows_covered)
            assertion_s_ = induct_assertion(antecedent_feature, consequent_target)
            assertion_s.append(assertion_s_)

    return assertion_sol, assertion_s


def induct_assertion(antecedent_feature, consequent_target):
    
    assertion = ' & '.join('(' + x[0] + ' == ' + str(x[1]) + ')' for x in antecedent_feature)
    assertion = assertion + ' |-> ' + '(' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'

    return assertion


def print_assertion(assertions):

    count = 1
    for assertion in assertions:
        print str(count) + ': ' + assertion
        count = count + 1

    return

def construct_dframe(features, target, rows_):

    dframe = pd.DataFrame()

    for feature in features:
        dframe = pd.concat([dframe, pd.to_numeric(rows_[feature])], axis=1)
    
    dframe = pd.concat([dframe, pd.to_numeric(rows_[target])], axis=1)
    return dframe

def mine(features, target, rows_, CONFIG, top_module, clks, rsts, verilog_files, inc_dir_path):

    gmin = CONFIG['min_coverage']
    gthreshold = 0.01
    cthreshold = 0.99

    csv_dframe = construct_dframe(features, target, rows_)

    total_rows_in_trace = csv_dframe.shape[0]

    print 'Total rows in trace: ' + str(total_rows_in_trace)

    assertion_c = []
    assertion_s = []
    assertion_sol = []

    coverage = 0.0
   
    feature_val = []
    value = [0, 1]
    for fea in features:
        for val in value:
            feature_val.append((fea, val))

    while not (gmin < gthreshold or coverage > cthreshold):
        gen_candidate(feature_val, target, csv_dframe, [], assertion_c, gmin)
        
        print '$' * 10
        print assertion_c 
        print '$' * 10

        assertion_sol, assertion_s = recalibrate_add(assertion_sol, assertion_s, assertion_c, csv_dframe, total_rows_in_trace, gmin)
        
        print 'Total rows covered: ' + str(assertion_sol)

        coverage = 1.0 * len(assertion_sol) / total_rows_in_trace

        gmin = gmin / 2.0

        assertion_c = []

    print_assertion(assertion_s)

    return assertion_s
