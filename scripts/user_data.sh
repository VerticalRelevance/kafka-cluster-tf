#!/bin/bash

# 1. Update the OS
dnf update -y

# 2. Install Java 17 (Kafka requires Java)
dnf install -y java-17-amazon-corretto

# 3. Download and extract Kafka
cd /opt
wget https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz
tar -xzf kafka_2.13-3.9.2.tgz
mv kafka_2.13-3.9.2 kafka

# 4. Start ZooKeeper
/opt/kafka/bin/zookeeper-server-start.sh -daemon /opt/kafka/config/zookeeper.properties

# Wait for ZooKeeper to be ready
sleep 5

# 5. Start Kafka
/opt/kafka/bin/kafka-server-start.sh -daemon /opt/kafka/config/server.properties