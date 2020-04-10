import pprint as pp

from miner_helper import gain, entropy

def best_gain_decision_forest(features, target, target_features_df, feature_val_pair, assertion_component):

    '''
    Main best_gain_decision_forest algorithm implementation following Sam's thesis Algorithm 1
    '''
    
    if target_features_df.empty:
        return

    entropy_target = round(entropy(target_features_df, target), 5)

    if entropy_target == 0.0:
        target_mean = target_features_df[target].mean()
        #assertion_ = induct_assertion(feature_val_pair, tuple([target, int(target_mean)]))
        #assertion.append(assertion_)
        assertion_component.append([feature_val_pair, tuple([target, int(target_mean)])])
        return assertion_component

    feature_gain_best = -999999.0
    feature_info_gain = []

    for feature in features:
        feature_info_gain_ = round(gain(target_features_df, feature, entropy_target, target), 5)
        feature_info_gain.append(tuple([feature, feature_info_gain_]))
        if feature_gain_best < feature_info_gain_:
            feature_gain_best = feature_info_gain_
    
    #print 'feature_gain_best: ' + str(feature_gain_best) + '\nfeature_info_gain: ' + \
            str(feature_info_gain) + '\n'
    #print 'features: ' + str(features)
    #print '\n' * 2
    for fea_info_ele in feature_info_gain:
        if fea_info_ele[1] == feature_gain_best:
            #print 'Removing feature: ' + fea_info_ele[0]
            features_ = features[:]
            features_.remove(fea_info_ele[0])
            #print 'Features: ' + str(features) + '\n'
            target_feature_df_feature_best_0 = target_features_df[target_features_df[fea_info_ele[0]] == 0]
            target_feature_df_feature_best_1 = target_features_df[target_features_df[fea_info_ele[0]] == 1]
            
            #print 'Zero recursing'
            feature_val_pair_feature_best_0 = feature_val_pair[:]
            feature_val_pair_feature_best_0.append(tuple([fea_info_ele[0], 0]))
            best_gain_decision_forest(features_, target, target_feature_df_feature_best_0, \
                    feature_val_pair_feature_best_0, assertion_component)

            #print 'One recursing'
            feature_val_pair_feature_best_1 = feature_val_pair[:]
            feature_val_pair_feature_best_1.append(tuple([fea_info_ele[0], 1]))
            best_gain_decision_forest(features_, target, target_feature_df_feature_best_1, \
                    feature_val_pair_feature_best_1, assertion_component)


    return assertion_component
