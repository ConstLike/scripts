#!/bin/bash

awk -v ref="$1" '{if($1=="INPUT" && $2="CARD>" && $3=="C1")
          {
              getline;
       	      C1_X=$5;
    	        C1_Y=$6;
   		        C1_Z=$7;

   		        getline;
   		        C2_X=$5;
   		        C2_Y=$6;
   		        C2_Z=$7;

   		        getline;
   		        C3_X=$5;
   		        C3_Y=$6;
   		        C3_Z=$7;

   		        getline;
   		        C4_X=$5;
   		        C4_Y=$6;
   		        C4_Z=$7;

		          bd1_X = (C2_X - C4_X)^2;
		          bd1_Y = (C2_Y - C4_Y)^2;
		          bd1_Z = (C2_Z - C4_Z)^2;

              bd2_X = (C4_X - C3_X)^2;
              bd2_Y = (C4_Y - C3_Y)^2;
              bd2_Z = (C4_Z - C3_Z)^2;

              bd3_X = (C3_X - C1_X)^2;
              bd3_Y = (C3_Y - C1_Y)^2;
              bd3_Z = (C3_Z - C1_Z)^2;

		          r1 = sqrt(bd1_X + bd1_Y + bd1_Z);
		          r2 = sqrt(bd2_X + bd2_Y + bd2_Z);
		          r3 = sqrt(bd3_X + bd3_Y + bd3_Z);

              Double = (r1+r3)/2
              Single = r2

              BLA = Double - Single

              printf("%.5f\t", BLA);
              printf("%.5f\t", r1);
              printf("%.5f\t", r2);
              printf("%.5f\t", r3);
          }
          # Start energy part
          n_states = 6;                      # number of states in log
          n_tmp = n_states - 2;
          if($2=="A")
          {
              i = $1 - 1;
              energy[i] = ($3+ref)*27.2114;
          }
          if($1==n_states && $2=="A")
          {
              for(i=0; i<=n_tmp; i++)
          {
              printf("%.10f\t", energy[i]);
          }
          printf("%.10f\n", energy[5]);      # print last element without a tab
      }
      }' "$2"
