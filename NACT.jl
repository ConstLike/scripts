using Plots

dt = 0.5
time, ES0, ES1, nact = [], [], [], []
fname = "namd2.log"
out = readlines(fname)
for (index, value) in enumerate(out)
   if occursin("NONADIABATIC COUPLING TERM (A.U.)",value)
      push!(nact, parse(Float64, split( out[index+5] )[3] ))
   end
   if occursin("NEGATIVE ROOT(S) FOUND", value)
      par = parse(Int64, split(value)[1] )
      if par == 1 (push!(ES0, parse(Float64, split( out[index+1] )[3] ))) end
      if par == 0 (push!(ES0, parse(Float64, split( out[index+2] )[3] ))) end
      push!(ES1, parse(Float64, split( out[index+3] )[3] ))
   end
end
time = Vector([i*dt for i in 1:length(nact)])
fn = plot(
           time, 
           ES1[2:length(ES1)-1]-ES0[2:length(ES0)-1],
           ylabel="E_S1-E_S0", 
           xlabel="time (fs)", 
           lv=5, 
           linecolor="black", 
           legend = false
          )
fn = plot!(
           time, 
           5*abs.(nact), 
           linecolor="red", 
           legend = true,
           show = true
          )
xlims!(0, 250)
show(fn)
gui()
