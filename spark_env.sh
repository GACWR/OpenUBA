#!/bin/bash

export HADOOP_COMMON_HOME=/usr/local/Cellar/hadoop/3.2.1/
export HADOOP_HDFS_HOME=/usr/local/Cellar/hadoop/3.2.1/libexec/share/hadoop/hdfs
export HADOOP_YARN_HOME=/usr/local/Cellar/hadoop/3.2.1/libexec/share/hadoopyarn


export JAVA_HOME=$(/usr/libexec/java_home)
export HADOOP_HOME=/usr/local/Cellar/hadoop/3.2.1/
export HADOOP_CONF_DIR=$HADOOP_HOME/libexec/etc/hadoop
export SCALA_HOME=/usr/local/Cellar/apache-spark/1.1.0

export PATH=$PATH:$HADOOP_HOME/bin:$SCALA_HOME/bin
alias hstart=$HADOOP_HOME/sbin/start-dfs.sh;$HADOOP_HOME/sbin/start-yarn.sh
alias hstop=$HADOOP_HOME/sbin/stop-dfs.sh;$HADOOP_HOME/sbin/stop-yarn.sh

