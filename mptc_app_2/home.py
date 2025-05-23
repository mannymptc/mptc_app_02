import streamlit as st

st.set_page_config(page_title="🧠 MPTC Listing Assistant", layout="wide")
st.title("🧠 MPTC Products Listing Assistant")

# -------------------------------------
st.markdown("## 🚀 Welcome!")
st.markdown("""
This powerful assistant helps you manage and automate your e-commerce product listings and backend tasks across marketplaces like **Amazon, eBay, TikTok Shop, Tesco, Wilko**, and more.

### What you can do:
- ✅ Generate SEO-optimized product **titles & descriptions** using GPT
- ✅ Access, edit, and insert data into your **Azure SQL product tables**
- ✅ Generate **product barcodes** for new SKUs (🚧 Coming Soon)
""")

# -------------------------------------
st.markdown("## 📂 Navigate to a Module")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_gpt_generator.py", label="1) Title & Description Generator", icon="🛍️")

with col2:
    st.page_link("pages/2_channel_specific.py", label="3) Channel Specific Generator", icon="✍🏻")

with col3:
    st.page_link("pages/3_database_access.py", label="2) Database Access & Editor", icon="🗃️")

with col4:
    st.page_link("pages/4_barcode_generator.py", label="3) Barcode Generator", icon="📦")

# -------------------------------------
st.markdown("---")
st.markdown("👤 **Built by Mantavya Jain** ")
