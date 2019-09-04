# Auto Scaling for Leap GIO Public

## Auto Scaling Controller and Dashboard

### Specifications

Supported OS (Leap GIO Public Virtual Machine)
* CentOS 7.x
* Ubuntu 16.04
* Ubuntu 18.04

Dashboard ports
* 8080-8084/tcp (allow 8080-8084/tcp iptables, firewalld or ufw)

### Requirements

* docker
* docker-compose

Required for Installation
* git
* ansible

### Getting Started

1. Create a new VM of Supported OS on Leap GIO Public
1. Login to the VM
1. Install and setup Auto Scaling Controller and Dashboard (Perform the following command)
```
bash <(curl -Ls https://github.com/leap-solutions-asia/auto-scaling/raw/master/setup/setup.sh)
```
4. Access to dashboard http://VM_IP_ADDRESS:8080/

## Auto Scaling Agent

### Specifications

Supported OS (Leap GIO Public Virtual Machine)
* CentOS 6.x
* CentOS 7.x
* Ubuntu 14.04
* Ubuntu 16.04
* Ubuntu 18.04

Agent port
* 8585/tcp (allow 8585/tcp iptables, firewalld or ufw)

### Requirements

* python >= 2.6

Required for Installation
* git
* ansible

### Getting Started

1. Create a new VM of Supported OS on Leap GIO Public
1. Login to the VM
1. Install and setup Auto Scaling Agent (Perform the following command)
```
bash <(curl -Ls https://github.com/leap-solutions-asia/auto-scaling/raw/master/setup/setup-agent.sh)
```
4. Stop the VM and create a new OS Template

## For Developer

### Requirements

* docker
* docker-compose
* git

### Getting Started

1. Clone repository
1. Start Auto Scaling Container and Dashboard
```
$ cd auto-scaling
$ docker-compose up -d
```
3. Access to dashboard http://localhost:8080/
