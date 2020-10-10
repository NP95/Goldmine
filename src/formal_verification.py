import os
import regex as re
import multiprocessing as mps
from datetime import datetime as dt
import pprint as pp

from configuration import current_path, make_directory, change_diretory, \
        change_parent_directory, remove_directory, remove_file
from helper import exec_command, print_warning, fatal_error

NUMBER_OF_PROCESSES = mps.cpu_count()

def verify(target, Assertions, CONFIG, top_module, clks, rsts, verilog_files, inc_dir_path, engine):
    # CONFIG: It is a dictionary 
    # Assertions: It is a list
    
    Assertion_Results = {}

    ifv = CONFIG['ifv']
    if not os.path.isfile(ifv) or not os.access(ifv, os.X_OK):
        fatal_error('Cannot find valid IFV executable at: ' + ifv)
        return
    
    if not len(Assertions):
        fatal_error('No assertions to verify')
        return

    remove_directory('verif/' + engine + '/' + target)
    # Sorting Assertion Keys by the Assertion number
    # Keys = sorted(Keys, key=lambda x: int(x[x.find('assertion') + len('assertion'):]))

    assertion_per_core = []
    
    task_queue = mps.Queue()
    done_queue = mps.Queue()
    
    # Logic to split the assertions to core for verification #

    # Logic 1 #
    ###########
    #quotient = total_num_assertions / NUMBER_OF_PROCESSES
    #remainder = total_num_assertions % NUMBER_OF_PROCESSES
    #if remainder == 0:
    #    assertion_per_core = [quotient] * NUMBER_OF_PROCESSES
    #else:
    #    assertion_per_core = [quotient] * (NUMBER_OF_PROCESSES - 1)
    #    assertion_per_core.append(remainder)

    # Logic 2 #
    ###########
    i = 0
    for idx in range(NUMBER_OF_PROCESSES):
        assertion_per_core.append([])

    for assertion in Assertions.keys():
        a_ = {}
        a_[assertion] = Assertions[assertion]
        assertion_per_core[i % NUMBER_OF_PROCESSES].append(a_)
        del a_
        i = i + 1
        if i == NUMBER_OF_PROCESSES:
            i = 0

    # assertion_per_core = [a for a in assertion_per_core if a]

    if len(assertion_per_core) > 1:
        #Keys_List = []
        #for i in range(len(assertion_per_core)):
        #    List = Keys[:sum(assertion_per_core[: i + 1])]
        #    Keys_List.append(List)
        #    del List

        TASKS = [(create_verification_task, (target, assertion_per_core[i], i, CONFIG, top_module, \
                clks, rsts, verilog_files, inc_dir_path, engine)) \
                for i in range(NUMBER_OF_PROCESSES) if assertion_per_core[i]]

    for task in TASKS:
        task_queue.put(task)

    for i in range(len(TASKS)):
        mps.Process(target=worker, args=(task_queue, done_queue)).start()
    
    
    # TODO
    # Result Aggregation Code is missing.
    # Look for Line no: 667 in Work/ECE_542/Mini_Project_1/src/run_taskid_3.py
    
    for i in range(len(TASKS)):
        result = done_queue.get()
        if result[1]:
            Assertion_Results.update(result[0])

    for i in range(len(TASKS)):
        task_queue.put('STOP')
   
    verified_assertion_keys = Assertion_Results.keys()
    for aname in Assertions.keys():
        asser = Assertions[aname]
        if aname in verified_assertion_keys:
            Assertion_Results[aname]['Assertion'] = asser
        else:
            print_warning('Assertion ' + aname + ': ' + asser + ' NOT verified')

    #pp.pprint(Assertion_Results)

    return Assertion_Results

