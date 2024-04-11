#!/bin/bash

input=$1

#SBATCH --job-name=bench-mrsf-at

/bighome/k.komarov/modules/work-dir/bin/oqp.sh $input
