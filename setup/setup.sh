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
        echo -n "Install Auto Scaling Controller and Dashboard? [y/n]: "
        read line
        [ "${line}" = "y" -o "${line}" = "Y" ] && break
        [ "${line}" = "n" -o "${line}" = "N" ] && exit 1
    done
fi

#
if [ "${install}" -eq "0" ]; then
    yum -y install git ansible
fi

#
if [ -d "${SRC_PATH}" ]; then
    cd ${SRC_PATH} && git pull
else
    git clone ${REPOSITORY_URL} ${SRC_PATH}
fi
[ $? -ne "0" ] && error "Cannot get source code"

#
cd ${SRC_PATH}/setup && ansible-playbook -i localhost, -c local controller.yml

exit 0
