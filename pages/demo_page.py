import os
import io
import replicate
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

generate_text = st.sidebar.checkbox(label="Generate analysis report", value=False)

hl_color = st.sidebar.text_input(label="Highlight Color",value="red")

bb_color = st.sidebar.text_input(label="Backbone Color",value="orange")
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


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run(llm,
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
    return output

st.title('🦙💬 How to understand prediction confidence?')
if 'REPLICATE_API_TOKEN' in st.secrets:
    st.success('API key already provided!', icon='✅')
    replicate_api = st.secrets['REPLICATE_API_TOKEN']
else:
    replicate_api = st.text_input('Enter Replicate API token:', type='password')
    if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
        st.warning('Please enter your credentials!', icon='⚠️')
    else:
        st.success('Proceed to entering your prompt message!', icon='👉')
#selected_model == 'Llama2-7B'
llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'

temperature = 0.1  # st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
top_p = 0.9  # st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
max_length = 512  # st.sidebar.slider('max_length', min_value=64, max_value=4096, value=512, step=8)

os.environ['REPLICATE_API_TOKEN'] = replicate_api


if generate_text:
    ligand_confidence=dataframes.get_resi_bfactor(temp_file_path, resi_name=["UNK","LIG","LG1"])
    prompt=f"Can you help me answer the question with the following information? From my project, I found that if the prediction confidence is above 80, than there is 80% percent chance the complex prediction is accurate; " \
           f"if the prediction confidence is below 80 but above 60, there is 50% chance the prediction is accurate. " \
           f"In the other cases, there is 10% chance the prediction is accurate." \
           f"Now the prediction confidence is {ligand_confidence['Prediction Confidence']}, tell me how accurate this prediction is? Just tell me the result, no need to show the analyzing steps"
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)






# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
#for message in st.session_state.messages:
#    with st.chat_message(message["role"]):
#        st.write(message["content"])

#
# User-provided prompt
#if prompt := st.chat_input(disabled=not replicate_api):
#    st.session_state.messages.append({"role": "user", "content": prompt})
#    with st.chat_message("user"):
#        st.write(prompt)

## Generate a new response if last message is not from assistant
#if st.session_state.messages[-1]["role"] != "assistant":
#    with st.chat_message("assistant"):
#        with st.spinner("Thinking..."):
#            response = generate_llama2_response(prompt)
#            placeholder = st.empty()
#            full_response = ''
#            for item in response:
#                full_response += item
#                placeholder.markdown(full_response)
#            placeholder.markdown(full_response)
#    message = {"role": "assistant", "content": full_response}
#    st.session_state.messages.append(message)
