#!/bin/bash

PROC=64

### Make tool installation directory
mkdir -pv tool
cd tool

## ABC installation
git clone https://github.com/berkeley-abc/abc.git
cd abc
make
cd ..

## YoSys instlation
git clone https://github.com/YosysHQ/yosys.git yosys
cd yosys
make -j${PROC}
cd ..

## SymbiYosys installation
git clone https://github.com/YosysHQ/SymbiYosys.git SymbiYosys
cd SymbiYosys
make install
cd ..

## Yices 2 installation
git clone https://github.com/SRI-CSL/yices2.git yices2
cd yices2
autoconf
./configure
make -j64
cd build/x86_64-pc-linux-gnu-release/bin
ln -s yices_smt2 yices-smt2
cd ../../../..

## Z3 instalation
git clone https://github.com/Z3Prover/z3.git z3
cd z3
python scripts/mk_make.py
cd build
make -j${PROC}
cd ../../

## super_prove installation
wget https://downloads.bvsrc.org/super_prove/super_prove-hwmcc17_final-2-d7b71160dddb-CentOS_7-Release.tar.gz
tar -xzvf super_prove-hwmcc17_final-2-d7b71160dddb-CentOS_7-Release.tar.gz
rm -rf super_prove-hwmcc17_final-2-d7b71160dddb-CentOS_7-Release.tar.gz
cd super_prove/bin
FILE="suprove"
printf '%s\n' '#!/bin/bash' \
'tool=super_prove; if [ "$1" != "${1#+}" ]; then tool="${1#+}"; shift; fi' \
'exec /opt/tool/super_prove/bin/${tool}.sh "$@"' > ${FILE}
/usr/bin/chmod +x ${FILE}
cd ../..

## Avy instllation
git clone https://bitbucket.org/arieg/extavy.git
cd extavy
git submodule update --init
mkdir -pv build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j64
cd ../..

## Boolector installation
git clone https://github.com/boolector/boolector
cd boolector
./contrib/setup-btor2tools.sh
./contrib/setup-lingeling.sh
./configure.sh
make -C build -j${PROC}
cd ..
