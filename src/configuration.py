import os, errno, shutil
import sys
import platform
from collections import OrderedDict as ODict
from datetime import datetime as dt

from helper import fatal_error, print_info, print_warning, printTable, get_file_names_from_loc

def remove_file(file_path):

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError, e:
            print_info("Error: %s - %s." % (e.file_path, e.strerror))
    else:
        print_info('Cannot find file: ' + file_path)

    return

def current_path():

    return os.getcwd()

def set_root_dir(current_dir):
    if not os.path.isdir(current_dir):
        fatal_error('Cannot open non-existent directory: ' + current_dir)

    root_dir = current_dir

    return current_dir

def make_directory(dir_path):

    current_path = os.getcwd()
    absolute_directory_path = ''
    
    if current_path in dir_path:
        absolute_directory_path = dir_path
    else:
        absolute_directory_path = current_path + '/' + dir_path

    if not os.path.exists(absolute_directory_path):
        try:
            os.makedirs(absolute_directory_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    return

def change_parent_directory(dir_path):
    if dir_path in os.path.dirname(os.getcwd()):
        os.chdir(dir_path)
    else:
        fatal_error('Caonnot change to non-existent parent direcotyr: ' + dr_path)

    return

def change_directory(dir_path):

    current_path = os.getcwd()
    absolute_directory_path = ''

    if current_path in dir_path:
        absolute_directory_path = dir_path
    else:
        absolute_directory_path = current_path + '/' + dir_path

    if not os.path.isdir(absolute_directory_path):
        fatal_error('Cannot change to non-existent directory: ' + absolute_directory_path) 

    os.chdir(absolute_directory_path)

    return current_path

def remove_directory(dir_path):

    current_path = os.getcwd()
    absolute_directory_path = ''

    if current_path in dir_path:
        absolute_directory_path = dir_path
    else:
        absolute_directory_path = current_path + '/' + dir_path

    if not os.path.exists(absolute_directory_path):
        print_warning('Cannot remove a non-existent directory: ' + absolute_directory_path)
        return

    try:
        shutil.rmtree(absolute_directory_path)
    except OSError, e:
        print_warning('%s - %s.' % (e.filename, e.strerror))

    return

def set_log_file_path(path_to_log):

    log_file_path = path_to_log + '/goldmine.log'

    return log_file_path

def open_log_file(log_file_path):

    log_file = open(log_file_path, 'w')

    return log_file

def close_log_file(log_file):

    if (log_file):
        log_file.close()
    
    return

def set_config_file_path(path_to_config, vcd_stat, is_comb):
    # vcd_stat: True if a VCD file is specified in the command line

    SEP = '::'
    CONFIG = {}
    MIN_SIM_CYCLES = 100
    MAX_SIM_CYCLES = 1000000

    if not os.path.exists(path_to_config):
        fatal_error('Cannot open configuration file: ' + path_to_config)

    cfile = open(path_to_config, 'r')
    clines = cfile.readlines()
    cfile.close()

    for cline in clines:
        # Do not parse strings starting with #. They are comments in the configuration file
        if cline[0] == '#':
            continue
        # Not a valid configuration line. Do not parse it
        if SEP not in cline:
            continue

        line = cline.lstrip().rstrip()
        Key = line[:line.find(SEP)]
        Val = line[line.find(SEP) + len(SEP) :]
        if Key == 'num_cycles':
            #CONFIG[Key] = max(1, int(Val))
            # NOTE: Due to Python's range semantics, to calculate assertions of the temporal length
            #       as specified by the user, the CONFIG must be 1 higher than that
            CONFIG[Key] = int(Val) + 1 if not is_comb else 1
        elif Key == 'max_sim_cycles':
            CONFIG[Key] = min(MAX_SIM_CYCLES, max(MIN_SIM_CYCLES, int(Val)))
        elif Key == 'num_propositions':
            CONFIG[Key] = max(1, int(Val))
        elif Key == 'num_partitions':
            if Val == '+':
                Val = sys.maxint 
            CONFIG[Key] = max(1, int(Val))
        elif Key == 'num_counterexamples':
            CONFIG[Key] = int(Val)
        elif Key == 'min_coverage':
            CONFIG[Key] = min(1.0, max(0.0, float(Val)))
        elif Key == 'cadence_license' or Key == 'synopsys_license':
            if 'LM_LICENSE_FILE' in CONFIG.keys():
                CONFIG['LM_LICENSE_FILE'] = CONFIG['LM_LICENSE_FILE'] + os.pathsep + Val
            else:
                CONFIG['LM_LICENSE_FILE'] = Val
        else:
            CONFIG[Key] = Val

    platform_type = platform.machine()
    
    vcs_exe = ''
    ifv_exe = ''
    iverilog_exe = ''
    # Set to True if VCS is not available
    vcs_stat = False


    if platform_type == 'x86_64':
        vcs_exe = CONFIG['vcs_home'] + '/amd64/bin/vcs'
        ifv_exe = CONFIG['ifv_root'] + '/tools/bin/64bit/ifv'
        iverilog_exe = CONFIG['iverilog_home'] + '/iverilog'
    else:
    # a X86 machine can be i386 or i686. Hence just kept as else
        vcs_exe = CONFIG['vcs_home'] + '/bin/vcs'
        ifv_exe = CONFIG['ifv_root'] + '/tools/bin/ifv'
        iverilog_exe = CONFIG['iverilog_home'] + '/iverilog'

        

    if not os.path.isfile(vcs_exe) or not os.access(vcs_exe, os.X_OK):
        CONFIG['vcs'] = ''
        print_warning('VCS Executable Not Found.')
        vcs_stat = True
    else:
        CONFIG['vcs'] = vcs_exe

    if not os.path.isfile(ifv_exe) or not os.access(ifv_exe, os.X_OK):
        CONFIG['ifv'] = ''
        print_warning('IFV Executable Not Found. Assertion Verification won\'t be possible.')
    else:
        CONFIG['ifv'] = ifv_exe

    if not os.path.isfile(iverilog_exe) or not os.access(iverilog_exe, os.X_OK):
        CONFIG['iverilog'] = ''
        if vcs_stat:
            if vcd_stat:
                print_info('Neither VCS nor IVerilog found. Supplied VCD will be used for mining.')
            else:
                fatal_error('Neither VCS nor IVerilog found. No VCD suppiled. Assertion generation not possible')
    else:
        CONFIG['iverilog'] = iverilog_exe
        
    return CONFIG

def summarize_report(top_moddule, targets, Resource_Stat, engine):
    
    Report = {}

    curr_path = current_path()
    summary_file = curr_path + '/' + top_moddule + '_' + engine + '_assertion_summary.txt'

    root_dir = curr_path + '/verif/' + engine 
    
    for target in targets:
        gfile = get_file_names_from_loc(root_dir + '/' + target, '*.gold')
        if not gfile:
            Report[target] = ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']
            continue

        ghandle = open(gfile[0], 'r')
        gcont = ghandle.readlines()
        ghandle.close()

        mine_index = [idx for idx in range(len(gcont)) if 'Total number of mined assertions' in gcont[idx]]
        pass_index = [idx for idx in range(len(gcont)) if 'Total number of passed assertions' in gcont[idx]]
        fail_index = [idx for idx in range(len(gcont)) if 'Total number of failed assertions' in gcont[idx]]
        vac_index = [idx for idx in range(len(gcont)) if 'Total number of vacuous / unexplored assertions' \
                in gcont[idx]]

        hit_index = [idx for idx in range(len(gcont)) if 'Hit rate' in gcont[idx]]
        miss_index = [idx for idx in range(len(gcont)) if 'Miss rate' in gcont[idx]]
        
        t_assertions = gcont[mine_index[0]][gcont[mine_index[0]].find(':') + 1:].lstrip().rstrip()
        p_assertions = gcont[pass_index[0]][gcont[pass_index[0]].find(':') + 1:].lstrip().rstrip()
        f_assertions = gcont[fail_index[0]][gcont[fail_index[0]].find(':') + 1:].lstrip().rstrip()
        v_assertions = gcont[vac_index[0]][gcont[vac_index[0]].find(':') + 1:].lstrip().rstrip()
        h_index = gcont[hit_index[0]][gcont[hit_index[0]].find(':') + 1:].lstrip().rstrip()
        m_index = gcont[miss_index[0]][gcont[miss_index[0]].find(':') + 1:].lstrip().rstrip()

        
        Report[target] = [t_assertions, p_assertions, f_assertions, v_assertions, round(float(h_index), 4), \
                round(float(m_index), 4)]
    
    Report = ODict(sorted(Report.items(), key=lambda t: t[0]))
    tableAssertionContent = printTable(Report, ['Target', 'Total', 'Passed', \
            'Failed', 'Vacuous', 'Hit', 'Miss'])
    tableResourceContent = printTable(Resource_Stat, ['Phase', 'Time (in [H]H:MM:SS:UUUUUU)', \
            'Memory (in MB)'])

    report_date_string = 'Assertion report generated on: ' + str(dt.now().strftime('%d-%b-%Y %I:%M:%S %p'))
    report_assertion_string = 'Assertion summary report for design: ' + top_moddule
    report_resource_string = 'Resource usage summary report for the desing: ' + top_moddule

    
    shandle = open(summary_file, 'w')
    shandle.write(report_date_string + '\n\n')
    shandle.write(report_assertion_string + '\n')
    shandle.write('#' * len(report_assertion_string) + '\n\n')
    shandle.write(tableAssertionContent)
    shandle.write('\n\n')
    shandle.write(report_resource_string + '\n')
    shandle.write('#' * len(report_resource_string) + '\n\n')
    shandle.write(tableResourceContent)
    shandle.close()

    return
