import os, sys
import pandas as pd
import regex as re
import pprint as pp
import numpy as np
import sets
from datetime import datetime as dt
from decimal import Decimal
from progressbar import ProgressBar, Percentage, ETA, Bar

from configuration import current_path, make_directory, remove_directory, remove_file
from helper import exec_command, print_info, print_warning, print_newline, fatal_error, cmd_exists
from vcd_parser import parse_timeframes as pt
# Dictionary for different bit values found in VCD file
ValDict = {'0': 'zero_val_type',
           '1': 'one_val_type',
           'x': 'x_val_type',
           'z': 'z_val_type'
        }

# VCD Keywords
COMMENT = '$comment'
DATE = '$date'
DUMPALL = '$dumpall'
DUMPOFF = '$dumpoff'
DUMPON = '$dumpon'
DUMPVARS = '$dumpvars'
END = '$end'
ENDDEF = '$enddefinitions'
SCOPE = '$scope'
TSCALE = '$timescale'
UPSCOPE = '$upscope'
VAR = '$var'
VERSION = '$version'


def parse(vcd_file_path, top_module, clks, temporal_depth, ELABORATE_INFO, \
        scope_module_map, INTERMODULAR):
    # Expect the vcd file location including the vcd file itself
    if os.path.isfile(vcd_file_path):
        name, ext = os.path.splitext(vcd_file_path)
        if ext == '.vcd':
            print_info('Parsing VCD file: ' + vcd_file_path)
            vfile = open(vcd_file_path, 'r')
            if not vfile:
                fatal_error('Cannot open the VCD file at: ' + vcd_file_path)
            vcd_file_contents = vfile.readlines()
            vfile.close()
            #return parse_vcd_file_slow(vcd_file_contents, top_module, clks, temporal_depth, Ports)
            return parse_vcd_file_fast(vcd_file_contents, top_module, clks, \
                    temporal_depth, ELABORATE_INFO, scope_module_map, INTERMODULAR)

