import numpy as np
import pandas as pd
from Bio.PDB import PDBParser, PDBIO

def get_pdb_df(pdb_file_path):
    parser = PDBParser()
    structure = parser.get_structure("PDB", pdb_file_path)
    df_data = []
    for model in structure:
        for chain in model:
            for residue in chain:
                atom_bfactor=[]
                for atom in residue:
                    atom_bfactor.append(atom.get_bfactor())
                df_data.append({"Residue Number":residue.get_id()[1],"Residue Name": residue.get_resname(),
                             "pLDDT": np.mean(atom_bfactor)})
    df = pd.DataFrame(df_data)
    return df

def get_resi_bfactor(pdb_file_path, resi_list=None, resi_name=None):
    df=get_pdb_df(pdb_file_path)
    if resi_list:
        tmp_df = df[df["Residue Number"].isin(resi_list)]
        return tmp_df
    if resi_name:
        tmp_df = df[df["Residue Name"].isin(resi_name)]
        return tmp_df
    else:
        return df







