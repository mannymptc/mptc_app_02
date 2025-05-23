import streamlit as st
import pandas as pd
import dropbox
import pyodbc

# --- Page Setup ---
st.set_page_config(layout="wide")
st.markdown("""
    <h3 style='margin-bottom: 10px;'>📤 Upload Product Images to Dropbox</h3>
""", unsafe_allow_html=True)

# --- Load secrets ---
DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# --- SQL Utilities ---
def get_product_listing_filters():
    conn = pyodbc.connect(st.secrets["AZURE_SQL"])
    df = pd.read_sql("SELECT DISTINCT Category, Name, Colour FROM product_listings", conn)
    conn.close()
    return df

def insert_into_db(df):
    conn = pyodbc.connect(st.secrets["AZURE_SQL"])
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("INSERT INTO dropbox_links (group_name, dropbox_url) VALUES (?, ?)",
                       row["Group Name"], row["Dropbox URL"])
    conn.commit()
    cursor.close()
    conn.close()

def format_folder_segment(text):
    return ''.join(word.capitalize() for word in text.strip().split())

# --- Step 1: Filter Inputs ---
product_df = get_product_listing_filters()

category_options = sorted(product_df['Category'].dropna().unique())
selected_category = st.selectbox("Select Category", category_options)

name_options = sorted(product_df[product_df['Category'] == selected_category]['Name'].dropna().unique())
selected_name = st.selectbox("Select Name", name_options)

colour_options = sorted(product_df[
    (product_df['Category'] == selected_category) &
    (product_df['Name'] == selected_name)
]['Colour'].dropna().unique())
selected_colour = st.selectbox("Select Colour", colour_options)

group_name = f"{format_folder_segment(selected_category)}-{format_folder_segment(selected_name)}-{format_folder_segment(selected_colour)}"
st.markdown(f"📁 **Folder Preview**: `{group_name}`")

# --- Step 2: Upload Images ---
uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.subheader("🖼️ Image Previews")
    for img in uploaded_files:
        st.image(img, width=150, caption=img.name)

# --- Step 3: Upload to Dropbox ---
if st.button("🚀 Confirm & Upload to Dropbox"):
    if uploaded_files and group_name:
        folder_path = f"/{group_name}"
        results = []

        for file in uploaded_files:
            image_bytes = file.read()
            dropbox_path = f"{folder_path}/{file.name}"

            # Upload image
            dbx.files_upload(image_bytes, dropbox_path, mode=dropbox.files.WriteMode.overwrite)

            # Generate public link
            try:
                link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
                public_url = link.url.replace("?dl=0", "?raw=1")
            except dropbox.exceptions.ApiError:
                links = dbx.sharing_list_shared_links(path=dropbox_path).links
                public_url = links[0].url.replace("?dl=0", "?raw=1") if links else "Error"

            results.append({
                "Group Name": group_name,
                "Dropbox URL": public_url
            })

        result_df = pd.DataFrame(results)

        st.success("✅ Uploaded and links generated!")
        st.subheader("🔗 Dropbox Image Links")
        st.dataframe(result_df)

        # CSV Download Button
        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv_data, file_name=f"{group_name}_links.csv", mime="text/csv")

# --- Step 4: Manual Upload into Database ---
st.markdown("---")
st.subheader("📂 Upload Dropbox CSV into Database")

csv_upload = st.file_uploader("Upload CSV file exported from above", type=["csv"], key="csv_db_upload")

if csv_upload:
    csv_df = pd.read_csv(csv_upload)
    st.dataframe(csv_df)

    if st.button("🗃️ Insert Uploaded CSV into Azure SQL Database"):
        insert_into_db(csv_df)
        st.success("✅ Successfully inserted into `dropbox_links` table")
