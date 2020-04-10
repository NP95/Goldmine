import numpy as np
from progressbar import ProgressBar, Percentage, ETA, Bar
from helper import fatal_error

def parse_timeframes(iindex, findex, vcontents, signals, signal_table, dframe):
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)
    
    # C Type Data Type to speed up. 
    # NOTE: Need further augmentation to speedup. A more accurate Cython implementation
    # NOTE: can be made. Future enahancement
    cdef Py_ssize_t idx
    cdef str vline, symbol, val, val_, signal_name, signal_scalar_name
    cdef int signalp
    cdef int row_id = 0

    for i in pbar(range(iindex, findex)):
        vline = vcontents[i].lstrip().rstrip()

        if not vline or vline[0] == '$':
            continue
        elif vline[0] == '#':
            for j in range(len(signals)):
                signalp = int(dframe[j][-1])
                dframe[j] = np.append(dframe[j], [signalp], axis=0)
            row_id = row_id + 1
        elif vline[0].upper() == 'B':
            vline_split = vline.split()
            symbol = vline_split[1]
            val = vline_split[0][1:]
            try:
                signal_name = signal_table[symbol]
            except KeyError:
                continue
            for k in range(len(val)):
                signal_scalar_name = signal_name + '[' + str(k) + ']'
                try:
                    idx = signals.index(signal_scalar_name)
                except ValueError:
                    continue
                if val[-1 - k] == 'x' or val[-1 - k] == 'X':
                    val_ = '2'
                elif val[-1 - k] == 'z' or val[-1 - k] == 'Z':
                    val_ = '3'
                else:
                    val_ = val[-1 - k]
                dframe[idx][row_id] = int(val_)
        else:
            symbol = vline[1:].lstrip().rstrip()
            if vline[0] == 'x' or vline[0] == 'X':
                val = '2'
            elif vline[0] == 'z' or vline[0] == 'Z':
                val = '3'
            else:
                val = vline[0]

            try:
                signal_name = signal_table[symbol]
            except KeyError:
                continue
            try:
                idx = signals.index(signal_name)
            except ValueError:
                continue
            dframe[idx][row_id] = int(val)

    return dframe

def validation_sim_data(first, last, num_rows_, signal_lookback, rows):
    
    widgets = ['Processed: ', Percentage(), ' ', Bar(marker='>', left='[', right=']'), \
            ' (', ETA(), ')']
    pbar = ProgressBar(widgets=widgets)
    
    rows_invalid_type = []
    
    if first >= num_rows_ or first >= last:
        fatal_error('Trace data construction is wrong')

    for i in range(first, last):
        rows_invalid_type.append('null_invalid_type')

    for i in pbar(range(len(signal_lookback))):
        for j in range(first, last):
            if rows_invalid_type[j] == 'null_invalid_type':
                if rows[j][i] == 'x' or rows[j][i] == 'X' or rows[j][i] == 2:
                    rows_invalid_type[j] = 'x_invalid_type'
                elif rows[j][i] == 'z' or rows[j][i] == 'Z' or rows[j][i] == 3:
                    rows_invalid_type[j] = 'z_invalid_type'

    return rows_invalid_type
