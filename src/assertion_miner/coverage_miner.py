import pprint as pp

def coverage_miner(features, target, target_feature_df, gmin, gthreshold, cthreshold):

    print("Inside coverage miner")
    #print(features)
    #print(target)
    #print(target_feature_df.iloc[0])
    print(target_feature_df[target_feature_df['[1]state'] == 1])
    print(target_feature_df[target_feature_df['[1]state'] == 1].index.tolist())
    exit(0)

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
    P = []
    current_covered_rows = []
    previous_covered_rows = []
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
            gen_candidates(F, P, target, target_feature_df, Ac, gmin)
            print(Ac)
            exit(0)
            As, current_covered_rows = recalibrate_add(Ac, As, previous_covered_rows, gmin)
            gmin = gmin / 2.0
            del Ac


    return As


def create_var_val_pair(features):
    F = []

    for var in features:
        F.append(tuple([var, 0]))
        F.append(tuple([var, 1]))

    return F

def gen_candidates(F, P, target, E, Ac, gmin):

    #for fi in F:
    print(F)
    print(P)
    while F:
        fi = F.pop()
        if 1.0 * 1 / len(P + [fi]) >= gmin:
            P = P + [fi]
            if check_consistency(E, P, target, 0):
                print('True consistency check') 
                Ac = Ac + [P, list(tuple(target, 0))]
            elif check_consistency(E, P, target, 1):
                print('False consistency check') 
                Ac = Ac + [P, list(tuple(target, 1))]
            else:
                print('Recursing') 
                gen_candidates(list(set(F) - set(fi)), P, target, E, Ac, gmin)

    return

def recalibrate_add(Ac, As, previous_covered_rows, gmin):
    
    for a in Ac:
        if gain(As, a) >= gmin:
            As = As + a
    return

def gain(As, a):


    return False


def check_consistency(E, P, target, tval):
    E_local = E.copy(deep=True)
    for p in P:
        attribute = p[0]
        pval = p[1]
        E_local = E_local[E_local[attribute] == pval] 
    
    uniq_val = E_local[target].drop_duplicates().tolist()
    if len(uniq_val) > 1:
        return False
    else:
        if tval in uniq_val:
            return True
        else:
            return False
