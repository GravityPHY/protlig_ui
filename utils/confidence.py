import os
import numpy as np
from Bio.PDB import PDBParser, PDBIO, Selection, NeighborSearch

def get_structure(pdb_file):
    parser = PDBParser()
    structure = parser.get_structure("PDB", pdb_file)
    return structure


def get_resi_plddt(pdb_path,resi_list,calc_type="mean"):
    raise NotImplemented

def get_plddt(pdb_code,chain_name,calc_type="mean"):
    parser = PDBParser()
    pdb_path=f"/Users/yuha1k/VisualApp/database/single_chain_single_lig/output/{pdb_code}/{pdb_code}_relaxed_plddt.pdb"
    structure = parser.get_structure("PDB", pdb_path)
    b_factors = []
    for chain in structure.get_chains():
        if chain.get_id() in chain_name:
            for residue in chain:
                for atom in residue:
                    b_factor = atom.get_bfactor()
                    if b_factor is not None:
                        b_factors.append(b_factor)
    mean_b_factor = np.mean(b_factors)
    return "{0:.2f}".format(mean_b_factor)


def select_pocket_residue(pdb_file_path, resi_id=-1, radius_cut=5.0):
    structure=get_structure(pdb_file_path)
    model=structure[0]
    ligand_atoms = [atom for atom in model.get_atoms() if "UNK" in atom.get_full_id()[3][0]]
    all_atoms = list(model.get_atoms())
    #atoms = Selection.unfold_entities(structure,'A')

    ns = NeighborSearch(all_atoms)
    near_atoms = []
    for atom in ligand_atoms:
        near_atoms.extend(ns.search(atom.get_coord(), radius_cut))
    near_residues = set(atom.get_parent() for atom in near_atoms)
    near_resi_num=[]
    for residue in near_residues:
        near_resi_num.append(residue.get_id()[1])
    return near_resi_num


