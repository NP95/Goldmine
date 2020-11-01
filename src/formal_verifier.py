import os, sys
import regex as re
import multiprocessing as mps
from datetime import datetime as dt
import pprint as pp

from configuration import current_path, make_directory, change_directory, \
        change_parent_directory, remove_directory, remove_file
from helper import exec_command, print_warning, print_fail, fatal_error

NUMBER_OF_PROCESSES = mps.cpu_count()

def vacuous_assertions(Assertion_Results):
    # Assertions: Dictionary of Dictionary. First level dictionary has the Key as assertion number
    #             Second level key is the Assertion properties like Status etc  
    vassertions = []
    for Key in Assertion_Results.keys():
        if Assertion_Results[Key]['Status'] == 'Unknown':
            vassertions.append(Key)

    return len(vassertions)


def failed_assertions(Assertion_Results):
    # Assertions: Dictionary of Dictionary. First level dictionary has the Key as assertion number
    #             Second level key is the Assertion properties like Status etc  
    fassertions = []
    for Key in Assertion_Results.keys():
        if Assertion_Results[Key]['Status'] == False:
            fassertions.append(Key)

    return len(fassertions)

def passed_assertions(Assertion_Results):

    passertions= []
    for Key in Assertion_Results.keys():
        if Assertion_Results[Key]['Status'] == True:
            passertions.append(Key)

    return len(passertions)

def verify(target, Assertions, CONFIG, top_module, clks, rsts, verilog_files, inc_dir_path, engine):
    # CONFIG: It is a dictionary 
    # Assertions: It is a list
    
    Assertion_Results = {}

    yosys = CONFIG['yosys']
    if not os.path.isfile(yosys) or not os.access(yosys, os.X_OK):
        fatal_error('Cannot find valid YoSys executable at: ' + yosys)
        return                                                        
                                                                      
    if not len(Assertions):                                           
        fatal_error('No assertions to verify')                        
        return                                                        
                                                                      
    remove_directory('verif/' + engine + '/' + target)                
    # Sorting Assertion Keys by the Assertion number                  
    # Keys = sorted(Keys, key=lambda x: int(x[x.find('assertion') + len('assertion'):]))
                                                                          
    #assertion_per_core = []
    #
    #task_queue = mps.Queue()
    #done_queue = mps.Queue()
    
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
    #i = 0
    #for idx in range(NUMBER_OF_PROCESSES):
    #    assertion_per_core.append([])

    #for assertion in Assertions.keys():
    #    a_ = {}
    #    a_[assertion] = Assertions[assertion]
    #    assertion_per_core[i % NUMBER_OF_PROCESSES].append(a_)
    #    del a_
    #    i = i + 1
    #    if i == NUMBER_OF_PROCESSES:
    #        i = 0

    # assertion_per_core = [a for a in assertion_per_core if a]

    #if len(assertion_per_core) > 1:
        #Keys_List = []
        #for i in range(len(assertion_per_core)):
        #    List = Keys[:sum(assertion_per_core[: i + 1])]
        #    Keys_List.append(List)
        #    del List

    TASKS = [(create_verification_task, (target, assertion, i, CONFIG, top_module, \
                clks, rsts, verilog_files, inc_dir_path, engine)) \
                for i,assertion in enumerate(Assertions.items())]

    #for task in TASKS:
    #    task_queue.put(task)

    #for i in range(len(TASKS)):
    #    mps.Process(target=worker, args=(task_queue, done_queue)).start()
    
    p = mps.Pool(NUMBER_OF_PROCESSES)
    results = p.map(calculate, TASKS)
    
    # TODO
    # Result Aggregation Code is missing.
    # Look for Line no: 667 in Work/ECE_542/Mini_Project_1/src/run_taskid_3.py
    
    for result in results:
        if result[1]:
            Assertion_Results.update(result[0])

    #for i in range(len(TASKS)):
    #    task_queue.put('STOP')
   
    verified_assertion_keys = Assertion_Results.keys()
    for aname in Assertions.keys():
        asser = Assertions[aname]
        if aname in verified_assertion_keys:
            Assertion_Results[aname]['Assertion'] = asser
        else:
            print_warning('Assertion ' + aname + ': ' + asser + ' NOT verified')

    #pp.pprint(Assertion_Results)

    return Assertion_Results

def worker(inputQ, outputQ):
    for func, args in iter(inputQ.get, 'STOP'):
        result = calculate((func, args))
        outputQ.put(result)

def calculate(*val):
    func, args = val[0]
    result = func(*args)
    return result

