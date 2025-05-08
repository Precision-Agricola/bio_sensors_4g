#!/bin/bash

SESSION="stream_session"
SCRIPT_PATH="/home/ec2-user/bio_sensors_4g/timestream/live_stream.py"
LOG_PATH="/home/ec2-user/bio_sensors_4g/timestream/live_stream.log"

tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
  echo "[INFO] Starting tmux session: $SESSION"
  tmux new-session -d -s $SESSION "python3 $SCRIPT_PATH >> $LOG_PATH 2>&1"
else
  echo "[INFO] Session already running: $SESSION"
fi
