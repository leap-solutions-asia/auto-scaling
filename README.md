# Auto Scaling for Leap GIO Public

Just testing!

## Auto Scaling Controller

### Specifications

* Supported OS (Leap GIO Public Virtual Machine)
  - CentOS 7.x

### Requirements

* docker
* docker-compose

Required for Installation
* git
* ansible

### Getting Started

1. Create a new CentOS 7.x VM on Leap GIO Public
1. Login to the VM
1. Install and setup Auto Scaling Controller (Perform the following command)
```
bash <(curl -Ls https://github.com/leap-solutions-asia/auto-scaling/raw/master/setup/setup.sh)
```

## Auto Scaling Agent

### Specifications

* Supported OS (Leap GIO Public Virtual Machine)
  - CentOS 6.x
  - CentOS 7.x
  - Ubuntu 14.04
  - Ubuntu 16.04
* Agent port
  - 8585/tcp (allow 8585/tcp iptables, firewalld and ufw)

### Requirements

*python >= 2.6

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
1. Stop the VM and create a new OS Template

## For Developer

### Requirements

* docker
* docker-compose
* git

### Getting Started

1. Clone repository
```
$ git clone git@github.com:leap-solutions-asia/auto-scaling.git
```
1. Start Auto Scaling Container
```
$ cd auto-scaling
$ docker-compose up -d
```
