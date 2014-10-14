#!/bin/bash

cd $(dirname $0)
dir=$(pwd)
script=$dir/Marvin.ircBot.py
python=python3
log=$dir/Marvin.log
commande="$python $script"
case $1 in
  "start")
    $commande >$log 2>&1 &
    ;;
  "stop")
    pid=$(ps -ef | grep "$python.*$script" | grep -v grep | awk '{print $2}')
    [[ -z $pid ]] && echo "Pas de process trouvé" || kill $pid
    ;;
  "status")
    echo processus : 
    ps -ef | grep "$python.*$script" | grep -v grep
    ;;
  "restart")
    $0 stop
    $0 start
    ;;
  "restartifneeded")
    if [ $($0 status|wc -l) -le 1 ]
    then
      $0 restart
    fi
    ;;
  *)
    echo "Usage : $0 stop|start|status|restart|restartifneeded"
    ;;
esac