def create_verification_task(target, assertion, i, CONFIG, top_module, clks, rsts, \
        verilog_files, inc_dir_path, engine):
   
    #parent_dir = os.getcwd()
    directory_name = 'verif/' + engine + '/' + target + '/assertion' + str(i)
    make_directory(directory_name)
    parent_dir = change_directory(directory_name)
    write_verilog(rsts, clks, verilog_files, top_module, assertion)
    write_sby(top_module)
    
    cmd_to_execute = verification_command(top_module, CONFIG)
    
    YOSYS_HOME = CONFIG['yosys_root']
    yosys_bin = os.path.join(YOSYS_HOME, 'bin')
    os.environ['PATH'] += os.pathsep + yosys_bin
    try:
        os.environ['LM_LICENSE_FILE'] += os.pathsep + CONFIG['LM_LICENSE_FILE']
    except:
        os.environ['LM_LICENSE_FILE'] = os.pathsep + CONFIG['LM_LICENSE_FILE']

    # TODO:
    # Subprocess to execute the ifv command
    start_verif = dt.now()
    data, err, retcode, mem_usage = exec_command(cmd_to_execute, 'PIPE', 'PIPE')
    end_verif = dt.now()

    cmd_file = open('yosys_command_' + target + '.sh', 'w')
    cmd_file.write('#!/bin/bash' + '\n\n')
    cmd_file.write('export PATH=' + yosys_bin + ':' + '$PATH\n\n')
    cmd_file.write('export LM_LICENSE_FILE=$LM_LICENSE_FILE:' + CONFIG['LM_LICENSE_FILE'] + '\n\n')
    cmd_file.write(cmd_to_execute)
    cmd_file.close()
    
    # FIXME
    # Make returns a tuple to put them in the Queue
    result_stat = read_results(top_module, assertion[0])

    #remove_directory(top_module + '_yosys')

    change_parent_directory(parent_dir)

    return result_stat

def verification_command(top_module, CONFIG):
    
    curr_path = current_path()

    yosys_executable = CONFIG['yosys']

    #ifv_cmd_to_execute = CONFIG['ifv'] + ' ' + curr_path + '/' + top_module + '_ifv.v' + ' ' \
    cmd_to_execute = 'sby -f ' + curr_path + '/' + top_module + '_yosys.sby > /dev/null'

    return cmd_to_execute

def write_verilog(rsts, clks, verilog_files, top_module, assertion):

    # clks: A dictionary where Key is the name of the clk pin and Vale is the clock polarity (i.e. posedge / negedge)
    # assertions: list of assertions that needs to be verified with the model

    model_file = current_path() + '/' + top_module + '_yosys.v'

    writing_module = False
    Successful = False

    top_module_pattern = re.compile(r'module\s+' + top_module)
    endmodule_pattern = re.compile(r'\s*endmodule')

    mcont = ''

    for verilog_file in verilog_files:
        vfile = open(verilog_file, 'r')
        if not vfile:
            msg = 'Cannot find the verilog file: ' + verilog_file[verilog_file.rfind('/') + 1:] + ' at location ' + verilog_file[:verilog_file.rfind('/')]
            print_fail(msg)
            raise Exception(msg)

        vline = vfile.readline()
        while vline:
            if re.search(top_module_pattern, vline):
                writing_module = True
            elif re.search(endmodule_pattern, vline) and writing_module:
                clk_string = ''
                for clk in clks.keys():
                    clk_string = clk_string + '@('
                    if clks[clk] == 1:
                        clk_string = clk_string + 'posedge '
                    else:
                        clk_string = clk_string + 'negedge '

                    clk_string = clk_string + clk + ')'

                aname = assertion[0]
                asser = assertion[1]
                mcont = mcont + 'property ' + aname + ';\n'
                mcont = mcont + '\t' + clk_string + '\n'
                mcont = mcont + '\t\t' + asser + ';\n'
                mcont = mcont + 'endproperty\n'
                mcont = mcont + '\n'
                mcont = mcont + 'assert_' + aname + ' : assert property (' + aname + ');\n'
                mcont = mcont + '\n'

            mcont =  mcont + vline
            vline = vfile.readline()

        writing_module = False
        Successful = True
        vfile.close()

    if not Successful:
        msg = 'Cannot find top module: ' + top_module
        print_fail(msg)
        raise Exception(msg)

    mfile = open(model_file, 'w')
    if not mfile:
        msg = 'Cannot create model verilog file for assertion verification: ' + model_file
        print_fail(msg)
        raise Exception(msg)
    
    mfile.write(mcont)
    mfile.close()

    del mcont 

    return

