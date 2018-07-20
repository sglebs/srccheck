FROM python:3.6-jessie

WORKDIR /data

COPY requirements.txt *.py /data/
ADD utilities /data/utilities

ENV UNDERSTAND_FILE="Understand-5.0.950-Linux-64bit.tgz" \
    UNDERSTAND_HOME="/data/scitools"

ENV UNDERSTAND_REPO_URL="http://latest.scitools.com/Understand/${UNDERSTAND_FILE}" \
    PYTHONPATH="${UNDERSTAND_HOME}/bin/linux64/python" \
    UNDERSTAND_USER_HOME="/root/.config/SciTools" \
    PATH="${PATH}:${UNDERSTAND_HOME}/bin/linux64/"


RUN apt-get update \
    && apt-get install -y curl tar libqt5gui5 \
    && curl -s -O "${UNDERSTAND_REPO_URL}" \
    && tar xvf "${UNDERSTAND_FILE}" \
    && rm -rf "${UNDERSTAND_FILE}" \
    && pip install --upgrade pip \
    && pip install paver \
    && pip install -r requirements.txt

VOLUME "${UNDERSTAND_USER_HOME}"

COPY docker-entrypoint.sh /data/

ENTRYPOINT [ "./docker-entrypoint.sh" ]
CMD [ "srccheck" ]