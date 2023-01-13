import pprint as pp

def decision_tree(features, target, target_feature_df, feature_val_pair, assertion_component):
    
    '''
    Main decision_tree algorithm implementation. From TCAD 2013 paper "Mining Hardware Assertions With Guidenace From Static Analysis"

    '''
    #print 'Feature_val_pair: ' + str(feature_val_pair)
    # Target variable mean calculation
    target_mean = target_feature_df[target].mean()
    # Target variable error calculation (mean(target_val - target_mean))
    target_error = target_feature_df[target].apply(lambda x: abs(x - target_mean)).mean()
    # If target mean is zero, mine assertion
    #print 'Target Error: ' + str(target_error)
    #print 'Features_val_pair: ' + str(feature_val_pair)
    #print 'Features: ' + str(features)
    #print '\n' *2
    if target_error == 0.0:
        # print feature_val_pair
        # assertion_ = induct_assertion(feature_val_pair, tuple([target, int(target_mean)]))
        # assertion.append(assertion_)
        assertion_component.append([feature_val_pair, tuple([target, int(target_mean)])])
        return assertion_component
    # Else find the beast feature variable to split
    feature_best = ''
    feature_gain_best = -999999.0

    for feature in features:
        # Find all rows where feature variable is 0
        dataframe_feature_0 = target_feature_df[target_feature_df[feature] == 0]
        #if dataframe_feature_0.empty:
        #    print 'Empty'
        # Find all rows where feature variable is 1
        dataframe_feature_1 = target_feature_df[target_feature_df[feature] == 1]
        
        target_mean_feature_0 = dataframe_feature_0[target].mean()
        #print 'Target mean feature_0: ' + str(target_mean_feature_0)
        target_error_feature_0 = dataframe_feature_0[target].apply(lambda x: \
                    abs(x - target_mean_feature_0)).mean()
        #print 'Target error feature_0: ' + str(target_error_feature_0)

        target_mean_feature_1 = dataframe_feature_1[target].mean()
        #print 'Target mean feature_1: ' + str(target_mean_feature_1)
        target_error_feature_1 = dataframe_feature_1[target].apply(lambda x: \
                abs(x - target_mean_feature_1)).mean()
        #print 'Target error feature_1: ' + str(target_error_feature_1)

        feature_gain = target_error - target_error_feature_0 - target_error_feature_1

        #print 'Feature: ' + feature + ' Gain: ' + str(feature_gain)

        if feature_gain > feature_gain_best:
            feature_best = feature
            feature_gain_best = feature_gain
   
    if not feature_best:
        return

    #print 'Best feature found: ' + str(feature_best)
    #print '#' *2

    target_feature_df_feature_best_0 = target_feature_df[target_feature_df[feature_best] == 0]
    target_feature_df_feature_best_1 = target_feature_df[target_feature_df[feature_best] == 1]
    
    # Call recursively decision_tree algorithm
    features.remove(feature_best)

    feature_val_pair_feature_best_0 = feature_val_pair[:]
    feature_val_pair_feature_best_0.append(tuple([feature_best, 0]))
    
    decision_tree(features, target, target_feature_df_feature_best_0, \
            feature_val_pair_feature_best_0, assertion_component)

    feature_val_pair_feature_best_1 = feature_val_pair[:]
    feature_val_pair_feature_best_1.append(tuple([feature_best, 1]))

    decision_tree(features, target, target_feature_df_feature_best_1, \
            feature_val_pair_feature_best_1, assertion_component)

    return assertion_component
