grep "Geom" opt_geom.xyz | awk '{print $2, $3}' | gnuplot -p -e "set terminal qt size 800,600; set title 'Energy vs. Geometry Number'; set xlabel 'Geometry Number'; set ylabel 'Energy'; plot '-' using 1:2 with lines title 'Energy'"