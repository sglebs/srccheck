#!/bin/bash

if [ ! -d "${UNDERSTAND_HOME}" ]; then
    mkdir -p "${UNDERSTAND_HOME}"
fi

if [ ! -z "${UNDERSTAND_FLOATING_LICENSE_SERVER}" ]; then
    if [ -z "${UNDERSTAND_FLOATING_LICENSE_SERVER_PORT}" ];then
        UNDERSTAND_FLOATING_LICENSE_SERVER_PORT="9000"
    fi
    echo "Connecting to floating license server: ${UNDERSTAND_FLOATING_LICENSE_SERVER}:${UNDERSTAND_FLOATING_LICENSE_SERVER_PORT}"
    echo "${UNDERSTAND_FLOATING_LICENSE_SERVER} 00000000 ${UNDERSTAND_FLOATING_LICENSE_SERVER_PORT}" > "${UNDERSTAND_HOME}/conf/license/locallicense.dat"
fi

if [[ ! -z "${UNDERSTAND_SDLCODE}" && ! -z "${UNDERSTAND_USER_EMAIL_ACCOUNT}" ]] ; then
    echo "${USER} ${UNDERSTAND_SDLCODE}" > "${UNDERSTAND_HOME}/conf/license/users.txt"
    UNDERSTAND_USER_CFG="${UNDERSTAND_USER_HOME}/Understand.conf"
    if [ ! -f "${UNDERSTAND_USER_CFG}" ]; then
        echo "Using SDL license registered to account \"${UNDERSTAND_USER_EMAIL_ACCOUNT}\": ${UNDERSTAND_SDLCODE}"
        echo "[General]" > "${UNDERSTAND_USER_CFG}"
        echo "UserText=${UNDERSTAND_USER_EMAIL_ACCOUNT}" >> "${UNDERSTAND_USER_CFG}"
    fi
fi

if [ ! -z "${UNDERSTAND_EVALCODE}" ]; then
    echo "Using evaluation code: ${UNDERSTAND_EVALCODE}"
    echo "${USER} ${UNDERSTAND_EVALCODE}" > "${UNDERSTAND_HOME}/conf/license/users.txt"
fi