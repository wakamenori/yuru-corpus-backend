#!/bin/bash

for i in `seq 0 12`
do
  echo "[$i]" ` date '+%y/%m/%d %H:%M:%S'` "connected."
  open https://colab.research.google.com/drive/1XbM1WuZ_ry83vqvKZKE0grur1XTU5ERu#scrollTo=SshyuAT_8XBN

  sleep 3600
done
