#!/bin/bash

if [ ! -d "${UNDERSTAND_HOME}" ]; then
    mkdir -p "${UNDERSTAND_HOME}"
fi

if [ ! -z "${FLOATING_LICENSE_SERVER}" ]; then
    if [ -z "${FLOATING_LICENSE_SERVER_PORT}" ];then
        FLOATING_LICENSE_SERVER_PORT="9000"
    fi
    echo "Connecting to floating license server: ${FLOATING_LICENSE_SERVER}:${FLOATING_LICENSE_SERVER_PORT}"
    echo "${FLOATING_LICENSE_SERVER} 00000000 ${FLOATING_LICENSE_SERVER_PORT}" > "${UNDERSTAND_HOME}/conf/license/locallicense.dat"
fi

if [[ ! -z "${SDLCODE}" && ! -z "${USER_EMAIL_ACCOUNT}" ]] ; then
    echo "${USER} ${SDLCODE}" > "${UNDERSTAND_HOME}/conf/license/users.txt"
    UNDERSTAND_USER_CFG="${UNDERSTAND_USER_HOME}/Understand.conf"
    if [ ! -f "${UNDERSTAND_USER_CFG}" ]; then
        echo "Using SDL license registered to account \"${USER_EMAIL_ACCOUNT}\": ${SDLCODE}"
        echo "[General]" > "${UNDERSTAND_USER_CFG}"
        echo "UserText=${USER_EMAIL_ACCOUNT}" >> "${UNDERSTAND_USER_CFG}"
    fi
fi

if [ ! -z "${EVALCODE}" ]; then
    echo "Using evaluation code: ${EVALCODE}"
    echo "${USER} ${EVALCODE}" > "${UNDERSTAND_HOME}/conf/license/users.txt"
fi

exec "${@}"