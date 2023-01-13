import pprint as pp

def prism(features, target, target_feature_df):
    
    # List of mined assertion
    assertion = []               

    # Create the target_feature dataset and finding unique values of the attribute set
    f_uniq_vals = {}
    for feature in features:
        f_uniq_vals[feature] = target_feature_df[feature].drop_duplicates().values.tolist()
    
    #print 'Features: ' + str(features)
    #print 'Target: ' + target
   
    # Finding unique values of target variable (different classification in the terminology of the Prism algorithm
    t_uniq_vals = target_feature_df[target].drop_duplicates().values.tolist()
    
    ## STEP 6: Rule for one classification have been induced. Trainig data set restored to its initial
    ## STEP 6: state and the algorithm is applied again to induce a set of rules covering the next
    ## STEP 6: classification
    for t_uniq_val in t_uniq_vals:
        target_feature_df_rt = target_feature_df.copy()
        #features_rt = features[:]
        ## STEP 5: Repeat STEPS1-4 untill all instances of ddelta_n have been removed
        while (t_uniq_val in target_feature_df_rt[target].drop_duplicates().tolist()):
            # To collect the attributes that contributes maximum information
            # to the target classification
            antecedent_feature = []
            training_data = target_feature_df_rt.copy()
            features_rt = features[:]
            # print training_data

            # STEP 3: Repeat STEP 1 and STEP 2 for this subset until it contains only instances
            # STEP 3: of class delta_n.
            #print 'Feature_RT at begining of entering inner while loop: ' + str(features_rt)
            old_size = -1
            new_size = -1
            while len(training_data[target].drop_duplicates().tolist()) > 1:
                #old_size = training_data.shape[0]
                #if old_size == new_size:
                #    print training_data
                #    exit(0)

                best_feature = ''
                best_feature_val = -2
                # To find the best possible feature-value pair to split the classification 
                # class. 
                b_prob_feature_class = 0.0
                #print features_rt
                
                if not features_rt:
                    antecedent_feature = []
                    break

                ## STEP 1:  Calculate probabiluty of occurence of p(delta_n | alpha_x) and find best alpha_x
                for feature in features_rt:
                    f_uniq_val = f_uniq_vals[feature]
                    for val in f_uniq_val:
                        #print 'feature: ' + feature + ' val: ' + str(val)
                        feature_val_count = training_data[training_data[feature] == val].shape[0]
                        feature_class_val_count = training_data[(training_data[feature] == val) \
                                & (training_data[target] == t_uniq_val)].shape[0]
                        # print 'Feature: ' + feature + ' Val: ' + str(val) + ' feature_val_count: '\
                                    #+ str(feature_val_count) + \
                        #       ' feature_class_val_count: ' + str(feature_class_val_count)
                        try:
                            prob_feature_class = feature_class_val_count * 1.0 / feature_val_count
                            #print 'Feature: ' + feature + ' Val: ' + str(val) + ' feature_val_count: ' + \
                            #        str(feature_val_count) + ' feature_class_val_count: ' + \
                            #        str(feature_class_val_count)
                            #print 'Training data size: ' + str(training_data.shape[0])
                            #print training_data
                        except ZeroDivisionError:
                            #print 'Feature: ' + feature + ' Val: ' + str(val) + ' feature_val_count: ' + \
                            #        str(feature_val_count) + ' feature_class_val_count: ' + \
                            #        str(feature_class_val_count)
                            #print 'Training data size: ' + str(training_data.shape[0])
                            #print training_data
                            continue
                        if prob_feature_class > b_prob_feature_class:
                            #print 'Best feature so far: ' + feature + ' val: ' + str(val) + \
                            #        ' prev best: ' + str(b_prob_feature_class) + \
                            #        ' cuurent: ' + str(prob_feature_class)
                            #print 'Best feature val so far: ' + str(val)
                            #print 'Best prob so far: ' + str(prob_feature_class)
                            b_prob_feature_class = prob_feature_class
                            best_feature = feature
                            best_feature_val = val
                ## STEP: Best alpha_x is a rule feature 
                antecedent_feature.append(tuple([best_feature, best_feature_val]))
                #print 'Antecedent Feature: ' + str(antecedent_feature)
                #print '#' * 20 + '\n'
                #print best_feature
                features_rt.remove(best_feature)
                #print 'Feature_RT within inner while loop after removal: ' + str(features_rt)
                #print 'Antecedent Feature: ' + str(antecedent_feature)
                #print 'After removing feature: ' + str(features_rt)

                ## STEP 2: Create a subset of the training data set comprising all the instances
                ## STEP 2: which contain selected alpha_x
                training_data = training_data[training_data[best_feature] == best_feature_val]
                #print 'Unique values of target in tarining data: ' + \
                #        str(training_data[target].drop_duplicates().tolist())
                #print 'New training data size: ' + str(training_data.shape[0])
                #new_size = training_data.shape[0]
                #print training_data
    

            #assertion_ = induct_assertion(antecedent_feature, tuple([target, t_uniq_val]))

            ## STEP 3: The induced rule is a conjection of all the atribute-value (alpha_x) pairs used
            ## STEP 3: in creating the homogeneous subset
            if not antecedent_feature:
                break
            assertion.append([antecedent_feature, tuple([target, t_uniq_val])])

            ## STEP 4: Remove all instances covered by this rule from the training data set
            To_Remove = ' & '.join('(target_feature_df_rt[\'' + x[0] + '\'] == ' + \
                    str(x[1]) + ')' for x in antecedent_feature)
            #To_Remove = To_Remove + ' & (target_feature_df_rt[\'' + target + '\'] == ' + str(t_uniq_val) + ')'
            target_feature_df_rt = target_feature_df_rt.drop(target_feature_df_rt[eval(To_Remove)].index)
            #print target_feature_df_rt

    return assertion
