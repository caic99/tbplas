"""
Functions and classes for constructing samples.

Functions
---------
    extend_prim_cell: user function
        extend primitive cell along a, b, and c directions
        reserved for compatibility with old version of TBPlaS
    reshape_prim_cell: user function
        reshape primitive cell to given lattice vectors and origin
    trim_prim_cell: user function
        trim dangling orbitals and associated hopping terms
    apply_pbc: user function
        apply periodic boundary conditions on primitive cell by removing hopping
        terms between cells along non-periodic direction

Classes
-------
    None.
"""

import math

import numpy as np

from . import constants as consts
from . import exceptions as exc
from .primitive import correct_coord, PrimitiveCell


def extend_prim_cell(prim_cell: PrimitiveCell, dim=(1, 1, 1)):
    """
    Extend primitive cell along a, b and c directions.

    :param prim_cell: instance of 'PrimitiveCell'
        primitive cell from which the extended cell is constructed
    :param dim: (na, nb, nc)
        dimension of the extended cell along 3 directions
    :return: extend_cell: instance of 'PrimitiveCell'
        extended cell created from primitive cell
    :raises CoordLenError: if len(dim) != 2 or 3
    :raises ValueError: if dimension along any direction is smaller than 1
    """
    # Check the dimension of extended cell
    dim = correct_coord(dim, complete_item=1)
    for i_dim in range(len(dim)):
        if dim[i_dim] < 1:
            raise ValueError(f"Dimension along direction {i_dim} should not"
                             f" be smaller than 1")

    # Extend lattice vectors
    lat_vec_ext = prim_cell.lat_vec.copy()
    for i_dim in range(3):
        lat_vec_ext[i_dim] *= dim[i_dim]

    # Create extended cell and add orbitals
    extend_cell = PrimitiveCell(lat_vec_ext, unit=consts.NM)
    extend_cell.extended *= np.prod(dim)
    orb_id_pc, orb_id_sc = [], {}
    id_sc = 0
    for i_a in range(dim[0]):
        for i_b in range(dim[1]):
            for i_c in range(dim[2]):
                for i_o, orbital in enumerate(prim_cell.orbital_list):
                    id_pc = (i_a, i_b, i_c, i_o)
                    orb_id_pc.append(id_pc)
                    orb_id_sc[id_pc] = id_sc
                    id_sc += 1
                    pos_ext = [(orbital.position[0] + i_a) / dim[0],
                               (orbital.position[1] + i_b) / dim[1],
                               (orbital.position[2] + i_c) / dim[2]]
                    extend_cell.add_orbital(pos_ext, orbital.energy)

    # Define periodic boundary condition.
    def _wrap_pbc(ji, ni):
        return ji % ni, ji // ni

    # Add hopping terms
    for id_sc_i in range(extend_cell.num_orb):
        id_pc_i = orb_id_pc[id_sc_i]
        for hopping in prim_cell.hopping_list:
            hop_ind = hopping.index
            if id_pc_i[3] == hop_ind[3]:
                ja, na = _wrap_pbc(id_pc_i[0] + hop_ind[0], dim[0])
                jb, nb = _wrap_pbc(id_pc_i[1] + hop_ind[1], dim[1])
                jc, nc = _wrap_pbc(id_pc_i[2] + hop_ind[2], dim[2])
                id_pc_j = (ja, jb, jc, hop_ind[4])
                id_sc_j = orb_id_sc[id_pc_j]
                rn = (na, nb, nc)
                extend_cell.add_hopping(rn, id_sc_i, id_sc_j, hopping.energy)

    extend_cell.sync_array()
    return extend_cell


