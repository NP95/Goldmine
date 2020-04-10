import os
import sys, fnmatch
from pyfiglet import figlet_format, Figlet
from termcolor import cprint
import pickle
from datetime import datetime as dt
from time import sleep
from threading import Thread, Event
from Queue import Queue
from subprocess import Popen, PIPE
import operator as op
import logging
import regex as re

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKBLACK  = "\033[90m"
    OKBCKGRD = "\033[47m"
    OKGREEN = '\033[92m'
    OKTEAL = '\033[96m'
    TRY = '\033[97m'
    WARNING = '\033[93m'
    BCKGRD_WARNING = "\033[93m"
    FAIL = '\033[91m'
    BCKGRD_FAIL = "\033[93m"
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])

def print_warning(print_string):
    try:
        modulename = sys._getframe(2).f_code.co_filename
        funcname = sys._getframe(2).f_code.co_name
    except ValueError:
        modulename = sys._getframe(1).f_code.co_filename
        funcname = sys._getframe(1).f_code.co_name
    warning = {'modulename': os.path.basename(modulename),
               'funcname': funcname
               }
    logger = logging.getLogger('goldmine')
    logger.warning(print_string, extra=warning)
    print(bcolors.BOLD  + bcolors.OKBLACK + bcolors.BCKGRD_WARNING + "[WARN]--> " + print_string + bcolors.ENDC + " ") 

def print_fail(print_string):
    try:
        modulename = sys._getframe(2).f_code.co_filename
        funcname = sys._getframe(2).f_code.co_name
    except ValueError:
        modulename = sys._getframe(1).f_code.co_filename
        funcname = sys._getframe(1).f_code.co_name
    fail = {'modulename': os.path.basename(modulename),
            'funcname': funcname.lstrip(' ').rstrip(' ')
            }
    logger = logging.getLogger('goldmine')
    logger.critical(print_string, extra=fail)
    print(bcolors.BOLD  + bcolors.OKBLACK + bcolors.FAIL +  "[FAIL]--> " + print_string + bcolors.ENDC + " ") 


def print_info(print_string):
    try:
        modulename = sys._getframe(2).f_code.co_filename
        funcname = sys._getframe(2).f_code.co_name
    except ValueError:
        modulename = sys._getframe(1).f_code.co_filename
        funcname = sys._getframe(1).f_code.co_name
    info = {'modulename': os.path.basename(modulename),
            'funcname': funcname
            }
    logger = logging.getLogger('goldmine')
    logger.info(print_string, extra=info)
    print(bcolors.BOLD + bcolors.OKTEAL + bcolors.OKGREEN + "[INFO]--> " + print_string + bcolors.ENDC + " ")

def print_prefix(string):
    #OKBLACK  = u"\u001b[30;1m"
    #OKBCKGRD = u"\u001b[0m"
    return bcolors.BOLD  + bcolors.OKBLACK + bcolors.OKBCKGRD + "[" + string + "]-->"  + bcolors.ENDC + " "

def print_line_stars():
	try:
		size = getTerminalSize()
	except:
		size = [80, 40]
	string = "".center(size[0], "*")
	print(string)

def print_current_time():
    print_line_stars()
    print(print_prefix("TIME") + dt.now().strftime('%Y-%m-%d %H:%M:%S'))
    print_line_stars()

def print_newline():
    print('\n')
    return

def print_start():
   print_line_stars()
   figlet_print("Start")
   print_current_time()
   print_line_stars()


def load_pickle(file_path):
    if (os.path.exists(file_path)):
         with open(file_path, "rb") as file:
            data = pickle.load(file)
    else:
        return None
    return data

def save_pickle(file_path, data):
    with open(file_path, "w") as file:
         pickle.dump(data, file)


