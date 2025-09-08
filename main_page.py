import os
import io
import streamlit as st
import pandas as pd
import numpy as np
from tempfile import NamedTemporaryFile
import py3Dmol
from stmol import showmol

# Import our RAG pipeline
from rag_pipeline import initialize_rag_pipeline

# Assuming these exist in your project
from utils import dataframes, confidence

# Environment setup
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


# Initialize session state for RAG pipeline
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = None


def gather_structure_data(temp_file_path, hl_ligand, hl_pocket, hl_chain, hl_resi_list):
    """Gather structural analysis data into a formatted string"""
    structure_summary = "=== PROTEIN STRUCTURE ANALYSIS ===\n"

    try:
        # Basic info
        structure_summary += f"• Analyzed Chain: {hl_chain}\n"
        #structure_summary += f"• Highlighted Residues: {len(hl_resi_list)} residues\n"

        # Ligand analysis
        if hl_ligand:
            try:
                ligand_df = dataframes.get_resi_bfactor(temp_file_path, resi_name=["UNK", "LIG", "LG1"])
                if not ligand_df.empty:
                    avg_confidence = ligand_df['Prediction Confidence'].mean()
                    min_confidence = ligand_df['Prediction Confidence'].min()
                    max_confidence = ligand_df['Prediction Confidence'].max()

                    structure_summary += f"\n=== LIGAND BINDING ANALYSIS ===\n"
                    structure_summary += f"• Average Prediction Confidence: {avg_confidence:.2f}\n"
                    structure_summary += f"• Confidence Range: {min_confidence:.2f} - {max_confidence:.2f}\n"

                    # Confidence interpretation
                    if avg_confidence >= 80:
                        reliability = "HIGH - 80% chance of accurate prediction"
                    elif avg_confidence >= 60:
                        reliability = "MODERATE - 50% chance of accurate prediction"
                    elif avg_confidence >= 0:
                        reliability = "LOW - 10% chance of accurate prediction"
                    else:
                        reliability = "UNDEFINED - requires validation"

                    structure_summary += f"• Reliability Assessment: {reliability}\n"
                else:
                    structure_summary += "\n=== LIGAND BINDING ANALYSIS ===\n"
                    structure_summary += "• No ligand data available\n"
            except Exception as e:
                structure_summary += f"\n=== LIGAND BINDING ANALYSIS ===\n"
                structure_summary += f"• Error analyzing ligand: {e}\n"

        # Pocket analysis
        if hl_pocket:
            try:
                pocket_resi_list, pocket_resname_list = confidence.select_pocket_residue(temp_file_path)
                pocket_df = dataframes.get_resi_bfactor(temp_file_path, resi_list=pocket_resi_list)
                if not pocket_df.empty:
                    avg_pocket_confidence = pocket_df['pLDDT'].mean()
                    structure_summary += f"\n=== BINDING POCKET ANALYSIS ===\n"
                    structure_summary += f"• Average Pocket Confidence (pLDDT): {avg_pocket_confidence:.2f}\n"
                    structure_summary += f"• Number of pocket residues: {len(pocket_resi_list)}\n"
                    structure_summary += f"• Binding Residues: {','.join(pocket_resname_list)}\n"
                else:
                    structure_summary += f"\n=== BINDING POCKET ANALYSIS ===\n"
                    structure_summary += "• No pocket data available\n"
            except Exception as e:
                structure_summary += f"\n=== BINDING POCKET ANALYSIS ===\n"
                structure_summary += f"• Error analyzing pocket: {e}\n"

    except Exception as e:
        structure_summary += f"\nError in structure analysis: {e}\n"

    return structure_summary


# Streamlit App
st.set_page_config(page_title="Protein Structure + Literature Analysis", layout="wide")
st.markdown("# Protein Structure + Literature Analysis")
st.markdown("*Analyze protein structures with integrated literature insights*")

# Initialize RAG pipeline
if st.session_state.rag_pipeline is None:
    st.session_state.rag_pipeline = initialize_rag_pipeline()

rag_pipeline = st.session_state.rag_pipeline

# Sidebar for file uploads and settings
st.sidebar.title("📁 Upload Files")