def parse_vcd_file_fast(vcontents, top_module, clks, temporal_depth, ELABORATE_INFO, \
        scope_module_map, INTERMODULAR):

    # clks: expected to be a dictionary with Key: Clock Name and Value = Clock edge (posedge or negedge)
    print_newline()
    #vfile = open(vcd_file_path, 'r')
    #if not vfile:
    #    fatal_error('Cannot open the VCD file at: ' + vcd_file_path)

    # FIXED: Change the instance name for the combinational circuit to include clock
    #        from the bench
    bench_name = top_module + '_bench'
    instance_name = top_module + '_'
    signal_table = {}
   
    IPort = ELABORATE_INFO[top_module]['ports']['IPort']
    OPort = ELABORATE_INFO[top_module]['ports']['OPort']
    Reg = ELABORATE_INFO[top_module]['ports']['Reg']
    Wire = ELABORATE_INFO[top_module]['ports']['Wire']

    if INTERMODULAR:
        print_warning('Intermodular assertion parsing requested. Proecssing will be significantly slow due to intermodular data parsing...')
        for scope_key in scope_module_map.keys():
            module_name = scope_module_map[scope_key]
            IPort_ = ELABORATE_INFO[module_name]['ports']['IPort']
            OPort_ = ELABORATE_INFO[module_name]['ports']['OPort']
            Reg_ = ELABORATE_INFO[module_name]['ports']['Reg']
            Wire_ = ELABORATE_INFO[module_name]['ports']['Wire']

            IPort_ = dict(("{}.{}".format(scope_key, k), v) for k, v in IPort_.items())
            OPort_ = dict(("{}.{}".format(scope_key, k), v) for k, v in OPort_.items())
            Reg_ = dict(("{}.{}".format(scope_key, k), v) for k, v in Reg_.items())
            Wire_ = dict(("{}.{}".format(scope_key, k), v) for k, v in Wire_.items())

            IPort.update(IPort_)
            OPort.update(OPort_)
            Reg.update(Reg_)
            Wire.update(Wire_)

            del IPort_
            del OPort_
            del Reg_
            del Wire_
    # We cannot just run a search for scope and upscope since if there are hierarchies, 
    # signals will get messed up. We still need to maintain the scope of each of the variable.
    # Do a Push and Pop of the scope
    # Read line by line in the VCD file
    version_Stat = False
    date_Stat = False
    timescale_Stat = False
    instance_Stat = False
    bench_Stat = False
    scope = []
    
    # This is the line index of the vcontents
    iindex = 0
    findex = len(vcontents)
    # Parsing the signal name, scopes etc
    #vline = vfile.readline()
    #while vline:

    for idx in range(iindex, findex):
        vline = vcontents[idx].lstrip().rstrip()
        if DATE in vline:
            date_Stat = True
        elif VERSION in vline:
            version_Stat = True
        elif TSCALE in vline:
            timescale_Stat = True
        elif version_Stat or date_Stat or timescale_Stat:
            if date_Stat:
                print_info('Parsing VCD file generated on: ' + vline.lstrip().rstrip())
                date_Stat = False
            elif version_Stat:
                print_info('VCD file created by the tool: ' + vline.lstrip().rstrip())
                version_Stat = False
            elif timescale_Stat:
                print_info('Design was simulated using timescale: ' + vline.lstrip().rstrip())
                timescale_Stat = False
        elif SCOPE in vline:
            line = vline.split(' ')
            scope_name = line[2]
            if scope_name == bench_name or scope_name == instance_name:
                scope.append('EMPTY')
            else:
                scope.append(scope_name)
            # FIXED: Make changes here for the Clock for Combinational circuit
            #        For combinational include the bench name in the dumpvar in testbench. Change in
            #        simulation.py. 
            # FIXME: Also, change the instance_stat for the scope below to include all 
            #        the inter-modular signal values. Else now, the CSV does not have the inter-modular
            #        signal names
            if scope_name == bench_name:
                bench_Stat = True
            if scope_name == instance_name:
                instance_Stat = True
                bench_Stat = False
            #else:
            #    instance_Stat = False
            del line
            #print scope
        elif UPSCOPE in vline:
            scope.pop()
        elif VAR in vline and bench_Stat:
            line = vline.split(' ')
            if line[4] == 'DEFAULT_CLOCK':
                signal_name = line[4]
                signal_symbol = line[3]
                #signal_table[signal_symbol] = '.'.join(x for x in scope) + '.' + signal_name
                signal_table[signal_symbol] = signal_name
            del line
        elif VAR in vline and instance_Stat:
            line = vline.split(' ')
            signal_symbol = line[3]
            signal_name = line[4]
            scope_ = [x for x in scope if x != 'EMPTY'] + [signal_name]
            if signal_symbol not in signal_table.keys():
                signal_table[signal_symbol] = '.'.join(scope_)
            #signal_table[signal_symbol] = signal_name
            del line
        elif ENDDEF in vline:
            iindex = idx + 1
            break

        #vline = vfile.readline() 
    
    pp.pprint(signal_table)
    print(len(signal_table.keys()))

    val_pattern = re.compile(r'^#{1}[0-9]+')
    # signals = [signal_table[key] for key in signal_table.keys()]

    # The above list comprehension of the signals won't work as we need to do bit blasting for vector signals
    # So follow the below procedure
    signals = []
    #signal_table_keys_to_remove = []

    for key in signal_table.keys():
        signal = signal_table[key]
        if signal in IPort.keys():
            width = int(IPort[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in OPort.keys():
            width = int(OPort[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in Reg.keys():
            width = int(Reg[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in Wire.keys():
            width = int(Wire[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal == 'DEFAULT_CLOCK':
            signals.append(signal)
        #else:
        #    signal_table_keys_to_remove.append(key)

    #if signal_table_keys_to_remove:
    #    for ele in signal_table_keys_to_remove:
    #        del signal_table[ele]
    #
    #del signal_table_keys_to_remove

    print(len(signals))
    #exit(0)
    # dframe: A list to get the signal values from the VCD trace dump for all the signals
    dframe = []
    for signal in signals:
        dframe.append(np.array([], dtype=np.int))

    for idx in range(iindex, findex):
        vline = vcontents[idx].lstrip().rstrip()
        if "#0" in vline:
            for idx1 in range(len(signals)):
                dframe[idx1] = np.append(dframe[idx1], [2], axis=0)
                
            iindex = idx + 1
            break
    
    row_id = 0
    print_newline()
    print_info('Parsing trace data')
    dframe = pt.parse_timeframes(iindex, findex, vcontents, signals, signal_table, dframe)

    shape = len(dframe[0])
    rows = []
    result = 0
    num_rows_ = 0
    signal_lookback = []
    for tdepth in range(temporal_depth):
        for signal in signals:
            if tdepth == 0:
                signal_lookback.append(signal)
            else:
                signal_lookback.append('[' + str(tdepth) + ']' + signal)
    
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)

    if not clks.keys() or 'DEFAULT_CLOCK' in clks.keys()[0]:
        print_info('Creating data frames for Combinational circuit type')
    else:
        print_info('Creating time shifted data for Sequential circuit type')
    
    clk_name = clks.keys()[0]
    clk_edge_value = int(clks[clk_name])
    clk_dframe = dframe[signals.index(clk_name)]
    
    print_newline()
    temporal_frame = []
    # List containing strings of unique time shifted values of the signals
    unique_row_values = []
    for idx1 in pbar(range(shape - 1)):
        curr_clk_val = int(clk_dframe[idx1])
        next_clk_val = int(clk_dframe[idx1 + 1])
        if curr_clk_val != clk_edge_value and next_clk_val == clk_edge_value:
            temporal_frame.append(idx1)
            if len(temporal_frame) < temporal_depth:
                continue
            row_values = []
            for idx2 in range(len(temporal_frame)):
                row_id = temporal_frame[len(temporal_frame) - idx2 - 1]
                for signal in signals:
                    row_values.append(dframe[signals.index(signal)][row_id])
            del temporal_frame[0]

            row_val_string = ''.join(str(x) for x in row_values)

            if row_val_string not in unique_row_values:
                rows.append(row_values)
                unique_row_values.append(row_val_string)
            else:
                continue

            num_rows_ = num_rows_ + 1
            result = result + 1

    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)
   
    print_newline()
    print_info('Converting time shifted mine data in dataframes')
    rows_ = pd.DataFrame()
    for idx in pbar(range(len(signal_lookback))):
        column_val = [item[idx] for item in rows]
        rows_[signal_lookback[idx]] = column_val
   
    print_newline()
    print_info('Validating simulation data')
    rows_valid_type = pt.validation_sim_data(num_rows_ - result, num_rows_, num_rows_, signal_lookback, rows)

    return rows_, num_rows_, rows_valid_type
    
def parse_vcd_file_slow(vcontents, top_module, clks, temporal_depth, Ports):

    # clks: expected to be a dictionary with Key: Clock Name and Value = Clock edge (posedge or negedge)
    print_newline()
    #vfile = open(vcd_file_path, 'r')
    #if not vfile:
    #    fatal_error('Cannot open the VCD file at: ' + vcd_file_path)

    instance_name = top_module + '_'
    signal_table = {}
   
    IPort = Ports['IPort']
    OPort = Ports['OPort']
    Reg = Ports['Reg']
    Wire = Ports['Wire']
    # We cannot just run a search for scope and upscope since if there are hierarchies, 
    # signals will get messed up. We still need to maintain the scope of each of the variable.
    # Do a Push and Pop of the scope
    # Read line by line in the VCD file
    version_Stat = False
    date_Stat = False
    timescale_Stat = False
    instance_Stat = False
    scope = []
    
    # This is the line index of the vcontents
    iindex = 0
    findex = len(vcontents)
    # Parsing the signal name, scopes etc
    #vline = vfile.readline()
    #while vline:

    for idx in range(iindex, findex):
        vline = vcontents[idx].lstrip().rstrip()
        if DATE in vline:
            date_Stat = True
        elif VERSION in vline:
            version_Stat = True
        elif TSCALE in vline:
            timescale_Stat = True
        elif version_Stat or date_Stat or timescale_Stat:
            if date_Stat:
                print_info('Parsing VCD file generated on: ' + vline.lstrip().rstrip())
                date_Stat = False
            elif version_Stat:
                print_info('VCD file created by the tool: ' + vline.lstrip().rstrip())
                version_Stat = False
            elif timescale_Stat:
                print_info('Design was simulated using timescale: ' + vline.lstrip().rstrip())
                timescale_Stat = False
        elif SCOPE in vline:
            line = vline.split(' ')
            scope_name = line[2]
            scope.append(scope_name)
            if scope_name == instance_name:
                instance_Stat = True
            else:
                instance_Stat = False
            del line
            #print scope
        elif UPSCOPE in vline:
            scope.pop()
        elif VAR in vline and instance_Stat:
            line = vline.split(' ')
            signal_symbol = line[3]
            signal_name = line[4]
            #signal_table[signal_symbol] = '.'.join(x for x in scope) + '.' + signal_name
            signal_table[signal_symbol] = signal_name
            del line
        elif ENDDEF in vline:
            iindex = idx + 1
            break

        #vline = vfile.readline() 

    val_pattern = re.compile(r'^#{1}[0-9]+')
    # signals = [signal_table[key] for key in signal_table.keys()]

    # The above list comprehension of the signals won't work as we need to do bit blasting for vector signals
    # So follow the below procedure
    signals = []
    
    for key in signal_table.keys():
        signal = signal_table[key]
        if signal in IPort.keys():
            width = int(IPort[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in OPort.keys():
            width = int(OPort[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in Reg.keys():
            width = int(Reg[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
        elif signal in Wire.keys():
            width = int(Wire[signal])
            if width == 1:
                signals.append(signal)
            else:
                signal_scalar = [signal + '[' + str(idx) + ']' for idx in range(width)]
                signals.extend(signal_scalar)
                del signal_scalar
    
    # dframe: a Panda dataframe to get the signal values from the VCD trace dump for all the signals
    dframe = pd.DataFrame(columns=signals)
    for signal in signals:
        dframe[signal] = dframe[signal].astype('str')
    
    #vline = vfile.readline()
    #while vline:
    for idx in range(iindex, findex):
        vline = vcontents[idx].lstrip().rstrip()
        if "#0" in vline:
            row_vals = {}
            for signal in signals:
                row_vals[signal] = ['x']
            dframe_ = pd.DataFrame.from_dict(row_vals, dtype='str')
            dframe = dframe.append(dframe_, ignore_index=True)
            iindex = idx + 1
            break
        #vline = vfile.readline()
   
    row_id = 0
    #while vline:
    trace_data_lines = findex - iindex
    
    print_info('Parsing trace data')
    
    # Progress Bar Widget for the trace data processing
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)
    for i in pbar(range(iindex, findex)):
        vline = vcontents[i].lstrip().rstrip()
        
        #percent_completed = 1.0 * (i - iindex) / trace_data_lines * 100
        #if percent_completed % 5.0 == 0.0:
        #    print 'Trace data parsing comleted: ' + str(percent_completed / 5.0)
        
        if not vline or vline[0] == '$':
            #vline = vfile.readline()
            continue
        elif vline[0] == '#':
            dtemp = pd.DataFrame()
            dtemp = dframe.tail(1)
            dframe = dframe.append(dtemp, ignore_index=True)
            row_id = row_id + 1
            #print dframe
        # TODO: Still need to tackle the bit vectors
        elif vline[0] == 'b' or vline[0] == 'B':
            vline_split = vline.split()
            symbol = vline_split[1]
            val = vline_split[0][1:]
            try:
                signal_name = signal_table[symbol]
            except KeyError:
                continue
            for j in range(len(val)):
                signal_scalar_name = signal_name + '[' + str(j) + ']'
                # Assuming the signals are specified in the Big-Endian format
                dframe[signal_scalar_name][row_id] = val[-1 - j]
        else:            
            symbol = vline[1:].lstrip().rstrip()
            val = vline[0]
            try:
                signal_name = signal_table[symbol]
            except KeyError:
                continue
            dframe[signal_name][row_id] = val

        #vline = vfile.readline()
        
    #vfile.close()
    print dframe.shape
    print_newline()
    
    # (rows, columns) in the data parsed from the VCD file
    shape = dframe.shape
    #print shape 
    rows = []
    result = 0
    num_rows_ = 0
    signal_lookback = []
    for tdepth in range(temporal_depth):
        for signal in signals:
            if tdepth == 0:
                signal_lookback.append(signal)
            else:
                signal_lookback.append('[' + str(tdepth) + ']' + signal)
    #print signal_lookback
    rows__ = pd.DataFrame(columns=signal_lookback)
    for signal in signal_lookback:
        rows__[signal] = rows__[signal].astype('str')
    #print rows_
    # Combinational Circuits
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)

    if not clks.keys():
        # TODO: Write the code for the data manipulation for the data for combinational circuits
        # print "Combinational Circuits"
        print_info('Creating time shifted data for Combinational circuit type')
        for idx0 in pbar(range(shape[0])):
            row_values = []
            for idx4 in range(shape[1]):
                row_values.append(dframe[idx4][idx0])

            rows.append(row_values)
            rows_unique = uniquify(rows)

            if len(rows_unique) < len(rows):
                rows = rows_unique
                continue
            
            rows = rows_unique
            num_rows_ = num_rows_ + 1
            row_dict = {}
            for idx5 in range(len(signals)):
                row_dict[signals[idx5]] = [row_values[idx5]]
            rows_frame = pd.DataFrame.from_dict(row_dict, dtype='str')

            rows__ = rows__.append(rows_frame, ignore_index=True)

            result = result + 1
    # Sequential Circuits
    else:
        # We will need the temporal_depth information to use here
        clk_name = clks.keys()[0]
        clk_edge_value = int(clks[clk_name])
        clk_dframe = dframe[clk_name]

        print_info('Creating time shifted data for Sequential circuit type')
        temporal_frame = []

        for idx1 in pbar(range(shape[0] - 1)):
            # FIXME: May have issues with X or Z val type. Correction needed
            curr_clk_val = int(clk_dframe[idx1])
            next_clk_val = int(clk_dframe[idx1 + 1])
            if curr_clk_val != clk_edge_value and next_clk_val == clk_edge_value:
                temporal_frame.append(idx1)
                #print "Pushed back Idx1: " + str(idx1)
                if len(temporal_frame) < temporal_depth:
                    continue
                row_values = []
                for idx2 in range(len(temporal_frame)):
                    row_id = temporal_frame[len(temporal_frame) - idx2 - 1]
                    #print "Row ID: " + str(row_id)
                    for signal in signals:
                        row_values.append(dframe[signal][row_id])
                # Delete the first temporal frame. So that in next iteration next frame index
                # can be added
                del temporal_frame[0]

                rows.append(row_values)
                #rows_unique = list(map(list, set(map(lambda i: tuple(i), rows))))
                #rows_unique = [list(x) for x in set(tuple(x) for x in rows)]
                rows_unique = uniquify(rows)

                if len(rows_unique) < len(rows):
                    rows = rows_unique
                    continue

                #print row_values
                # locally checking if any new rows of values can be added or not 
                rows = rows_unique

                num_rows_ = num_rows_ + 1
                row_dict = {}
                for idx3 in range(len(signal_lookback)):
                    row_dict[signal_lookback[idx3]] = [row_values[idx3]]
                rows_frame = pd.DataFrame.from_dict(row_dict, dtype='str')

                rows__ = rows__.append(rows_frame, ignore_index=True)
                #print rows_
                #if num_rows_ == 4:
                #    exit(0)

                result = result + 1
    
    rows_ = pd.DataFrame()
    for signal in signal_lookback:
        rows_ = pd.concat([rows_, rows__[signal]], axis=1)
    #rows_.to_csv('rows_.csv', index=False)
    #print 'result: ' + str(result) + ' num_rows_ : ' + str(num_rows_) + '\n'
    # FIXME: Fix the validate function below
    rows_valid_type = validate_sim_data(num_rows_ - result, num_rows_, num_rows_, signal_lookback, rows_)
        
    #print_info('Total number of trace examples added: ' + str(num_rows_))

    return rows_, num_rows_, rows_valid_type

def uniquify(x):
    concatData = []
    for x_ in x:
        concatData_ = "".join(x__ for x__ in x_)
        concatData.append(concatData_)

    uniqueset = sets.Set(concatData)

    uniqueList = []
    for t in uniqueset:
        list_ = []
        for i in range(len(t)):
            list_.extend(t[i])
        uniqueList.append(list_)
        del list_

    return uniqueList

'''
def validate_sim_data(first, last, num_rows_, signal_lookback, rows_):
    
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)
    
    print_newline()
    rows_invalid_type = []
    
    if first >= num_rows_ or first >= last:
        fatal_error('Trace data construction is wrong')

    for i in range(first, last):
        rows_invalid_type.append('null_invalid_type')
    
    print_info('Validating simulation data')

    for signal in pbar(signal_lookback):
        for j in range(first, last):
            if rows_invalid_type[j] == 'null_invalid_type':
                if rows_[signal][j] == 'x' or rows_[signal][j] == 'X' or rows_[signal][j] == 2:
                    rows_invalid_type[j] = 'x_invalid_type'
                elif rows_[signal][j] == 'z' or rows_[signal][j] == 'Z' or rows_[signal][j] == 3:
                    rows_invalid_type[j] = 'z_invalid_type'

    return rows_invalid_type
'''

def mine_data_valid(csv_dframe):
    # Can we look for at least N = 30 number of data examples in the mining data 
    # for effective mining? Its an easy fix. Lets do it
    rows_invalid_type = validate_mine_data(csv_dframe)
    if rows_invalid_type.count('null_invalid_type') >= 10:
        return True
    else:
        return False

def is_target_constant(csv_dframe, target):
    
    values = csv_dframe[target].drop_duplicates().values.tolist()
    if len(values) > 1:
        return False
    else:
        return True

def validate_mine_data(csv_dframe):
    shape = csv_dframe.shape
    num_rows = shape[0]
    column_names = list(csv_dframe)

    rows_invalid_type = []

    for i in range(num_rows):
        rows_invalid_type.append('null_invalid_type')

    for column in column_names:
        for j in range(num_rows):
            if rows_invalid_type[j] == 'null_invalid_type':
                if csv_dframe[column][j] == 'x' or csv_dframe[column][j] == 'X' or csv_dframe[column][j] == 2:
                    rows_invalid_type[j] = 'x_invalid_type'
                elif csv_dframe[column][j] == 'z' or csv_dframe[column][j] == 'Z' or csv_dframe[column][j] == 3:
                    rows_invalid_type[j] = 'z_invalid_type'
    return rows_invalid_type

def find_invalid_row_indices(rows_invalid_type):
    indices = [i for i in range(len(rows_invalid_type)) if rows_invalid_type[i] != 'null_invalid_type']
    return indices

def erase_and_reindex_data(csv_dframe, target):
    
    shape = csv_dframe.shape
    rows_invalid_type = validate_mine_data(csv_dframe)
    summary_report(rows_invalid_type)
    invalid_rows_indices = find_invalid_row_indices(rows_invalid_type)

    if invalid_rows_indices:
        indices_to_keep = set(range(shape[0])) - set(invalid_rows_indices)
        csv_dframe = csv_dframe.take(list(indices_to_keep))
        csv_dframe = csv_dframe.reset_index()
    
    csv_dframe = csv_dframe.apply(pd.to_numeric)

    return csv_dframe

def summary_report(rows_invalid_type):

    num_valid_rows = rows_invalid_type.count('null_invalid_type')
    num_invalid_rows = rows_invalid_type.count('x_invalid_type') + rows_invalid_type.count('z_invalid_type')

    '''
    for idx in range(len(rows_invalid_type)):
        if rows_invalid_type[idx] == 'null_invalid_type':
            num_valid_rows = num_valid_rows + 1
   
        if rows_invalid_type[idx] != 'null_invalid_type':
            num_invalid_rows = num_invalid_rows + 1
    '''
    print_info('Number of added unique data examples: ' + str(len(rows_invalid_type)))
    print_info('Number of valid examples: ' + str(num_valid_rows))
    print_info('Number of invalid examples: ' + str(num_invalid_rows))
    
    print_newline()

    return

def write_csv(dframe, top_module, target):

    if target:
        csv_dir = current_path() + '/' + target
    else:
        csv_dir = current_path()

    if not os.path.isdir(csv_dir):
        make_directory(csv_dir)
    
    if target:
        csv_file_name = csv_dir + '/' + target + '.csv'
    else:
        csv_file_name = csv_dir + '/' + top_module + '.csv'

    dframe.to_csv(csv_file_name, index=False)

    return

def write_testbench(top_module, clks, rsts, max_sim_cycles, inports, outports):
    # curr_path = current_path()
    # testbench_location = curr_path + '/goldmine.out/' + top_module
    # if not os.path.isdir(testbench_location):
    #    make_directory(testbench_location)
    testbench_location = current_path()
    testbench_file_name = testbench_location + '/' + top_module + '_bench.v'
    vcd_file_name = testbench_location + '/' + top_module + '.vcd'
    
    remove_file(testbench_file_name)
    remove_file(vcd_file_name)

    ckeys = clks.keys()
    rkeys = rsts.keys()
    # Content of the testbench is written in the string tcont in main memory and then it will 
    # be written to the file at once. This will save to and fro from the main disk and will compensate
    # some penalty
    tcont = '`timescale 1ns/1ps'
    tcont = tcont + '\n\n'
    tcont = tcont + 'module ' + top_module + '_bench();\n\n'
    
    # NOTE: Just taking care of the combinational module
    if 'DEFAULT_CLOCK' in ckeys:
        tcont = tcont + 'reg DEFAULT_CLOCK;\n'
    if 'DEFAULT_RESET' in rkeys:
        tcont = tcont + 'reg DEFAULT_RESET;\n'

    for key in inports.keys():
        port_name = key
        port_width = int(inports[key])
        if port_width == 1:
            tcont = tcont + 'reg ' + port_name + ';\n'
        else:
            tcont = tcont + 'reg ' + '[' + str(port_width - 1) + ':0] ' + port_name + ';\n'

    tcont = tcont + '\n'

    for key in outports:
        port_name = key
        port_width = int(outports[key])
        if port_width == 1:
            tcont = tcont + 'wire ' + port_name + ';\n'
        else:
            tcont = tcont + 'wire ' + '[' + str(port_width - 1) + ':0] ' + port_name + ';\n'

    tcont = tcont + '\n'

    tcont = tcont + top_module + ' ' + top_module + '_ (\n'

    inp = ',\n'.join('\t.' + x + '(' + x + ')' for x in inports)
    outp = ',\n'.join('\t.' + x + '(' + x + ')' for x in outports)
    
    tcont = tcont + inp + ',\n' + outp + ');\n\n'
   
    tcont = tcont + '\tinitial begin\n'
    tcont = tcont + '\t\t$dumpfile(\"' + vcd_file_name + '\");\n'
    
    #NOTE: To tackle the combinational circuit, we create a temporary clock in the testbench
    #      as a reference signal in the bench and dump all signal values from bench and beneath
    if 'DEFAULT_CLOCK' in ckeys:
        tcont = tcont + '\t\t$dumpvars(0, ' + top_module + '_bench);\n'
    else:
        tcont = tcont + '\t\t$dumpvars(0, ' + top_module + '_bench.' + top_module + '_);\n'

    for clk in ckeys:
        tcont = tcont + '\t\t' + clk + ' = ' + clks[clk] + ';\n'
    for rst in rkeys:
        tcont = tcont + '\t\t' + rst + ' = ' + rsts[rst] + ';\n'
    tcont = tcont + '\t\t#26;\n'
    for rst in rkeys:
        tcont = tcont + '\t\t' + rst + ' = ' + str(abs(1 - int(rsts[rst]))) + ';\n'
    tcont = tcont + '\t\t#' + str(50 * max_sim_cycles) + ' $finish;\n'
    tcont = tcont + '\tend\n\n'

    for clk in ckeys:
        tcont = tcont + '\talways begin\n'
        tcont = tcont + '\t\t#25 ' + clk + ' = ~' + clk + ';\n'
        tcont = tcont + '\tend\n\n'

    tcont = tcont + '\talways begin\n'
    tcont = tcont + '\t\t#24;\n'
    for inport in inports:
        if inport not in ckeys and inport not in rkeys:
            tcont = tcont + '\t\t' + inport + ' = $random;\n'
    tcont = tcont + '\t\t#26;\n'
    tcont = tcont + '\tend\n\n'

    tcont = tcont + 'endmodule'

    tfile = open(testbench_file_name, 'w')

    tfile.write(tcont)
    tfile.close()

    del tcont

    return

def simulation_command(top_module, verilog_files, testbench_file_name, include_paths, sim_tool, CONFIG):
    # verilog_files: assumed to be a list: containing the verilog files needed for the simulation 
    # with the absolute path

    # include_paths: assumed to be a list: containing the paths where the files specified by the `include
    # command can be found
    sim_executable = CONFIG[sim_tool]
    if not os.path.isfile(sim_executable) or not os.access(sim_executable, os.X_OK):
        fatal_error('Cannot run simulation. Cannot find valid executbale for tool: ' + sim_tool)
        return
        
    curr_path = current_path()
    sim_command = ''

    if sim_tool == 'iverilog':
        #sim_command = sim_executable + ' -g2001 -osimv -s ' + top_module + '_bench ' + \
        sim_command = 'iverilog -g2001 -osimv -s ' + top_module + '_bench ' + \
                testbench_file_name
    elif sim_tool == 'vcs':
        #sim_command = sim_executable + ' -full64 +v2k -top ' + top_module + '_bench ' + \
        sim_command = 'vcs +v2k -top ' + top_module + '_bench ' + \
                '-l ' + top_module + '.log ' + testbench_file_name + \
                ' -full64' if 'amd64' in sim_executable else ''

    vfile = ' '.join(x for x in verilog_files)

    sim_command = sim_command + ' ' + vfile

    incpath = ''
    if sim_tool == 'iverilog':
        for x in include_paths:
           incpath = incpath + ' -I' + x
    elif sim_tool == 'vcs':
        incpath = incpath + '+incdir'
        for x in include_paths:
            incpath = incpath + '+' + x

    sim_command = sim_command + ' ' + incpath

    return sim_command

def simulate(top_module, clks, rsts, verilog_files, include_paths, max_sim_cycles, sim_tool, CONFIG, Ports):
    
    write_testbench(top_module, clks, rsts, max_sim_cycles, Ports['IPort'], Ports['OPort'])

    testbench_location = current_path()
    testbench_file_name = testbench_location + '/' + top_module + '_bench.v'
    if not os.path.isfile(testbench_file_name):
        fatal_error('No testbench file found for the module: ' + top_module \
                + ' at location: ' + testbench_location)

    sim_command = simulation_command(top_module, verilog_files, testbench_file_name, \
            include_paths, sim_tool, CONFIG)
    #print sim_command 
    # TODO: Write Process command to compile the design
    print_info('Simulating with: ' + sim_tool)
    print_newline()

    out_file_name = testbench_location + '/' + top_module + '_compile.log'
    err_file_name = testbench_location + '/' + top_module + '_err.log'
    
    remove_file(out_file_name)
    remove_file(err_file_name)
    
    # If VCS needs to be used export VCS_HOME environment variable
    if sim_tool == 'vcs':
       VCS_HOME = CONFIG['vcs_home']
       os.environ['VCS_HOME'] = VCS_HOME
       vcs_bin_path = os.path.join(VCS_HOME, 'bin')
       os.environ['PATH'] += os.pathsep + vcs_bin_path
       try:
           os.environ['LM_LICENSE_FILE'] += os.pathsep + CONFIG['LM_LICENSE_FILE']
       except KeyError:
           os.environ['LM_LICENSE_FILE'] = os.pathsep + CONFIG['LM_LICENSE_FILE']
    
    start_compile = dt.now()
    data, err, retcode, mem_usage = exec_command(sim_command, out_file_name, err_file_name)
    end_compile = dt.now()

    cmd_file = open('sim_command_' + top_module + '.sh', 'w')
    cmd_file.write('#!/bin/bash' + '\n\n')
    if sim_tool == 'vcs':
        cmd_file.write('export VCS_HOME=' + CONFIG['vcs_home'] + '\n\n')
        cmd_file.write('export PATH=$VCS_HOME/bin:$PATH' + '\n\n')
        cmd_file.write('export LM_LICENSE_FILE=$LM_LICENSE_FILE:' + CONFIG['LM_LICENSE_FILE'] + '\n\n')
    cmd_file.write(sim_command)
    cmd_file.close()

    print_info('Compile Time: ' + str(end_compile - start_compile))
    print_info('Compile Memory Usage: ' + str(round(Decimal(mem_usage / 1048576), 2)) + ' MB')
    print_newline()


    # Check if the executable has been generated
    simv = testbench_location + '/simv'
    if not os.path.isfile(simv) or not os.access(simv, os.X_OK):
        fatal_error('Verilog file compilation failed. Cannot run simulation')


    # TODO: Write Process command to run the simv executable
    out_file_name = testbench_location + '/' + top_module + '_run.log'

    remove_file(out_file_name)

    start_run = dt.now()
    data, err, retcode, mem_usage = exec_command(simv, out_file_name, 'PIPE')
    end_run = dt.now()

    vcd_file_name = testbench_location + '/' + top_module + '.vcd'
    if not os.path.isfile(vcd_file_name):
        fatal_error('Running simulation failed. No VCD file produced for mining')

    print_info('Run Time: ' + str(end_compile - start_compile))
    print_info('Run Memory Usage: '+ str(round(Decimal(mem_usage / 1048576), 2)) + ' MB')
    print_newline()

    # Clean up directory
    if sim_tool == 'iverilog':
        remove_file(simv)
    elif sim_tool == 'vcs':
        remove_file(simv)
        remove_file('ucli.key')
        remove_directory('csrc')
        remove_directory('simv')
        remove_directory('simv.daidir')
        remove_directory('.vcsmx_rebuild')

    return 

#clks = {'clk':'1'}
#rsts = {'rst':'1'}
#inports = ['req1', 'req2', 'rst', 'clk']
#outports = ['gnt1', 'gnt2']
#parse('./arb2.vcd', 'arb2', clks, 4)
#write_testbench('arb2', clks, rsts, inports, outports)
