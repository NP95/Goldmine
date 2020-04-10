from helper import print_warning, print_line_stars

package_list = ["copy",
         "os",
         "sys",
         "numpy",
         "scipy",
         "pandas",
         "pyverilog",
         "matplotlib",
         "optparse",
         "datetime",
         "Queue",
         "subprocess",
         "pprint",
         "math",
         "sklearn",
         "multiprocessing",
         "progressbar",
         "networkx",
         "graphviz",
         "pygraphviz",
         "tempfile",
         "regex",
         "itertools",
         "collections",
         "csv",
         "errno",
         "shutil",
         "platform",
         "argparse",
         "decimal",
         "fnmatch",
         "pyfiglet",
         "termcolor",
         "time",
         "threading",
         "operator",
         "logging",
         "sets",
         "distutils",
         "Cython",
         "glob",
         "random",
         "json",
         "pyparsing",
         "inspect",
         "re",
         "pickle"
         ]
failed_libs = []

def check_system_sanity():
    for module in package_list:
        try:
            exec("import {0}".format(module))	
            exec("del {0}".format(module))
        except ImportError as err_msg:
            failed_libs.append(module)
    with open("install.sh", "w") as file:
        for module in failed_libs:
            file.write("pip install {0}\n".format(module))
            print_warning("No Module {0}, please install using pip!".format(module))
    if (len(failed_libs) > 0):
        print_line_stars()
        print("[MES]-->" + "System module sanity check failed")
        print("[MES]-->" + "Please run 'sh install.sh' as root")
        print_line_stars()
    else:
        print_line_stars()
        print("[MES]-->" + "System module sanity check succeeded")
        print_line_stars()

    return


if __name__ == '__main__':
    check_system_sanity()
