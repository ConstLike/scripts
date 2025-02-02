 $contrl
   scftyp=rohf
   runtyp=md
   dfttyp=bhhlyp
   icharg=0
   tddft=mrsf
   maxit=200
   mult=3
   units=bohr
 $end
 $scf
   dirscf=.t.
   diis=.t.
   soscf=.f.
   fdiff=.f.
   damp=.f.
   shift=.f.
   swdiis=1e-4
   couple=.true.
   alpha(1)=0.5,0.5,0.5
   beta(1)=0.5,0.5,0.5
 $end
 $basis
   gbasis=n31
   ngauss=6
   ndfunc=1
 $end
 $dft
   swoff=1e-6
 $end
 $tddft
   nstate=6
   iroot=3
   mult=1
   tammd=.t.
 $end
 $system
   timlim=999999100
   mwords=500
   kdiag=4
 $end
 $md
   read=.f.
   mbt=.t.
   mbr=.t.
   ttotal=0
   dt=5e-16
   nsteps=4000
   mdint=vverlet
   nvtnh=0
   batht(1)=300.0
   rstemp=.f.
   jevery=1
   kevery=1
   thrshe=7.5
   namd=.t.
   ndtlf=2
 $end
