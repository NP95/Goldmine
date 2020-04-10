#Using Fedora 29 Image from Docker Hub
FROM fedora:29
#Name of the MAINTAINER
MAINTAINER Debjit Pal <work.debjitpal@gmail.com>

# Prepping the Fedora Docker container with upgraded packages and base system packages
RUN dnf clean all
RUN dnf -y update
RUN dnf -y install python2 python2-devel python2-pygraphviz gcc gcc-c++ vim-enhanced iverilog wget

# Copying GoldMine code to the Docker container
ADD ./ /opt/goldmine
WORKDIR /opt/goldmine

# Installing GoldMine specific Python packages to the Container
RUN pip install -r requirements.txt
RUN wget https://www.dropbox.com/s/e1wf6vh64v9tpf1/pyverilog_customized.tar.gz?dl=0 -O /opt/pyverilog.tar.gz
RUN tar -xzvf /opt/pyverilog.tar.gz -C /usr/lib/python2.7/site-packages
RUN rm /opt/pyverilog.tar.gz
