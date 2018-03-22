"""antimonene_bands.py

Antimonene band structure example for tipsi.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.append("..")
sys.path.append("../materials")
import tipsi
import black_phosphorus

def main():
    
    #########################
    # SIMULATION PARAMETERS #
    #########################
    
    # band plot resolution
    res_bands = 25
    
    # create lattice, hop_dict and pbc_wrap
    lat = black_phosphorus.lattice()
    hop_dict = black_phosphorus.hop_dict()
    
    # define symmetry points
    G = np.array([0. ,0. ,0. ])
    X = lat.reciprocal_latt()[0] / 2
    Y = lat.reciprocal_latt()[1] / 2
    S = X + Y
    kpoints = [G, Y, S, X, G]
    ticktitles = ["G","Y","S","X","G"]

    # get band structure
    kpoints, kvals, ticks = tipsi.interpolate_k_points(kpoints, res_bands)
    bands = tipsi.band_structure(hop_dict, lat, kpoints)
    for i in range(len(bands[0,:])):
        plt.plot(kvals, bands[:,i], color='k')
    for tick in ticks:
        plt.axvline(tick, color='k', linewidth=0.5)
    plt.xticks(ticks, ticktitles)
    plt.xlim((0., np.amax(kvals)))
    plt.xlabel("k (1/nm)")
    plt.ylabel("E (eV)")
    plt.savefig("bands.png")
    plt.close()

    
if __name__ == '__main__':
    main()
            