def write_tcl(top_module, rsts, clks):
    
    # rsts: A dictionary where Key is the name of the rst pin and Val is the reset polarity (i.e. active high / active low)
    # clks: A dictionary where Key is the name of the clk pin and Val is the clock polfor arity (i.e. posedge / negedge)
                                                                                          
    tcl_file = current_path() + '/'+ top_module + '_ifv.tcl'                              
                                                                                          
    tcont = ''                                                                            
                                                                                          
    for clk in clks.keys():                                                               
        tcont = tcont + 'clock -add ' + clk + '\n'                                        
    tcont = tcont + '\n'                                                                  
                                                                                          
    for rst in rsts.keys():                                                               
        tcont = tcont + 'force ' + rst + ' ' + rsts[rst] + '\n'
    tcont = tcont + '\n' 

    tcont = tcont + 'run 10\n'
    tcont = tcont + '\n'
                        
    tcont = tcont + 'init -load -current\n'
    tcont = tcont + '\n'
                        
    for rst in rsts.keys():
        tcont = tcont + 'constraint -add -pin ' + rst + ' ' + str(abs(int(rsts[rst]) - 1)) + ' -reset\n'
    tcont = tcont + '\n'
                        
    tcont = tcont + 'define debugmode=on\n'
    tcont = tcont + 'define effort=mid\n'
    tcont = tcont + 'prove\n'
    tcont = tcont + '\n'

    tcont = tcont + 'exit'

    tclf = open(tcl_file, 'w')
    if not tclf:
        fatal_error('Cannot create tcl file: ' + tcl_file)

    tclf.write(tcont)
    tclf.close()

    del tcont

    return

def write_sby(top_module):
    sby_file = current_path() + "/" + top_module + "_yosys.sby"

    with open(sby_file, "w") as f:
        f.write("[options]\n")
        f.write("mode prove\n")

        f.write("\n\n")

        f.write("[engines]\n")
        f.write("smtbmc")

        f.write("\n\n")

        f.write("[script]\n")
        f.write("read -formal " + top_module + "_yosys.v\n")
        f.write("prep -top " + top_module + "\n")

        f.write("\n\n")

        f.write("[files]\n")
        f.write(top_module + "_yosys.v\n")



def read_results(top_module, assertion_name):
    
    # Key of it is the assertion name and the Val will be the status of the assertion.
    # Thinking of making it a dictionary of dictionary, i.e. 
    # Assertion[Key1] = {Key11: Val11, Key12: Val12, Key13: Val13}
    Assertion = {}
    Verif_Success = False

    formal_verifier_log = current_path() + '/' + top_module + '_yosys/logfile.txt'
    flog = open(formal_verifier_log, 'r')
    if not flog:
        msg = 'Cannot find log file: ' + formal_verifier_log
        print_fail(msg)
        raise Exception(msg)

    # Keep reading one line at a time and then parse it for the information
    # Can read the whole file but may be too large to process
    #success_pattern = re.compile(r'formalbuild: Successfully completed')
    #assertion_pattern = re.compile(r'(assertion[0-9]+)\s:\s(Pass|Fail|Explored)\s(\([0-9]+\) )?-\s(Trigger):\s(Pass|Fail)') # checked via https://pythex.org
    #assertion_pattern = re.compile(r'(a[0-9]+)\s:\s(Pass|Fail|Explored)\s(\([0-9]+\) )?-\s(Trigger):\s(Pass|Fail)') # checked via https://pythex.org
    
    fline  = flog.readlines()[-1]

    #match_a = re.search(assertion_pattern, fline)
    #match_s = re.search(success_pattern, fline)

    if "ERROR" in fline or "DONE" not in fline:
        Verif_Success = False
        msg = 'Cannot Run YoSys. Please see: ' + formal_verifier_log
        print_fail(msg)
        raise Exception(msg)
    else:
        Verif_Success = True
        #assertion_name = match_a.group(1)
        #assertion_status = match_a.group(2)
        #assertion_trigger = match_a.group(5)

        #assertion_triggered = assertion_trigger == 'Pass'
        ## Antecedent could not be sensitized. Hence vacuous assertion
        #assertion_vacuous = assertion_trigger == 'Fail' 

        # FIXME
        assertion_triggered = True
        assertion_vacuous = False
        
        #if assertion_status == 'Pass':
        if "PASS" in fline:
            Assertion_ = {}
            Assertion_['Status'] = True
            Assertion_['Vacuous'] = assertion_vacuous
            Assertion_['Triggered'] = assertion_triggered
            Assertion[assertion_name] = Assertion_
            del Assertion_
            #elif assertion_status == 'Fail':
        elif "FAIL" in fline: 
            Assertion_ = {}
            Assertion_['Status'] = False
            Assertion_['Vacuous'] = assertion_vacuous
            Assertion_['Triggered'] = assertion_triggered
            Assertion[assertion_name] = Assertion_
            del Assertion_
            #elif assertion_status == 'Explored':
        else:
            print("UNEXPECTED YOSYS STATUS PLEASE INFORM DEVELOPER")
            Assertion_ = {}
            Assertion_['Status'] = 'Unknown'
            Assertion_['Vacuous'] = assertion_vacuous
            Assertion_['Triggered'] = assertion_triggered
            Assertion[assertion_name] = Assertion_
            del Assertion_

    flog.close()     
                     
    return (Assertion, Verif_Success)
