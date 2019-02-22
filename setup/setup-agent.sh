#! /bin/bash

#
REPOSITORY_URL=https://github.com/leap-solutions-asia/auto-scaling.git
SRC_PATH=/usr/local/src/auto-scaling

#
error(){
    echo "Error: $*"
    exit 1
}

#
usage(){
    echo "Usage: ${SCRIPT} [-s|-y]"
    echo "       -s: Skip install git and ansible"
    echo "       -y: Skip confimation"
    exit 1
}

#
install=0
confirm=0

while getopts :hsy OPT
do
    case $OPT in
        s)
            install=1
            ;;
        y)
            confirm=1
            ;;
        :|h|\?)
            usage
            ;;
    esac
done

#
if [ "${confirm}" -eq "0" ]; then
    while [ 1 ]
    do
        echo -n "Install Auto Scaling Agent? [y/n]: "
        read line
        [ "${line}" = "y" -o "${line}" = "Y" ] && break
        [ "${line}" = "n" -o "${line}" = "N" ] && exit 1
    done
fi

#
if [ "${install}" -eq "0" ]; then
    if [ -f "/etc/os-release" ]; then
        . /etc/os-release
    else
        if [ -f "/etc/redhat-release" ]; then
            ID=centos
            VERSION_ID=6
        fi
    fi

    case "${ID}" in
        centos)
            [ "${VERSION_ID}" -eq 6 ] && yum -y install epel-release
            yum -y install git ansible
            ;;
        ubuntu)
            apt-get update
            apt-get install -y software-properties-common
            if [ "${VERSION_ID}" = "14.04" ]; then
                apt-add-repository --yes ppa:ansible/ansible
                apt-get update
            else
                apt-add-repository --yes --update ppa:ansible/ansible
            fi
            apt-get install -y git ansible
            ;;
        *)
            echo "Error: unsupported OS"
            exit 1
            ;;
    esac
fi

#
if [ -d "${SRC_PATH}" ]; then
    cd ${SRC_PATH} && git pull
else
    git clone ${REPOSITORY_URL} ${SRC_PATH}
fi
[ $? -ne "0" ] && error "Cannot get source code"

#
cd ${SRC_PATH}/setup && ansible-playbook -i localhost, -c local agent.yml

exit $?