# PDB file upload
pdb_file = st.sidebar.file_uploader("Choose a PDB file", type=['pdb'])
pdb_code = st.sidebar.text_input("Or enter PDB Code", value=None)

# PDF upload for RAG
st.sidebar.markdown("---")
st.sidebar.markdown("**📚 Literature Analysis (Optional)**")

if rag_pipeline is None:
    st.sidebar.error("⚠️ RAG pipeline not initialized. Please provide OpenAI API key.")
else:
    st.sidebar.success("✅ RAG pipeline ready")

pdf_docs = st.sidebar.file_uploader(
    "Upload PDF literature (max 10MB each)",
    accept_multiple_files=True,
    type=['pdf'],
    help="Upload relevant research papers for contextual analysis"
)

# Process PDFs if uploaded
literature_available = False
if pdf_docs and rag_pipeline:
    if st.sidebar.button("📖 Process Literature"):
        with st.sidebar.spinner("Processing PDFs..."):
            success, message = rag_pipeline.process_literature(pdf_docs)
            if success:
                st.sidebar.success(message)
                literature_available = True
            else:
                st.sidebar.error(message)

# Check if literature is already available
if rag_pipeline and rag_pipeline.is_literature_available():
    literature_available = True
    st.sidebar.info("📚 Literature database ready")

# Visualization settings
st.sidebar.markdown("---")
st.sidebar.title("🔧 View Settings")
surf_transp = st.sidebar.slider("Surface Transparency", 0.0, 1.0, 0.5)
hl_chain = st.sidebar.text_input("Highlight Chain", value="A")
hl_resi_list = st.sidebar.multiselect("Highlight Residues", options=list(range(1, 100)))
hl_pocket = st.sidebar.checkbox("Highlight Pocket", value=False)
hl_ligand = st.sidebar.checkbox("Highlight Ligand", value=False)
hl_color = st.sidebar.text_input("Highlight Color", value="red")
bb_color = st.sidebar.text_input("Backbone Color", value="orange")
lig_color = st.sidebar.text_input("Ligand Color", value="white")

# Main layout
col1, col2 = st.columns([2.5, 1.5])

with col1:
    st.subheader("🧬 3D Structure Visualization")

    # Setup 3D visualization
    width, height = 700, 600
    cartoon_radius, stick_radius = 0.2, 0.2

    if pdb_file:
        with NamedTemporaryFile(delete=False, suffix=".pdb") as temp_file:
            temp_file.write(pdb_file.getvalue())
            temp_file_path = temp_file.name
        view = py3Dmol.view(width=width, height=height)
        view.addModel(pdb_file.getvalue().decode("utf-8"))
        view.zoomTo()

    elif pdb_code:
        view = py3Dmol.view(query=f"pdb:{pdb_code.lower()}", width=width, height=height)
        temp_file_path = f"{pdb_code.lower()}.pdb"  # This might need special handling

    else:
        # Default structure
        view = py3Dmol.view(width=width, height=height)
        pdb_file_path = "./showcase/8SLG_relaxed_plddt.pdb"
        with io.open(pdb_file_path, mode="r", encoding="utf-8") as f:
            pdb_content = f.read()
        temp_file_path = pdb_file_path
        view.addModel(pdb_content)
        view.zoomTo()

    # Apply styling
    view.setStyle({"cartoon": {"style": "oval", "color": bb_color, "thickness": cartoon_radius}})
    view.addSurface(py3Dmol.VDW, {"opacity": surf_transp, "color": bb_color}, {"hetflag": False})
    view.addStyle({"elem": "C", "hetflag": True}, {"stick": {"color": lig_color, "radius": stick_radius}})
    view.addStyle({"hetflag": True}, {"stick": {"radius": stick_radius}})

    if hl_pocket:
        view.addStyle({'within': {'distance': '5.5', 'sel': {'resn': 'UNK', "elem": "C"}}},
                      {'stick': {'colorscheme': 'white', "radius": stick_radius}})

    for hl_resi in hl_resi_list:
        view.addStyle({"chain": hl_chain, "resi": hl_resi, "elem": "C"},
                      {"stick": {'colorscheme': "white", "radius": stick_radius}})

    showmol(view, height=height, width=width)

