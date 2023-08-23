 $contrl runtyp=energy $end
 $tddft iroot=1 $end
 $contrl scftyp=rohf mult=3 $end
 $scf couple=.t. alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 $end
 $contrl dfttyp=bhhlyp $end
 $scf dirscf=.t. $end
 $contrl units=bohr coord=unique icharg=0 maxit=200 $end
 $scf diis=.t. soscf=.f. fdiff=.f. damp=.f. shift=.f. $end
 $system timlim=999999100 mwords=500 kdiag=4 $end
 $basis gbasis=n31 ngauss=6 ndfunc=1 $end
 $contrl tddft=mrsf $end
 $tddft nstate=5 tammd=.t. mult=1 mrsoc=.t. $end
 $transt $end
