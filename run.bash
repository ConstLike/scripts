#gms_sbatch2 -i $1 -s `pwd` -p "r630,ryzn,r631" -n28 -N1 -c1 -e  -v test -e /bighome/k.komarov/projects/work-dir
#gms_sbatch2 -i $1 -s `pwd` -p r630 -v gkonst -e /bighome/k.komarov/projects/gms-us
#gms_sbatch2 -i $1 -s `pwd` -p "r630,r631,ryzn" -v test -e /bighome/k.komarov/projects/work-dir
#gms_sbatch2 -i $1 -s `pwd` -p r630 -v konstoa4 -e /bighome/k.komarov/projects/work-dir
#gms_sbatch2 -i $1 -s `pwd` -p r630 -v konstob4 -e /bighome/k.komarov/projects/work-dir
#gms_sbatch2 -i $1 -p r630  --exclusive --reservation test
sbatch --reservation test -N1 -n1 -c28 -p r630 --exclusive sub.sh $1
