import pprint as pp
import pandas as pd

def coverage_miner(features, target, target_feature_df, gmin, gthreshold, cthreshold):

    features = ['a', 'b', 'c']
    target = 'z'
    
    data = [[0,0,0,0], [0,1,1,0], [1,0,1,0], [1,1,0,1]]
    target_feature_df = pd.DataFrame(data, columns = ['a', 'b', 'c', 'z'])

    covAs = 0.0
    TRows = target_feature_df.shape[0]
    '''
    Final format for the returned assertion:

    [[antecedent_var_val_pair], consequent_var_val_pair]
    [ \
    [[('req2', 0)], ('gnt2', 0)],\
    [[('req1', 1), ('state', 0)], ('gnt2', 0)],\
    [[('req2', 1), ('req1', 0)], ('gnt2', 1)],\
    [[('req2', 1), ('state', 1)], ('gnt2', 1)]\
    ]

    '''
    As = []
    curr_covered_rows = []
    prev_covered_rows = []
    '''
    [('[1]state', 0), ('[1]state', 1), ('[2]req2', 0), ('[2]req2', 1), ('[2]req1', 0),..]
    '''
    F = create_var_val_pair(features)
    
    while True:
        if gmin < gthreshold or covAs > cthreshold:
            break
        else:
            # P: set of (feature_var, val) pair representing the antecedent of an assertion
            # F: set of (feature var, val) pair not in P
            # E: simulation trace. Here target_feature_df
            Ac = []
            Ac = gen_candidates(F, [], target, target_feature_df, Ac, gmin)
            print(Ac)
            As, curr_covered_rows = recalibrate_add(Ac, \
                    As, target_feature_df, prev_covered_rows, TRows, gmin)
            gmin = gmin / 2.0
            covAs = 1.0 * len(curr_covered_rows) / TRows
            print('New coverage: ', covAs)
            print('New gmin: ', gmin)
            del Ac
            prev_covered_rows = curr_covered_rows

    return As


def create_var_val_pair(features):
    F = []

    for var in features:
        F.append(tuple([var, 0]))
        F.append(tuple([var, 1]))

    return F

def gen_candidates(F, P, target, E, Ac, gmin):

    for fi in F:
        #fi = F.pop()
        if 1.0 * 1 / pow(2, len(list(set(P + [fi])))) >= gmin:
            P_ = list(set(P + [fi]))
            print('Current gain in gen_candidates: ', 1.0 * 1 / pow(2, len(P_)))
            check_consistency_, tval = check_consistency(E, P_, target)
            if check_consistency_:
                Ac.append([P_, tuple([target, tval])])
                print(Ac)
            else:
                newF = list(set(F) - set([fi]))
                gen_candidates(newF, P_, target, E, Ac, gmin)

    return Ac

def recalibrate_add(Ac, As, E, prev_covered_rows, TRows, gmin):
    
    for a in Ac:
        gain, addl_covered_rows = calc_gain(E, prev_covered_rows, TRows, a)
        if gain >= gmin:
            prev_covered_rows = list(set(prev_covered_rows + addl_covered_rows))
            As = As + a
    return As, prev_covered_rows

def calc_gain(E, prev_covered_rows, TRows, a):
    
    new_covered_rows = []
    E_local = E.copy(deep=True)
    P = a[0]
    for p in P:
        attribute = p[0]
        pval = p[1]
        E_local = E_local[E_local[attribute] == pval]

    new_covered_rows = E_local.index.tolist()

    addl_covered_rows = list(set(new_covered_rows) - set(prev_covered_rows))

    return 1.0 * len(addl_covered_rows) / TRows, addl_covered_rows

def check_consistency(E, P, target):
    E_local = E.copy(deep=True)
    print(P)
    for p in P:
        attribute = p[0]
        pval = p[1]
        E_local = E_local[E_local[attribute] == pval] 
    
    uniq_val = E_local[target].drop_duplicates().values.tolist()
    if len(uniq_val) > 1 or len(uniq_val) < 1:
        #print('More the one unique val')
        return False, -1
    else:
        #print('Uniq val: ', uniq_val[0])
        return True, uniq_val[0]
