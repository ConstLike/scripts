#!/bin/bash

awk -v ref="$1" '{
     if($1=="1" && $2=="A")
     {
     S0en=-($3+ref);
     printf("%.10f\n", S0en);
     }
     }' "$2"
