import csv
import pandas as pd
import pprint as pp
import math as mt

from progressbar import ProgressBar, Percentage, ETA, Bar
import regex as re


from helper import print_info

def construct_dframe(features, target, rows_):

    empty_frame = pd.DataFrame()
    dframe = pd.DataFrame()
    print_info('Constructing target specific data frame for mining..')
    # Progress Bar Widget for the trace data processing
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)

    for feature in pbar(features):
        try:
            dframe = pd.concat([dframe, rows_[feature]], axis=1)
        except KeyError:
            return empty_frame, feature
    try: 
        dframe = pd.concat([dframe, rows_[target]], axis=1)
    except KeyError:
        return empty_frame, target
    return dframe, ''

def induct_assertion(antecedent_feature, consequent_target):
    
    antecedent_dict = {}
    
    literal_pattern = re.compile(r'(\[[0-9]*\])?([A-Za-z0-9_\[\]]+)')

    for x in antecedent_feature:
        match_a = re.search(literal_pattern, x[0])
        if match_a:
            try:
                delay = int(match_a.group(1).replace('[', '').replace(']',''))
            except AttributeError:
                delay = 0
            literal = match_a.group(2)
            if delay not in antecedent_dict.keys():
                antecedent_dict[delay] = [tuple([literal, x[1]])]
            else:
                antecedent_dict[delay].append(tuple([literal, x[1]]))
        
    ordered_antecedent = sorted(antecedent_dict.items(), key=lambda t: t[0], reverse=True)
    
    max_cycle = max(antecedent_dict.keys())
    max_cycle_considered = 0

    antecedent = ''
    for term in ordered_antecedent:
        curr_cycle_delay = max_cycle - term[0]
        prop = term[1]
        if curr_cycle_delay == 0:
            propostion = '(' + ' & '.join(x[0] + ' == ' + str(x[1]) for x in prop) + ')'
        else:
            propostion = ' ##' + str(curr_cycle_delay) + ' (' + ' & '.join(x[0] + \
                    ' == ' + str(x[1]) for x in prop) + ')'

        antecedent = antecedent + propostion
        max_cycle_considered = curr_cycle_delay

    assertion = ''
    if (max_cycle - max_cycle_considered) == 0:
        assertion = antecedent + ' |-> (' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'
    elif (max_cycle - max_cycle_considered) == 1:
        assertion = antecedent + ' |=> ' + '(' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'
    else:
        assertion = antecedent + ' |=> ##' + str(max_cycle - max_cycle_considered - 1) + \
                ' (' + consequent_target[0] + ' == ' + str(consequent_target[1]) + ')'


    return assertion

def print_assertion(assertions):

    count = 1
    for assertion in assertions:
        print str(count) + ': ' + assertion
        count = count + 1

    return

def log2(x):
    '''
    Calculating log base 2 using standard log function
    try-except block is needed if received x == 0
    '''
    try:
        return mt.log(x, 2)
    except ValueError:
        return 0.0

def entropy(target_features_df, target):
        
    '''
    Calculating standard entropy based on Sam's thesis Eq 2.1
    '''

    target_feature_df_size = target_features_df.shape[0]
    target_zero_df_size = target_features_df[target_features_df[target] == 0].shape[0]
    target_one_df_size = target_features_df[target_features_df[target] == 1].shape[0]
    
    # This is needed to be done otherwise Python wont consider Float and eventually log calculation will catch an exception
    # will return Zero.
    try:
        p0 = 1.0 * target_zero_df_size / target_feature_df_size
    except ZeroDivisionError:
        p0 = 0.0

    try:
        p1 = 1.0 * target_one_df_size / target_feature_df_size
    except ZeroDivisionError:
        p1 = 0.0

    entropy_target = - p0 * log2(p0) - p1 * log2(p1)
    
    return entropy_target

def gain(target_features_df, feature, entropy_target, target):
    
    '''
    Calculating gain from a feature split based on Sam's thesis Eq 2.2
    '''

    feature_gain = 0.0
    target_feature_df_size = target_features_df.shape[0]
    
    feature_zero_df = target_features_df[target_features_df[feature] == 0]
    feature_one_df = target_features_df[target_features_df[feature] == 1]

    feature_zero_df_size = feature_zero_df.shape[0]
    feature_one_df_size = feature_one_df.shape[0]
    
    feature_gain = entropy_target - 1.0 * feature_zero_df_size / target_feature_df_size * entropy(feature_zero_df, target) - 1.0 * feature_one_df_size / target_feature_df_size * entropy(feature_one_df, target)
    
    return feature_gain

def set_containment(assertion_component):
    
    assertion_component_sorted = sorted(assertion_component, key=lambda x: len(x[0]))
    consequent_index_zero = [idx for idx in range(len(assertion_component_sorted)) \
            if assertion_component_sorted[idx][1][1] == 0]
    consequent_index_one =  [idx for idx in range(len(assertion_component_sorted)) \
            if assertion_component_sorted[idx][1][1] == 1]
    
    #print assertion_component_sorted
    #print consequent_index_zero
    #print consequent_index_one

    to_be_removed = []

    for idx in range(len(consequent_index_zero) - 1):
        idx1 = consequent_index_zero[idx]
        if idx1 not in to_be_removed:
            for idx_ in range(idx + 1, len(consequent_index_zero)):
                idx2 = consequent_index_zero[idx_]
                if idx2 not in to_be_removed:
                    antecedent_A = assertion_component_sorted[idx1][0]
                    antecedent_B = assertion_component_sorted[idx2][0]
                    if not set(antecedent_A).difference(set(antecedent_B)):
                        to_be_removed.append(idx2)

    for idx in range(len(consequent_index_one) - 1):
        idx1 = consequent_index_one[idx]
        if idx1 not in to_be_removed:
            for idx_ in range(idx1 + 1, len(consequent_index_one)):
                idx2 = consequent_index_one[idx_]
                if idx2 not in to_be_removed:
                    antecedent_A = assertion_component_sorted[idx1][0]
                    antecedent_B = assertion_component_sorted[idx2][0]
                    if not set(antecedent_A).difference(set(antecedent_B)):
                        to_be_removed.append(idx2)

    #One problem is when you delete an item, the indices of every item after 
    #it also changes. One strategy then is to delete the elements in descending 
    #order, i.e. delete the largest indices first. That way, you do not change 
    #the indices of the smaller indices, so you can still delete them. We 
    #can sort them in reverse order like this:

    for i in sorted(to_be_removed, reverse=True):
        del assertion_component_sorted[i]

    print_info('Set containment removed: ' + str(round(100.0 * len(to_be_removed)/len(assertion_component) \
            , 2)) + '% of mined assertions before formal check')
    return assertion_component_sorted 
