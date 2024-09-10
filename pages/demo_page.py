import io
import streamlit as st
import pandas as pd
import numpy as np
from tempfile import NamedTemporaryFile

import py3Dmol
from stmol import showmol

from utils import dataframes, confidence


st.markdown("# Demo")

st.sidebar.title("Upload File")
pdb_file =st.sidebar.file_uploader("Choose a file",type=['pdb'])

pdb_code = st.sidebar.text_input(
        label="PDB Code",
        value=None,
    )

#if pdb_file:
#   with NamedTemporaryFile(delete=False, suffix=".pdb") as temp_file:
#        temp_file.write(pdb_file.getvalue())
#        temp_file_path = temp_file.name
        
#    st_molstar(temp_file_path, height=600)
#elif pdb_code:
#    st_molstar_rcsb(pdb_code, height=600,key='3')
#else:
#    st.write("Please enter a PDB code or upload a PDB file.")


st.sidebar.title("View Settings")
surf_transp = st.sidebar.slider("Surface Transparency", min_value=0.0, max_value=1.0, value=0.5)

hl_chain = st.sidebar.text_input(label="Highlight Chain",value="A")

hl_resi_list = st.sidebar.multiselect(label="Highlight Residues",options=list(range(1,5000)))

label_resi = st.sidebar.checkbox(label="Label Residues", value=True)

hl_pocket = st.sidebar.checkbox(label="Highlight Pocket", value=False)
hl_ligand = st.sidebar.checkbox(label="Highlight Ligand", value=False)

hl_color = st.sidebar.text_input(label="Highlight Color",value="red")

bb_color = st.sidebar.text_input(label="Backbone Color",value="spectrum")
lig_color = st.sidebar.text_input(label="Ligand Color",value="white")
### Step 3) Py3Dmol

width = 700
height = 700

cartoon_radius = 0.2
stick_radius = 0.2

if pdb_file:
    with NamedTemporaryFile(delete=False, suffix=".pdb") as temp_file:
        temp_file.write(pdb_file.getvalue())
        temp_file_path = temp_file.name
    view=py3Dmol.view(width=width, height=height)
    view.addModel(pdb_file.getvalue().decode("utf-8"))
    view.zoomTo()
    
elif pdb_code:
    view = py3Dmol.view(query=f"pdb:{pdb_code.lower()}", width=width, height=height)

else:
    view = py3Dmol.view(width=width, height=height)
    pdb_file="./showcase/8SLG_relaxed_plddt.pdb"
    temp_file = io.open(pdb_file, mode="r", encoding="utf-8")
    temp_file_path = pdb_file
    view.addModel(temp_file.read())
    view.zoomTo()
    
    


view.setStyle({"cartoon": {"style": "oval","color": bb_color,"thickness": cartoon_radius}})
view.addSurface(py3Dmol.VDW, {"opacity": surf_transp, "color": bb_color},{"hetflag": False})
view.addStyle({"elem": "C", "hetflag": True},
                {"stick": {"color": lig_color, "radius": stick_radius}})
view.addStyle({"hetflag": True},
                    {"stick": {"radius": stick_radius}})

if hl_pocket:
    view.addStyle({'within':{'distance':'5.5', 'sel':{'resn':'UNK',"elem": "C"}}}, 
    {'stick': {'colorscheme':'white', "radius": stick_radius}})


for hl_resi in hl_resi_list:
    view.addStyle({"chain": hl_chain, "resi": hl_resi, "elem": "C"},
    {"stick": {'colorscheme': "white", "radius": stick_radius}})


showmol(view, height=height, width=width)

st.title("Prediction Confidence")

col2, col3 = st.columns(2)
#if pdb_file:
#    col1.write("All residues")
#    pddf=dataframes.get_resi_bfactor(temp_file_path)
#    col1.dataframe(pddf) 
    #col1.write("All residues statistics")
    #col1.dataframe(pddf['pLDDT'].describe()) 

if hl_pocket:
    col2.write("Pocket")
    pocket_resi_list=confidence.select_pocket_residue(temp_file_path)
    col2.dataframe(dataframes.get_resi_bfactor(temp_file_path, resi_list=pocket_resi_list)) 
    col2.write("Pocket Statistics")
    col2.dataframe(dataframes.get_resi_bfactor(temp_file_path, resi_list=pocket_resi_list).describe()) 

if hl_ligand:
    col3.write("Ligand")
    col3.dataframe(dataframes.get_resi_bfactor(temp_file_path, resi_name=["UNK","LIG","LG1"]))

 



    
