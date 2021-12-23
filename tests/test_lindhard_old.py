#! /usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt

import tbplas as tb
from tbplas.lindhard_old import Lindhard


def main():
    # Construct primitive cell
    cell = tb.make_graphene_diamond()
    t = 2.7  # Absolute hopping energy
    a = 0.142  # C-C distance in NM

    # Setting parameters
    en_range = 10
    step = 2048
    mesh = 1200
    mu = 0.0
    temp = 300
    back_epsilon = 1
    # q-point for reproducing Phys. Rev. B 84, 035439 (2011)
    # |q| = 1/a with theta = 30 degrees
    q_points = [[6.09877042, 3.52112676, 0.]]

    # Calculating with lindhard function
    lindhard = Lindhard(cell, en_range, step, mesh, mu, temp, back_epsilon)
    omegas, dyn_pol = lindhard.DP_qpoints(q_points)

    # Plot
    omegas = np.array(omegas)
    for i in range(len(q_points)):
        plt.plot(omegas/t, -dyn_pol.imag[i])
    plt.savefig("lindhard_im_dyn_pol.png")
    plt.close()


if __name__ == '__main__':
    main()
