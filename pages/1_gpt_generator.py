import streamlit as st
import pandas as pd
import pyodbc
import time
import csv
from io import BytesIO
from utils.gpt_utils import generate_output_for_group
from streamlit_searchbox import st_searchbox

# -------------------- DB Connection --------------------
def get_sql_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=mptcecommerce-sql-server.database.windows.net;"
        "Database=mptcecommerce-db;"
        "Uid=mptcadmin;"
        "Pwd=Mptc@2025;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )

@st.cache_data
def load_categories():
    conn = get_sql_connection()
    df = pd.read_sql("SELECT category_name, gpt_prompt FROM product_categories", conn)
    conn.close()
    df["category_name"] = df["category_name"].str.strip()
    return df

# -------------------- Page Setup --------------------
st.set_page_config(page_title="SEO Title & Description Generator", layout="wide")
st.title("Product Listing Generator for Marketplaces")

# -------------------- Smart Category Selection --------------------
# Load categories
load_categories.clear()
cat_df = load_categories()
category_list = cat_df["category_name"].dropna().unique().tolist()
category_list_sorted = sorted(category_list, key=lambda x: x.lower())

# Add an empty option at the top to avoid default selection
category_options = [""] + category_list_sorted

# Selection box (with no pre-selected value)
selected_category = st.selectbox(
    "🔍 Search & Select Product Category",
    options=category_options,
    index=0,
    help="Start typing to filter categories",
    placeholder="Start typing or select a product category..."
)

# Conditionally show the default prompt
if selected_category:
    default_prompt_row = cat_df[cat_df["category_name"] == selected_category]
    if not default_prompt_row.empty:
        default_prompt = default_prompt_row["gpt_prompt"].values[0]
        st.markdown("#### 📜 Default Prompt for Selected Category")
        st.text_area("Prompt:", value=default_prompt, height=280, disabled=True)
    else:
        st.warning("⚠️ No prompt found for the selected category.")
else:
    st.info("ℹ️ Please select a product category to see the default prompt.")

# -------------------- File Upload --------------------
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
df = None

# ---------- Safe GPT Retry Wrapper ----------
def safe_generate_output(group, image_link, prompt_input, retries=1, delay=1.0):
    for attempt in range(retries + 1):
        output = generate_output_for_group(group, image_link, prompt_input)
        raw_response = output.get("gpt_raw_response", "").strip()
        if raw_response and "I'm sorry" not in raw_response:
            return output
        time.sleep(delay)
    return output  # return last attempt even if bad

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip().str.replace(' +', ' ', regex=True)

    # 🔥 Remove fully empty rows and rows without SKU or Name
    df.dropna(how="all", inplace=True)
    df = df[~(df["SKU"].isna() | df["Name"].isna())]
    df = df[~((df["SKU"].astype(str).str.strip() == "") & (df["Name"].astype(str).str.strip() == ""))]
    df.reset_index(drop=True, inplace=True)

    required_info_cols = ["Size", "Colour", "Category", "Finish/ Style", "Feature",
                          "Care Instructions", "Composition", "Product Width", "Product Length", "Product Height"]

    # Add expected columns if missing
    for col in required_info_cols + ["Image Link 1", "SKU", "Name", "Brand", "Description"]:
        if col not in df.columns:
            df[col] = ""

    # Handle optional Includes column
    includes_col_present = "Includes" in df.columns
    if not includes_col_present:
        df["Includes"] = ""

    # 📊 Show Preview
    preview_cols = ["SKU", "Name"] + [col for col in required_info_cols if col in df.columns]
    if includes_col_present:
        preview_cols += ["Includes"]
    st.markdown("### Preview of Uploaded Product Data")
    st.dataframe(df[preview_cols])

    grouped = df.groupby(["Brand", "Name"])

    if st.button("Start Title & Description Generation"):
        output_rows = []
        st.session_state["final_preview_df"] = None
        st.markdown("### GPT-Generated Preview (Step 1)")

        for (brand, name), group in grouped:
            time.sleep(1.5)
            image_link = group["Image Link 1"].dropna().iloc[0] if group["Image Link 1"].dropna().any() else None

            if not image_link:
                for _, row in group.iterrows():
                    output_rows.append({
                        "SKU": row["SKU"], "Name": row["Name"], "Includes": row.get("Includes", ""),
                        "Title 1": "", "Title 2": "", "Title 3": "", "Title 4": "",
                        "Description": "", "Status": "❌ Skipped (No Image)"
                    })
                continue

            available_info_cols = [col for col in required_info_cols if col in group.columns]
            row_data = group.iloc[0]
            product_info_text = "\n".join([
                f"{k}: {v}" for k, v in row_data[available_info_cols].dropna().items()
            ])

            # Add Includes if present and not empty
            includes_value = str(row_data.get("Includes", "")).strip()
            if includes_col_present and includes_value:
                product_info_text += f"\nIncludes: {includes_value}"

            prompt_input = f"{default_prompt.strip()}\n\nProduct Info:\n{product_info_text}"

            output = safe_generate_output(group, image_link, prompt_input, retries=1, delay=1.0)

            sku = group["SKU"].dropna().iloc[0]
            name = group["Name"].dropna().iloc[0]

            st.markdown(f"---\n### 🧾 Raw GPT Output for: **{sku} – {name}**")
            st.code(output.get("gpt_raw_response", "(empty)"), language="markdown")

            for _, row in group.iterrows():
                output_rows.append({
                    "SKU": row["SKU"], "Name": row["Name"],
                    "Includes": row.get("Includes", ""),
                    "Title 1": output.get("title_map", {}).get("Title 1", ""),
                    "Title 2": output.get("title_map", {}).get("Title 2", ""),
                    "Title 3": output.get("title_map", {}).get("Title 3", ""),
                    "Title 4": output.get("title_map", {}).get("Title 4", ""),
                    "Description": output.get("desc1", ""),
                    "Status": "Generated"
                })

        gpt_df = pd.DataFrame(output_rows)

        # Merge original product info with GPT results
        info_cols = ["SKU", "Name", "Size", "Colour", "Category", "Finish/ Style", "Feature",
                     "Care Instructions", "Composition", "Product Width", "Product Length", "Product Height"]
        if includes_col_present:
            info_cols.append("Includes")

        base_df = df[info_cols].copy()
        final_preview_df = pd.merge(base_df, gpt_df, on=["SKU", "Name", "Includes"], how="left")

        # Reorder 'Includes' column to the end
        cols = [col for col in final_preview_df.columns if col != "Includes"] + ["Includes"]
        final_preview_df = final_preview_df[cols]
        
        st.markdown("### Final Preview of GPT Outputs with Product Data")
        st.dataframe(final_preview_df)
        
        st.session_state["final_preview_df"] = final_preview_df

    # -------------------- Preserve & Download Output --------------------
    if "final_preview_df" in st.session_state and st.session_state["final_preview_df"] is not None:
        csv_buffer = BytesIO()
        st.session_state["final_preview_df"].to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)
        st.download_button(
            "⬇️ Download GPT Output",
            data=csv_buffer.getvalue(),
            file_name="gpt_preview.csv",
            mime="text/csv"
        )
