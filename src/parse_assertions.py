import sys
from pprint import pprint


def convert_constant(constant):
   if ("?" in constant):
     value = -1
   elif ("'b" in constant):
     binary = constant.split("'b")[1].replace("_", "")
     if ("x" in binary or "z" in binary):
        value = "und"
     else:
        value = int(binary, 2)
   elif ("'h" in constant):
     binary = constant.split("'h")[1].replace("_", "")
     value = int(binary, 16)
   elif ("'d" in constant):
     binary = constant.split("'d")[1].replace("_", "")
     value = int(binary)
   else:
     try:
       value = int(constant)
     except:
       print("Value is probably a param check")
     
   return value

def parse_assertion(list_assertions, top_module):
    assertion_tables = dict()
    for key in list_assertions:
        raw_assertion = list_assertions[key]["Assertion"]
        clock_cycle = 2
        assertion_table = dict()
        raw_assertion = ''.join(raw_assertion.split()) #remove white space 
        raw_assertion = raw_assertion.replace("\n", "")
        assertion_string = raw_assertion
        label = key
        extra_cycle = False
        if ("|->" in raw_assertion):
            consequent = raw_assertion.split("|->")[1]
            raw_assertion = raw_assertion.split("|->")[0]
        elif ("|=>" in raw_assertion):
            consequent = raw_assertion.split("|=>")[1]
            raw_assertion = raw_assertion.split("|=>")[0]
            extra_cycle = True
        consequent = consequent.replace("(","").replace(")","")
        consequent_name = str(top_module) + "." + consequent.split("==")[0]
        consequent_value = consequent.split("==")[1]
        same_cycle_assertions = []
        same_cycle_assertions.append("0" + raw_assertion.split("##",1)[0].replace("(","").replace(")",""))
        try:
            raw_assertion = raw_assertion.split("##")[1]
        except IndexError:
            raw_assertion = "ONE CYCLE"
        if raw_assertion != "ONE CYCLE":
            for cycles in raw_assertion.split("##"):
                same_cycle_assertions.append(cycles.replace("(","").replace(")",""))
        cycle = 2
        for cur_cycle in same_cycle_assertions:
            additional_cycles = int(cur_cycle[0])
            cycle += additional_cycles
            cur_cycle = cur_cycle[1:]
            antecedents = cur_cycle.split("&")
            for antecedent in antecedents:
                signal_name = str(top_module) + "." + antecedent.split("==")[0]
                signal_value = antecedent.split("==")[1]
                clock_cycle += 0
                write_value = convert_constant(signal_value)
                if ("[" in signal_name):
                    select_value = signal_name.split("[")[1].split("]")[0]
                    signal_name =  signal_name.split("[")[0]
                    if (":" in select_value):
                        (msb,lsb) = select_value.split(":")
                        power = abs(int(msb) - int(lsb))
                        value = 2 ** power
                    else:
                        value = 2**int(select_value)
                        write_value = value
                if ((signal_name,cycle) not in assertion_table):
                    assertion_table[(signal_name, cycle)] = write_value
                else:
                    assertion_table[(signal_name, cycle)] = assertion_table[(signal_name,cycle)] + int(write_value)
 
        if (extra_cycle):
            cycle += 1
        assertion_table["max_cycle"] = cycle
        assertion_table[(consequent_name, cycle)] = convert_constant(consequent_value)
        assertion_table["consequent"] = (consequent_name, cycle)
        assertion_tables[label] = (assertion_table, assertion_string)
    return assertion_tables


def parse_assertion_file(filename, top_module):
   assertion_tables = dict()
   skip_strings = ["Importance", "Complexity", "Rank", "Triggered", "Vacuous", "Verification", "Report", "Total", "rate"]
   with open(filename, "r") as file:
      raw_assertions = file.readlines()
   for raw_assertion in raw_assertions:
      clock_cycle = 2
      assertion_table = dict()
      if ("Tabularized" in raw_assertion):
          break
      if (raw_assertion == "\n"): #skip empty lines
         continue
      if (raw_assertion[0] == "#"): #skip the comment
         continue
      if (raw_assertion[0] == "-"): #skip the comment
         continue
      if (any(x in raw_assertion for x in skip_strings)):
         continue
      raw_assertion = ''.join(raw_assertion.split()) #remove white space 
      raw_assertion = raw_assertion.replace("\n", "")
      assertion_string = raw_assertion
      label = raw_assertion.split(":")[0]
      raw_assertion = raw_assertion.split(":")[1]
      extra_cycle = False
      if ("|->" in raw_assertion):
         consequent = raw_assertion.split("|->")[1]
         raw_assertion = raw_assertion.split("|->")[0]
      elif ("|=>" in raw_assertion):
         consequent = raw_assertion.split("|=>")[1]
         raw_assertion = raw_assertion.split("|=>")[0]
         extra_cycle = True
      consequent = consequent.replace("(","").replace(")","")
      consequent_name = str(top_module) + "." + consequent.split("==")[0]
      consequent_value = consequent.split("==")[1]
      same_cycle_assertions = []
      same_cycle_assertions.append("0" + raw_assertion.split("##",1)[0].replace("(","").replace(")",""))
      try:
         raw_assertion = raw_assertion.split("##")[1]
      except IndexError:
         raw_assertion = "ONE CYCLE"
      if raw_assertion != "ONE CYCLE":
         for cycles in raw_assertion.split("##"):
            same_cycle_assertions.append(cycles.replace("(","").replace(")",""))
      cycle = 2
      for cur_cycle in same_cycle_assertions:
         additional_cycles = int(cur_cycle[0])
         cycle += additional_cycles
         cur_cycle = cur_cycle[1:]
         antecedents = cur_cycle.split("&")
         for antecedent in antecedents:
            signal_name = str(top_module) + "." + antecedent.split("==")[0]
            signal_value = antecedent.split("==")[1]
            clock_cycle += 0
            write_value = convert_constant(signal_value)
            if ("[" in signal_name):
               select_value = signal_name.split("[")[1].split("]")[0]
               signal_name =  signal_name.split("[")[0]
               if (":" in select_value):
                  (msb,lsb) = select_value.split(":")
                  power = abs(int(msb) - int(lsb))
                  value = 2 ** power
               else:
                  value = 2**int(select_value)
               write_value = value
            if ((signal_name,cycle) not in assertion_table):
               assertion_table[(signal_name, cycle)] = write_value
            else:
               assertion_table[(signal_name, cycle)] = assertion_table[(signal_name,cycle)] + int(write_value)
 
      if (extra_cycle):
         cycle += 1
      assertion_table["max_cycle"] = cycle
      assertion_table[(consequent_name, cycle)] = convert_constant(consequent_value)
      assertion_table["consequent"] = (consequent_name, cycle)
      assertion_tables[label] = (assertion_table, assertion_string)
   return assertion_tables
      
'''
if __name__ == '__main__':
   table = parse_assertion_file(sys.argv[1])
   pprint(table)
'''
