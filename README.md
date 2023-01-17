#############################################################################

GoldMine Tool Command Line Parameters:

    usage: goldmine.py [-h] [-a] -m TOP -c CLOCK -r RESET [-p] [-e ENGINE] -u
                       CONFIG_LOC [-v VCD] [-t TARGETV] [-T] [-I INCLUDE] [-V]
                       [-S] [-M MAN_ASSERTION_FILE] [-f FILE_LOC | -F LFILE]

    arguments:
      -h, --help            Gives list of arguments and exits
	  -a, --aggregate       Aggregate rankings for assertion importance,
	                        complexity, coverage and complexity (BETA phase)
	  -m TOP, --module TOP  Top module of the design (Mandatory arguments)
	  -c CLOCK, --clock CLOCK
	                        Clock signal
	  -r RESET, --reset RESET
	                        Reset signal
	  -p, --parse           Parse the verilog file(s) and exit
	  -e ENGINE, --engine ENGINE
	                        Assertion mining engine (Default engine is PRISM)
	  -u CONFIG_LOC, --configuration_file_loc CONFIG_LOC
	                        GoldMine configuration file location (Mandatory arguments)
	  -v VCD, --vcd VCD     VCD File(s)
	  -t TARGETV, --targets TARGETV
	                        Target variables seperated by comma for assertions
	                        mining*
	  -I INCLUDE, --include INCLUDE
	                        Include Path for Verilog `include files
	  -V, --verification    Specify to skip formal verification
	  -S, --static_dump     Specify to dump static analysis results
      -N, --inter_modular   Specify to mine inter modular assertions
                            (significantly slow)
	  -M MAN_ASSERTION_FILE, --manual_assertion MAN_ASSERTION_FILE
	                        File containing user specified assertions
	  -f FILE_LOC, --files FILE_LOC
	                        Location containing source Verilog files
	  -F LFILE, --file_list LFILE
	                        A file containing name of verilog files with absolute
	                        path, one file in every line

    * To understand target variable, please read the paper: https://ieeexplore.ieee.org/document/6516599/
#############################################################################

GoldMine Configuration File goldmine.cfg explanation

	vcs_home :: Installation directory of Synopsys VCS tool
	
	synopsys_license :: Synopsys license string
	
	ifv_root :: Installation directory of Cadence IFV tool
	
	cadence_license :: Cadence license string
	
	iverilog_home :: Installation directory of IVerilog executable
	
	engine :: Default mining engine. If no engine is specified in the command line,
	          this engine will be used for mining.
	
	max_sim_cycles :: maximum number of cycles for which simulation trace data is generated
	
	num_cycles :: maximum temporal depth of the generated assertions
	
	num_propositions :: maximum number of propositions allowed in the antecedent of the assertions
	                    (To be implemented. Future enhancement)
	
	num_counterexamples :: Maximum number of counter-examples to be used to refine an assertion
	                       (To be implemented. Future enhancement) 
	
	num_partitions :: Decision forest parametrs (To be implemented.
	                  Future enhancement)
	
	min_coverage :: Coverage miner parameters. (Will be used when Coverage Miner is integrated
	                as one of the mining algorithms)


#############################################################################

3rd-Party Tool Requirements:

    Synopsys Verilog Compiler Simulator / IVerilog
        GoldMine uses VCS /IVerilog to generate random simulation data. GoldMine can
        accept VCD files on the command line if VCS/IVerilog is not available. 
    
    Cadence Incisive Formal Verifier
        GoldMine uses IFV to formally verify the assertions it generates.
        GoldMine will label the assertions it generates as "unverified" if IFV
        is not available.

    Verific (https://www.verific.com/) Library for SystemVerilog support (optional)
        GoldMine uses Verific Python Library to parse SystemVerilog designs
        for static analysis purposes. This has been made possible via a gracious research
        donation by Verific.

##############################################################################

How to use Python 3 virtualenv (Preferred method):

	mkdir $HOME/VirtualEnvs
	cd $HOME/VirtualEnvs
	which python3
	virtualenv --python="/usr/bin/python3" 3vgoldmine
	cd 3vgoldmine/bin
	source activate
	cd
	mkdir -pv $HOME/Work
	cd $HOME/Work
	git clone https://debjitp@bitbucket.org/debjitp/goldminer.git GoldMine
	cd GoldMine
	pip install -r requirements3.txt
	pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"  (You might need sudo access for graphviz. If you do not have graphviz, then you have to comment those out in source files, which is a painful thing)
	cd src3/vcd_parser
	python setup.py build_ext --inplace
	ln -s ./vcd_parser/parse_timeframe*.so parse_timeframes.so
	cd ~/Downloads
	wget https://www.dropbox.com/s/cym1olcdsrc7rxs/pyverilog3_customized.tar.gz?dl=0 -O ./pyverilog3.tar.gz
	tar -xzvf pyverilog3.tar.gz
	cp pyverilog ~/VirtualEnvs/vgoldmine/lib/python3.10/site-packages/ -r
	cd ~/Work/GoldMine
	mkdir -pv RunTime
	cd RunTime
	python ../src3/goldmine.py -h

##############################################################################

How to use Docker container (Recommended method):

    git clone https://debjitp@bitbucket.org/debjitp/goldminer.git
    cd goldmine
    vi goldmine.cfg (Edit goldmine.cfg to setup VCS/IVerilog/IFV location, VCS/IFV license string)
    mkdir -pv RunTime
    cd RunTime
    ln -s ../run_goldmine.sh
    ln -s ../vfiles
    cd ..
    sh build_docker.sh

When above procedure is finished, your Docker container should be up and running. Once Docker container is active do the following to build the VCD parser:

    cd src/vcd_parser
    python setup.py build_ext --inplace
    ln -s ./vcd_parser/parse_timeframes.so 
    cd ../../RunTime
    python ../src/goldmine.py -h
    sh run_goldmine.sh

Before you exit Docker container, please make sure you have copied the generated data from the container to your host machine. Once you exit Docker, any data created within Docker container is lost forever.

##############################################################################

How to use Anaconda Python environment (Recommended):

    1. For Anaconda, Anaconda 2.7.X / Python 2.7.X is needed. It can be downloaded from https://repo.anaconda.com/archive/Anaconda2-2019.10-Linux-x86_64.sh (Please visit https://www.anaconda.com/distribution/#download-section for the latest download linki for Linux/Mac)
    2. Install Anaconda into a user space where new environment can be created
    3. Replicate GoldMine Anaconda environment using goldmine.yml file following the below steps.
        i) Set the prefix at the end of the yml file. The prefix should be the location where goldmine environemnt will be created and the additional packages will be installed
        ii) Execute the command -- 
            conda env create -f goldmine.yml
        iii) Execute the command --
            conda activate goldmine
        iv) Once the conda environemnt is set, please do the following:
            wget https://www.dropbox.com/s/e1wf6vh64v9tpf1/pyverilog_customized.tar.gz?dl=0 -O ~/Downloads/pyverilog.tar.gz
            cd ~/Downloads
            tar -xzvf pyverilog.tar.gz -C <Anaconda_Installation_Dir>/envs/goldmine/lib/python2.7/site-packages
            cd <goldmine_clone_directory>/src/vcd_parser
            python setup.py build_ext --inplace
            ln -s ./vcd_parser/parse_timeframes.so
            cd ../../
            vi goldmine.cfg (Edit goldmine.cfg to setup VCS/IVerilog/IFV location, VCS/IFV license string)
            mkdir -pv RunTime
            cd RunTime
            python ../src/goldmine.py -h
            ln -s ../run_goldmine.sh
            ln -s ../vfiles
            sh run_goldmine.sh
                
##############################################################################

How to do a standalone install (Not recommended):

	1. Run  python system_sanity.py. It should check for the existence of all the necessary
	Python packages in the system. If some of the packages are not available, then it will 
	create a shell script file which can be run as a root to install the necessary Python 
	packages in the system
	
	2. To parse VCD trace file successfully, follow the steps below:
	    i) cd src/vcd_parser
	    ii) python setup.py build_ext --inplace
	    iii) ln -s ./vcd_parser/parse_timeframes.so 
	
	3. Write vfiles enlisting all the files necessary for the design for which assertion 
	to be mined. If the required files are available in a directory you can specify the 
	directory using -f option. vfiles should have the name of the source Verilog files
	with a relative path to the Run directory or in terms of absolute path.
	
	4. All directory and files can be specified either relative to the run directory or 
	along with the absolute path
	
	5. Run the tool from a Run directory outside of the src directory in order not to 
	distort source code
	
	6. Python requirement: Python 2.7.X
	
	7. Simulator that can be used: Synopsys VCS / IVerilog. IVerilog gets precedence. 
	Please see goldmine.cfg to specify simulation tools
	
	8. Verification engine can be used: Cadence IFV. Please see goldmine.cfg to 
	specify formal verifier engine tool.

##############################################################################

How to report an issue?

    - Please report your issues/bug at https://bitbucket.org/debjitp/goldminer/issues
    - Please provide the command that you ran, any and all error files, sample Verilog design to replicate
      the issue, snapshot of the error message

##############################################################################

FAQs and tips
    
    0. GoldMine can only accept Verilog designs as it uses a Verilog parser at the backend. GoldMine does not accept SystmeVerilog designs.
    1. GoldMine can mine assertions for both sequential and combinational designs. However it can only mine assertions for single bit target variable. For example, if you have the following set of outputs,
        
        output A;
        output [3:0] B;

        GoldMine will be able to mine assertions for the output/target variable A but not for output/target variable B.
        
    2. We DO NOT support 2-dimensional registers as of now. It has been planned for future release.
    3. All vector signals (including input/output/register/wire) must have explicit numerical values of the
       MSB and LSBs
    4. We provide several formal verification IPs that can be used to formally verify the assertions. They are tuned for Cadence IFV. In case, you want to use a different formal verifier, please use those APIs and modify the internal functions to suit the format of the formal verifier used.
    5. Please go through the example directory to inspect different verilog codes and expected outputs for some sample designs.
    6. All GoldMine related papers are available at https://sites.google.com/view/goldmine-illinois/publications?authuser=0
