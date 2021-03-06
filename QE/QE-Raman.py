import re
import sys
from math import sqrt

CmtoEv = 0.0001239842573
Bohr = 0.52917721092 # [A]

scf_in = open(sys.argv[1], 'r')

stepsize = 0.005

masses_dict = {}
symbols = []
masses = []
positions = []
while True:
    line = scf_in.readline()
    if not line:
        break

    p = re.search(r'ATOMIC_SPECIES', line)
    if p:
        while True:
            line = scf_in.readline()
            p1 = re.search(r'^\s*(\w+)\s*(\d+\.\d+)', line)

            if not p1:
                break
            masses_dict[p1.group(1)] = float(p1.group(2))

    p = re.search(r'ATOMIC_POSITIONS angstrom', line)
    if p:
        while True:
            line = scf_in.readline()
            p1 = re.search(r'^\s*(\w+)\s*(-*\d+\.\d+)\s+(-*\d+\.\d+)\s+(-*\d+\.\d+)', line)

            if not p1:
                break

            atomic_symbol = p1.group(1)
            symbols.append( atomic_symbol )
            masses.append( masses_dict[atomic_symbol] )
            positions.append([ float(p1.group(2))/Bohr, float(p1.group(3))/Bohr, float(p1.group(4))/Bohr ])
scf_in.close()
natoms = len(symbols)
#print symbols, masses, positions

dynmat_out = open(sys.argv[2], 'r')
q_point = []
eigvals = []
norms = []
eigenvecs = []

while True:
    line = dynmat_out.readline()
    if not line:
        break

    p = re.search(r'\s*q\s*=\s*([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)', line)
    if p:
        q_point = [float(p.group(1)), float(p.group(2)), float(p.group(3))]
        if any(x != 0.0 for x in q_point):
            print "Found q point which is not G point."
            sys.exit(0)

    p = re.search(r'\s*omega.+?([-\d\.]+)\s*\[cm-1\]; norm=\s*([-\d\.]+)', line)
    if p:
        eigval = float(p.group(1))
        norm = float(p.group(2))

        if eigval < 0.0:
            print "Skipping negative eigenvalue %5.3f cm-1" % eigval
            continue

        eigvals.append(eigval)
        eigenvecs.append("")
        norms.append(norm)
        for i in range(natoms):
            line = dynmat_out.readline()
            p1 = re.search(r'(-*\d+\.\d+)\s+(-*\d+\.\d+)\s+(-*\d+\.\d+)\s+(-*\d+\.\d+)\s+(-*\d+\.\d+)\s+(-*\d+\.\d+)', line)
            if not p1:
                break

            #eigenvec = [ float(p1.group(1)), float(p1.group(3)), float(p1.group(5)) ]
            eigenvecs[len(eigvals)-1] += " "+p1.group(1)+" "+p1.group(3)+" "+p1.group(5)


#print eigenvecs
#stepsize = 0.02
for i in range(len(eigvals)):
    for step in (-1,1):
        filename = '%03d-%d' % (i, step)

        scf_file = open(filename+'-scf.in', 'w')
        ph_file = open(filename+'-ph.in', 'w')

        scf_in = open(sys.argv[1], 'r')
        while True:
            line = scf_in.readline()
            if not line:
                break

            p = re.search(r'\s*&control', line)
            if p:
                scf_file.write(line+'    outdir = "./'+filename+'"\n')
                continue
            
            p = re.search(r'ATOMIC_POSITIONS angstrom', line)
            if p:
                scf_file.write("ATOMIC_POSITIONS bohr\n")
                eigenvec = [float(x) for x in eigenvecs[i].split()]
                #print step, i, eigvals[i]
                for j in range(natoms):
                    line = scf_in.readline()
                    pos = positions[j]
                    vec = eigenvec[3*j:3*j+3]
                    #print vec
                    eigenvec_scaled = [a * stepsize * step for a in vec]
                    #disp = sqrt(norm) * sqrt(masses[j])
                    pos = [a + b for (a,b) in zip(pos,eigenvec_scaled)]
                    print '%5e %5e %5e; %5e %5e %5e' % (vec[0],vec[1],vec[2],eigenvec_scaled[0], eigenvec_scaled[1], eigenvec_scaled[2])

                    scf_file.write("%s %7.5f %7.5f %7.5f\n" % (symbols[j], pos[0], pos[1], pos[2]) )
                print ""
                continue

            scf_file.write(line)

        ph_file.write("--\n")
        ph_file.write("&inputph\n")
        ph_file.write("  tr2_ph   =  1.0d-12\n")
        ph_file.write('  outdir   =  "./'+filename+'"\n')
        ph_file.write('  prefix   = "output"\n')
        ph_file.write('  reduce_io=.TRUE.\n')
        ph_file.write('  epsil=.TRUE.\n')
        ph_file.write('  trans=.false.\n')
        ph_file.write('  zeu=.false.\n')
        ph_file.write('/\n')
        ph_file.write('0.0 0.0 0.0\n')



#print eigvals
#print eigenvecs