with col2:
    st.subheader("📊 Confidence Metrics")

    if 'temp_file_path' in locals():
        try:
            if hl_pocket:
                pocket_resi_list, pocket_resname_list = confidence.select_pocket_residue(temp_file_path)
                pocket_df = dataframes.get_resi_bfactor(temp_file_path, resi_list=pocket_resi_list)
                st.write("**Pocket Residues**")
                st.dataframe(pocket_df, height=200)

            if hl_ligand:
                ligand_df = dataframes.get_resi_bfactor(temp_file_path, resi_name=["UNK", "LIG", "LG1"])
                st.write("**Ligand Confidence**")
                st.dataframe(ligand_df, height=200)

        except Exception as e:
            st.error(f"Error loading confidence data: {e}")
    else:
        st.info("Load a PDB structure to see confidence metrics")

# Analysis Section
st.markdown("---")

# Two-column layout for analysis
analysis_col1, analysis_col2 = st.columns([1, 1])

with analysis_col1:
    st.subheader("🤖 AI-Powered Analysis")

    # Generate analysis button
    if st.button("🔬 Generate Structure Analysis", type="primary", use_container_width=True):
        if not rag_pipeline:
            st.error("RAG pipeline not available. Please check your OpenAI API key.")
        elif 'temp_file_path' not in locals():
            st.error("No protein structure loaded")
        else:
            with st.spinner("Analyzing structure and searching literature..."):
                # Gather structural data
                structure_data = gather_structure_data(
                    temp_file_path, hl_ligand, hl_pocket, hl_chain, hl_resi_list
                )

                # Generate analysis
                if literature_available:
                    # Search literature for relevant context
                    literature_query = f"protein ligand binding confidence prediction accuracy validation {hl_chain}"
                    literature_context = rag_pipeline.search_literature(literature_query)

                    analysis = rag_pipeline.generate_analysis_with_gpt(
                        structure_data, literature_context, has_literature=True
                    )
                    st.success("✅ Analysis generated with literature context")
                else:
                    analysis = rag_pipeline.generate_analysis_with_gpt(
                        structure_data, has_literature=False
                    )
                    st.info("ℹ️ Analysis generated without literature context")

                # Display results
                st.markdown("### 📋 Analysis Report")
                st.markdown(analysis)

with analysis_col2:
    st.subheader("💬 Interactive Q&A")

    if literature_available and rag_pipeline:
        st.success("📚 Literature-enhanced Q&A available")

        user_question = st.text_input(
            "Ask about your structure + literature:",
            placeholder="e.g., What does literature say about this confidence score?"
        )

        if user_question and st.button("🔍 Get Answer", use_container_width=True):
            with st.spinner("Searching literature and generating answer..."):
                # Get current structure context
                if 'temp_file_path' in locals():
                    structure_context = gather_structure_data(
                        temp_file_path, hl_ligand, hl_pocket, hl_chain, hl_resi_list
                    )
                else:
                    structure_context = "No structure currently loaded"

                # Generate answer
                answer = rag_pipeline.answer_question(user_question, structure_context)

                st.markdown("### 💡 Answer")
                st.markdown(answer)

    elif rag_pipeline:
        st.info("📚 Upload and process literature PDFs to enable Q&A")

        # Basic structure-only Q&A
        user_question = st.text_input(
            "Ask about structure analysis:",
            placeholder="e.g., What do these confidence scores mean?"
        )

        if user_question and st.button("🔍 Get Answer", use_container_width=True):
            with st.spinner("Generating answer..."):
                if temp_file_path:
                    structure_context = gather_structure_data(
                        temp_file_path, hl_ligand, hl_pocket, hl_chain, hl_resi_list
                    )

                    # Generate structure-only answer
                    answer = rag_pipeline.generate_analysis_with_gpt(
                        f"Question: {user_question}\n\nContext: {structure_context}"
                    )

                    st.markdown("### 💡 Answer")
                    st.markdown(answer)
                else:
                    st.error("No structure loaded for analysis")

    else:
        st.warning("⚠️ Q&A requires OpenAI API key")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <small>Built with Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)