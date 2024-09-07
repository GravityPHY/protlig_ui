import streamlit as st

st.markdown("# Internship at Discovery Sciences, Data Science Team of Novartis Institutes for BioMedical Research (NIBR)")
st.markdown("##### June 3rd - August 9th")
st.markdown("##### Author: Hao Yu")
st.markdown("##### Affliation: Electrical and Computer Engineering, Boston University")
st.markdown("##### Contact: imhaoyu@bu.edu")
st.markdown("## Background")
st.write(open("./txt/introduction.txt").read())
st.markdown("## Project Overview")
st.write()
st.markdown("## Summary")
st.image(["./figures/umol-plddt.png","./figures/rfaa-plddt.png"])
st.markdown("### References")
st.write("1. Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold. Nature. 2021")
st.write("2. Bryant, P. et al. Structure prediction of protein-ligand complexes from sequence information with Umol. Nat. Commun. 2024")
st.write("3. Krishna, R. et al. Generalized biomolecular modeling and design with RoseTTAFold All-Atom. Science. 2024")
st.markdown("### Acknowledgement")
st.write("This internship project is supported by the Professional Development & Postdoctoral Affairs National Science Foundation Innovations in Graduate Education from Boston University. \n I would like to thank supervision from my mentors Jian Fang, Dave Barkan, Lingling Shen, Roman Sloutsky, Christian Schleberger and Peter Kutchukian.")