class parser_types:
    LST = "<type 'list'>"
    INT = "<type 'int'>"
    STR = "<type 'str'>"
    SINGLE_OPS = {'NOT': "~", \
                'ULNOT': "~", \
                'UNOT': "~"
                }
                    
    OPERATORS =  {'PLUS': "+",
            'MINUS': "-",
	    'POWER': "NOT_SUPPORTED",
	    'TIMES': "*",
	    'DIVIDE': "/",
            'Uand': "&",
	    'MOD': "NOT_SUPPORTED",
	    'OR': "|", 
	    'NOR': "@", 
	    'AND': "&", 
	    'NAND': "$", 
	    'XOR': "^", 
	    'XNOR': "NOT_SUPPORTED",
	    'LOR': "|", 
	    'LAND': "&", 
	    'NOTEQ': "!=",
	    'LNOT': "NOT_SUPPORTED",
	    'LSHIFTA': "<<", 
	    'RSHIFTA': ">>", 
            'LSHIFT': "NOT_SUPPORTED", 
            'RSHIFT': "NOT_SUPPORTED",
            'LT': "<", 
            'GT': ">", 
            'LE': "<=", 
            'GE': ">=", 
            'EQ': "==", 
            'NE': "!=", 
            'EQL': "NOT_SUPPORTED", 
            'NEL': "NOT_SUPPORTED",
            'COND': "?", # ?
            'EQUALS': "="
            }

def fatal_error(message):
    modulename = sys._getframe(1).f_code.co_filename
    funcname = sys._getframe(1).f_code.co_name
    fatal = {'modulename': os.path.basename(modulename),
               'funcname': funcname
               }
    print_fail(message)
    logger = logging.getLogger('goldmine')
    logger.critical(message, extra=fatal)
    exit(-1)
    return

def center_print(text):
    (width, height) = getTerminalSize()
    centered = op.methodcaller('center', width)
    
    text_to_print = '##  ' + text + '  ##'
    text_width = len(text_to_print)
    print(centered('#' * text_width))
    print(centered(text_to_print))
    print(centered('#' * text_width))

    return

def center_print(text):
    (width, height) = getTerminalSize()
    centered = op.methodcaller('center', width)
    
    text_to_print = '##  ' + text + '  ##'
    text_width = len(text_to_print)
    print(centered('#' * text_width))
    print(centered(text_to_print))
    print(centered('#' * text_width))
	
	
def figlet_print(text):
    #cprint(figlet_format(text, font='starwars'))
    (width, height) = getTerminalSize()
    f = Figlet(font='slant', direction=1, justify='center', width=width)
    print(f.renderText(text))
    return

def printTable(myDict, colList=None):
  
    if not colList:
        colList = list(myDict[0].keys() if myDict else []) 
    myList = [colList] # 1st row = header

    for key in myDict.keys(): 
        if type(myDict[key]) is list:
            list_ = [str(x) for x in myDict[key]]
            myList.append([key] + list_)
        else:
            myList.append([key, str(myDict[key])])

    colSize = [max(map(len,col)) for col in zip(*myList)]
    formatStr = ' | '.join(["{{:^{}}}".format(i) for i in colSize])
    myList.insert(1, ['-' * i for i in colSize]) # Seperating line

    content = ''

    for item in myList:
        content = content + formatStr.format(*item) + '\n'
    
    return content

def get_memory_usage(VmKey, PID):
    _proc_status = '/proc/' + str(PID) + '/status'
    _scale = {'kB': 1024.0, 'mB': 1024.0 * 1024.0,
              'kB': 1024.0, 'MB': 1024.0 * 1024.0}

    try:
        t = open(_proc_status)
        v = t.readlines()
        t.close()
    except: 
        return 0.0
    VmKeyLine = filter(lambda x: VmKey in x, v)
    try:
        VmKeys = VmKeyLine[0].split(None, 3)
    except IndexError:
        return 0.0

    if len(VmKeys) < 3:
        return 0.0

    return float(VmKeys[1]) * _scale[VmKeys[2]]

def memory_usage(PID):
    return get_memory_usage('VmSize:', PID)

def poll_memory(proc, q):
    memory = 0.0
    while proc.poll() is None:
        memory = max(memory, memory_usage(proc.pid))
        sleep(1)

    q.put(memory)