def reshape_prim_cell(prim_cell: PrimitiveCell, lat_frac: np.ndarray,
                      origin: np.ndarray = np.zeros(3),
                      delta=0.01, pos_tol=1e-5):
    """
    Reshape primitive cell to given lattice vectors and origin.

    :param prim_cell: instance of 'PrimitiveCell' class
        primitive cell from which the reshaped cell is constructed
    :param lat_frac: (3, 3) float64 array
        FRACTIONAL coordinates of lattice vectors of reshaped cell in basis
        vectors of primitive cell
    :param origin: (3,) float64 array
        FRACTIONAL coordinates of origin of reshaped cell in basis vectors
        of reshaped cell
    :param delta: float64
        small parameter to add to origin such that orbitals fall on cell
        borders will not be clipped
        This parameter will be subtracted from orbital positions of reshaped
        cell. So the origin is still correct.
    :param pos_tol: float64
        tolerance on positions for identifying equivalent orbitals
    :return: res_cell: instance of 'PrimitiveCell' class
        reshaped cell
    :raises LatVecError: if lat_frac.shape != (3, 3)
    :raises ValueError: if origin.shape != (3,)
    """
    # Check lattice vectors and origin
    if lat_frac.shape != (3, 3):
        raise exc.LatVecError()
    if origin.shape != (3,):
        raise ValueError("Length of origin is not 3")

    # Conversion matrix of fractional coordinates from primitive cell to
    # reshaped cell: x_res = x_prim * conv_mat, with x_new and x_prim
    # being ROW vectors
    conv_mat = np.linalg.inv(lat_frac)

    # Function for getting cell index from fractional coordinates
    def _get_cell_index(x):
        return math.floor(x.item(0)), math.floor(x.item(1)), \
               math.floor(x.item(2))

    # Create reshaped cell
    lat_cart = np.zeros((3, 3), dtype=np.float64)
    for i_dim in range(3):
        lat_cart[i_dim] = np.matmul(lat_frac[i_dim], prim_cell.lat_vec)
    res_cell = PrimitiveCell(lat_cart, unit=1.0)

    # Add orbitals
    prim_cell.sync_array()
    rn_range = np.zeros((3, 2), dtype=np.int32)
    for i_dim in range(3):
        sum_vec = lat_frac.sum(axis=0) - lat_frac[i_dim]
        for j_dim in range(3):
            rn_range[j_dim, 0] = min(rn_range.item(j_dim, 0),
                                     math.floor(sum_vec[j_dim]))
            rn_range[j_dim, 1] = max(rn_range.item(j_dim, 1),
                                     math.ceil(sum_vec[j_dim]))
    rn_range[:, 0] -= 1
    rn_range[:, 1] += 1

    orb_id_pc, orb_id_sc = [], {}
    id_sc = 0
    for i_a in range(rn_range.item(0, 0), rn_range.item(0, 1)+1):
        for i_b in range(rn_range.item(1, 0), rn_range.item(1, 1)+1):
            for i_c in range(rn_range.item(2, 0), rn_range.item(2, 1)+1):
                rn = (i_a, i_b, i_c)
                for i_o, pos in enumerate(prim_cell.orb_pos):
                    res_pos = np.matmul(rn + pos, conv_mat) - origin + delta
                    res_rn = _get_cell_index(res_pos)
                    if res_rn == (0, 0, 0):
                        id_pc = (i_a, i_b, i_c, i_o)
                        orb_id_pc.append(id_pc)
                        orb_id_sc[id_pc] = id_sc
                        id_sc += 1
                        res_cell.add_orbital(res_pos,
                                             prim_cell.orb_eng.item(i_o))

    # Add hopping terms
    res_cell.sync_array()
    for id_sc_i in range(res_cell.num_orb):
        id_pc_i = orb_id_pc[id_sc_i]
        for i_h, hop in enumerate(prim_cell.hop_ind):
            if id_pc_i[3] == hop.item(3):
                # Get fractional coordinate of id_sc_j in reshaped cell
                rn = id_pc_i[:3] + hop[:3]
                pos = prim_cell.orb_pos[hop.item(4)]
                res_pos = np.matmul(rn + pos, conv_mat) - origin + delta

                # Wrap back into (0, 0, 0)-th reshaped cell
                res_rn = _get_cell_index(res_pos)
                res_pos -= res_rn

                # Determine corresponding id_sc_j
                for id_pc_j in orb_id_pc:
                    if id_pc_j[3] == hop.item(4):
                        id_sc_j = orb_id_sc[id_pc_j]
                        chk_pos = res_cell.orb_pos[id_sc_j]
                        if np.linalg.norm(chk_pos - res_pos) <= pos_tol:
                            res_cell.add_hopping(res_rn, id_sc_i, id_sc_j,
                                                 prim_cell.hop_eng[i_h])

    # Subtract delta from orbital positions
    res_cell.orb_pos -= delta
    for i_o, pos in enumerate(res_cell.orb_pos):
        res_cell.orbital_list[i_o].position = tuple(pos)
    res_cell.sync_array()
    return res_cell


def trim_prim_cell(prim_cell: PrimitiveCell):
    """
    Trim dangling orbitals and associated hopping terms.

    :param prim_cell: instance of 'PrimitiveCell' class
        primitive cell to trim
    :return: None
        Incoming prim_cell is modified.
    """
    # Count the number of hopping terms of each orbital
    hop_count = np.zeros(prim_cell.num_orb, dtype=np.int32)
    for hop in prim_cell.hopping_list:
        hop_count[hop.index[3]] += 1
        hop_count[hop.index[4]] += 1

    # Get indices of orbitals to remove
    orb_id_trim = [i_o for i_o, count in enumerate(hop_count) if count <= 1]

    # Remove orbitals and hopping terms
    # Orbital indices should be sorted in increasing order.
    orb_id_trim = sorted(orb_id_trim)
    for i, orb_id in enumerate(orb_id_trim):
        prim_cell.remove_orbital(orb_id - i)
    prim_cell.sync_array()


def apply_pbc(prim_cell: PrimitiveCell, pbc=(True, True, True)):
    """
    Apply periodic boundary conditions on primitive cell by removing hopping
    terms between cells along non-periodic direction.

    :param prim_cell: instance of 'PrimitiveCell' class
        primitive on which pbc will be applied
    :param pbc: tuple of 3 booleans
        whether pbc is enabled along 3 directions
    :return: None
        Incoming prim_cell is modified.
    :raises ValueError: if len(pbc) != 3
    """
    if len(pbc) != 3:
        raise ValueError("Length of pbc is not 3")

    # Get the list of hopping terms to keep
    hop_to_keep = []
    for hop in prim_cell.hopping_list:
        to_keep = True
        for i_dim in range(3):
            if not pbc[i_dim] and hop.index[i_dim] != 0:
                to_keep = False
                break
        if to_keep:
            hop_to_keep.append(hop)

    # Reset hopping_list
    prim_cell.hopping_list = hop_to_keep
    prim_cell.sync_array()
