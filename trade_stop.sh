#!/bin/bash

pids=`pgrep -f trade_main.py`

for pid in $pids; do
  ppidInfo=`ps -o args= -p $pid`
  echo "[INFO] $ppidInfo($pid)"

  childpids="$(pgrep -P "${pid}")"
  for childpid in ${childpids}; do
    echo "[INFO] $(ps -o args= -p $childpid)($childpid)"
    kill $childpid
  done

  if [ -n "${childpids}" ]; then
    sleep 1
  fi

  ps -p $pid > /dev/null && kill $pid
  echo "[INFO] Successfully stopped $ppidInfo"
  done
done