def cmd_exists(cmd):
    return any(
        os.access(os.path.join(path, cmd), os.X_OK) 
        for path in os.environ["PATH"].split(os.pathsep)
    )

def exec_command(command, out_file_name, err_file_name):
    
    done = Event()
    q = Queue()

    if out_file_name == 'pipe' or out_file_name == 'PIPE':
        out = PIPE
    else:
        out = open(out_file_name, 'w')

    if err_file_name == 'pipe' or err_file_name == 'PIPE':
        err = PIPE
    else:
        err = open(err_file_name, 'w')


    proc = Popen(command, shell=True, stdout=out, stderr=err)

    memory = 0.0
    memwatch = Thread(target=poll_memory, args=(proc, q))
    memwatch.daemon = True
    memwatch.start()

    data, stderr = proc.communicate()
    done.set()

    if not out_file_name == 'PIPE' and not out_file_name == 'pipe':
        out.close()

    if not err_file_name == 'PIPE' and not err_file_name == 'pipe':
        err.close()

    return data, stderr, proc.returncode, q.get()

def parse_cmdline_options(options):
    # Receives the options from the OptionParser commandline and 
    # Returns a dictionary with all parameters
    # Key of Returns is the Parameter Name specified in the command line
    # Val of Returns is the Parameter Value specified in the command line
    CMD_LINE_OPTIONS = {}

    CMD_LINE_OPTIONS['AGGREGATE'] = True if options.aggregate else False

    CMD_LINE_OPTIONS['VERIF'] = False if options.verif else True

    CMD_LINE_OPTIONS['STATICGRAPH'] = True if options.staticgraph else False
    
    CMD_LINE_OPTIONS['INTERMODULAR'] = True if options.intermodular else False

    if options.top:
        CMD_LINE_OPTIONS['TOP'] = options.top
    else:
        print_fail('Top module not specified for Assertion Mining.')
        exit(-1)
    
    if options.clock:
        clock = options.clock
        clock_name = clock[:clock.find(':')]
        clock_edge = clock[clock.find(':') + 1 :]
        CMD_LINE_OPTIONS['CLK'] = {clock_name:clock_edge}
    else:
        print_warning('Clock not specified. Assuming combinational design')

    if not os.path.isfile(options.man_assertion_file):
        print_info('User specified assertion file does not exist. Continuing with auto-generated assertions')
        CMD_LINE_OPTIONS['MAN_ASSERTIONS'] = []
    else:
        CMD_LINE_OPTIONS['MAN_ASSERTIONS'] = get_user_specified_assertions(options.man_assertion_file)
        #print CMD_LINE_OPTIONS['MAN_ASSERTIONS']
        #exit(0)

    if options.reset:
        reset = options.reset
        reset_name = reset[:reset.find(':')]
        reset_edge = reset[reset.find(':') + 1:]
        CMD_LINE_OPTIONS['RST'] = {reset_name:reset_edge}

    CMD_LINE_OPTIONS['INCLUDE'] = []
    if options.include:
        for include in options.include:
            if os.path.isdir(include):
                CMD_LINE_OPTIONS['INCLUDE'].append(os.path.abspath(include))
    else:
        CMD_LINE_OPTIONS['INCLUDE'] = []

    CMD_LINE_OPTIONS['PARSE'] = True if options.parse else False
    
    CMD_LINE_OPTIONS['MENGINE'] = options.engine
    if not options.engine:
        print_info('No Mining Engine specified. Engine specified in the goldmine.cfg will be used')

    if options.config_loc:
        CMD_LINE_OPTIONS['CFG'] = options.config_loc + '/goldmine.cfg' if options.config_loc else ''
    else:
        CMD_LINE_OPTIONS['CFG'] = './goldmine.cfg'

    if not os.path.exists(CMD_LINE_OPTIONS['CFG']):
        fatal_error('No GoldMine Configuration file specified. Use -u to specify a valid configuration file.')

    CMD_LINE_OPTIONS['VCD'] = os.path.abspath(options.vcd) if os.path.isfile(options.vcd) else ''
    CMD_LINE_OPTIONS['TARGETS'] = get_targets(options.targetv) if options.targetv else []
    CMD_LINE_OPTIONS['VTARGETS'] = True if options.vectorf else False
    
    if options.file_loc:
        CMD_LINE_OPTIONS['VFILES'] = get_file_names_from_loc(options.file_loc, '*.v')
    elif options.lfile:
        CMD_LINE_OPTIONS['VFILES'] = get_file_names_from_file(options.lfile)
    else:
        CMD_LINE_OPTIONS['VFILES'] = []

    
    if not CMD_LINE_OPTIONS['VFILES']:
        fatal_error('No source verilog file specified at command line. Use -f/-F option to specify \
                    source Verilog files')
   
    return CMD_LINE_OPTIONS


def get_user_specified_assertions(man_assertion_file):
    # One assertion per line in the format A |-> C or A |=> C. No need to give any name 
    massertions = []
    implications = ['|->', '|=>']

    mfile = open(man_assertion_file, 'r')
    mlines = mfile.readlines()
    mfile.close()

    for line in mlines:
        if line[0] == '#' or line[0] == '/':
            continue
        if not line:
            continue
        cycle_count = 0
        masserrtion_ = []
        antecedent_ = []

        implication_index = [line.find(s) for s in implications if s in line][0]
        antecedent = line[:implication_index]
        consequent = line[implication_index + 3 :]
        
        cycle_pattern = re.compile(r'(##[0-9]+)')
        prop_pattern = re.compile(r'([A-Za-z0-9_\[\]]+) == (0|1)')

        antecedent_list = re.split(cycle_pattern, antecedent)
        
        max_cycle = 0
        for ele in antecedent_list:
            if '##' in ele:
                max_cycle = max_cycle + int(ele[ele.rfind('#') + 1:])
        if implications[1] in line:
            max_cycle = max_cycle + 1
        
        for ele in antecedent_list:
            ele = ele.lstrip().rstrip()
            if '##' in ele:
                max_cycle = max_cycle - int(ele[ele.rfind('#') + 1:])
            else:
                propositions = ele.split('&')
                for prop in propositions:
                    match_p = re.search(prop_pattern, prop)
                    if match_p:
                        signal_ = match_p.group(1)
                        val = match_p.group(2)
                        signal = '[' + str(max_cycle) + ']' + signal_ if max_cycle > 0 else signal_
                        antecedent_.append(tuple([signal, int(val)]))

        masserrtion_.append(antecedent_)

        del antecedent_

        consequent = consequent.strip(' ()')
        consequent_ = consequent.split(' == ')
        masserrtion_.append(tuple([consequent_[0], int(consequent_[1].strip(' \n()'))]))

        massertions.append(masserrtion_)
        
        del masserrtion_

    
    return massertions

def get_file_names_from_loc(root_dir, extension):
    name_of_files = []

    for root, dirNames, fileNames in os.walk(root_dir):
        for fileName in fnmatch.filter(fileNames, extension):
            name_of_files.append(os.path.abspath(os.path.join(root, fileName)))

    return name_of_files

def get_file_names_from_file(lfile):

    lf = open(lfile, 'r')
    llines = lf.readlines()
    lf.close()

    vfiles = []

    for line_ in llines:
        line = line_.lstrip().rstrip()
        if not line:
            continue
        if line[0] == '#' or line[0] == '//':
            continue
        if os.path.isfile(line):
            abspath = os.path.abspath(line)
            vfiles.append(abspath.lstrip().rstrip())
    return vfiles


def get_targets(targets):

    targets_ = []
    stargets = targets.split(',')
    for target in stargets:
        targets_.append(target)

    return targets_

def goldmine_logger(name, logname):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(modulename)s - \
            %(funcname)s - %(message)s')
    
    handler = logging.FileHandler(logname, mode='w')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger
