import streamlit as st
import pandas as pd
import pyodbc
from io import BytesIO

# -------------------------------------
template_cols = {
    "product_categories": ["category_id", "category_name", "gpt_prompt"],
    "product_listings": [
        "SKU", "Name", "Size", "Colour", "Category", "Finish/ Style", "Feature",
        "Care Instructions", "Composition", "Product Width", "Product Length", "Product Height",
        "Title 1", "Title 2", "Title 3", "Title 4", "Description", "Status", "Includes"
    ],
    "products_word_bank": (
        ["category_id", "category_name", "sub_category"] +
        [f"keyword_{i}" for i in range(1, 126)]
    )
}

# -------------------------------------
# Setup SQL connection
def get_sql_connection():
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=mptcecommerce-sql-server.database.windows.net;"
        "Database=mptcecommerce-db;"
        "Uid=mptcadmin;"
        "Pwd=Mptc@2025;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )
    return pyodbc.connect(conn_str)

# -------------------------------------
# Load data from selected table
def load_table_data(table_name):
    conn = get_sql_connection()
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# -------------------------------------
# Convert DataFrame to CSV
def convert_df_to_csv(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()

# -------------------------------------
# Overwrite table with type-safe insertions
def overwrite_table(table_name, df):
    conn = get_sql_connection()
    cursor = conn.cursor()

    # Keep existing records — no deletion
    pass

    expected_columns = template_cols[table_name]
    if list(df.columns) != expected_columns:
        st.error(f"❌ Column mismatch for `{table_name}`.\nExpected: {expected_columns}\nGot: {list(df.columns)}")
        return

    for idx, row in df.iterrows():
        try:
            if table_name == "product_categories":
                cursor.execute("""
                    INSERT INTO product_categories (category_id, category_name, gpt_prompt)
                    VALUES (?, ?, ?)
                """,
                int(row["category_id"]) if pd.notna(row["category_id"]) else None,
                str(row["category_name"]) if pd.notna(row["category_name"]) else None,
                str(row["gpt_prompt"]) if pd.notna(row["gpt_prompt"]) else None)

            elif table_name == "product_listings":
                cursor.execute("""
                    INSERT INTO product_listings (
                        SKU, Name, [Size], Colour, Category, [Finish/ Style], Feature,
                        [Care Instructions], Composition, [Product Width], [Product Length], [Product Height],
                        [Title 1], [Title 2], [Title 3], [Title 4],
                        [Description], Status, Includes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                str(row.get("SKU")) if pd.notna(row.get("SKU")) else None,
                str(row.get("Name")) if pd.notna(row.get("Name")) else None,
                str(row.get("Size")) if pd.notna(row.get("Size")) else None,
                str(row.get("Colour")) if pd.notna(row.get("Colour")) else None,
                str(row.get("Category")) if pd.notna(row.get("Category")) else None,
                str(row.get("Finish/ Style")) if pd.notna(row.get("Finish/ Style")) else None,
                str(row.get("Feature")) if pd.notna(row.get("Feature")) else None,
                str(row.get("Care Instructions")) if pd.notna(row.get("Care Instructions")) else None,
                str(row.get("Composition")) if pd.notna(row.get("Composition")) else None,
                str(row.get("Product Width")) if pd.notna(row.get("Product Width")) else None,
                str(row.get("Product Length")) if pd.notna(row.get("Product Length")) else None,
                str(row.get("Product Height")) if pd.notna(row.get("Product Height")) else None,
                str(row.get("Title 1")) if pd.notna(row.get("Title 1")) else None,
                str(row.get("Title 2")) if pd.notna(row.get("Title 2")) else None,
                str(row.get("Title 3")) if pd.notna(row.get("Title 3")) else None,
                str(row.get("Title 4")) if pd.notna(row.get("Title 4")) else None,
                str(row.get("Description")) if pd.notna(row.get("Description")) else None,
                str(row.get("Status")) if pd.notna(row.get("Status")) else None,
                str(row.get("Includes")) if pd.notna(row.get("Includes")) else None)

            elif table_name == "products_word_bank":
                placeholders = ','.join(['?'] * len(expected_columns))
                sql = f"INSERT INTO products_word_bank ({', '.join(expected_columns)}) VALUES ({placeholders})"
                values = [str(row[col]) if pd.notna(row[col]) else None for col in expected_columns]
                values[0] = int(row["category_id"]) if pd.notna(row["category_id"]) else None  # Ensure int
                cursor.execute(sql, values)

        except Exception as e:
            st.error(f"❌ Failed to insert row {idx + 1}: {row.to_dict()}\n\nError: {e}")
            continue

    conn.commit()
    conn.close()

# -------------------------------------
# Streamlit UI
st.set_page_config(page_title="📂 SQL Database Manager", layout="wide")
st.title("🗃️ Database Access & Management")

col1, col2 = st.columns([1, 7])
with col1:
    st.markdown("<span style='font-size:23px; font-weight:600;'>Select Table:</span>", unsafe_allow_html=True)
with col2:
    table_choice = st.selectbox("", list(template_cols.keys()), label_visibility="collapsed")

st.markdown("<hr style='margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------
# Section 1: Editable Table Viewer
if table_choice:
    df = load_table_data(table_choice)
    st.markdown(f"### 📋 Editable Table: `{table_choice}`")
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    col1, col2 = st.columns(2)
    with col1:
        save_clicked = st.button("💾 Save Changes to SQL", use_container_width=True)
    with col2:
        st.download_button(
            label="📥 Download Table as CSV",
            data=convert_df_to_csv(edited_df),
            file_name=f"{table_choice}_export.csv",
            mime="text/csv",
            use_container_width=True
        )

    if save_clicked:
        try:
            if list(edited_df.columns) != template_cols[table_choice]:
                st.error(f"❌ Edited columns do not match expected format for `{table_choice}`.")
            else:
                overwrite_table(table_choice, edited_df)
                st.success("✅ Changes successfully saved to the database.")
        except Exception as e:
            st.error(f"❌ Failed to save changes:\n{e}")

st.markdown("<hr style='margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------
# Section 2: Upload CSV to Insert
st.markdown("### 📤 Upload CSV to Insert into Database")

up1, up2, up3 = st.columns([7, 1.5, 1.5])

with up1:
    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

with up2:
    st.download_button(
        label="📄 Download Blank Template",
        data=convert_df_to_csv(pd.DataFrame(columns=template_cols[table_choice])),
        file_name=f"{table_choice}_template.csv",
        mime="text/csv",
        use_container_width=True
    )

with up3:
    insert_button_clicked = st.button("📥 Insert Uploaded CSV into Database", use_container_width=True)

# Handle uploaded file
if uploaded_csv:
    try:
        csv_df = pd.read_csv(uploaded_csv)
        st.success("✅ CSV loaded successfully. Preview below:")
        st.markdown("#### 📌 Uploaded CSV Columns")
        st.write(list(csv_df.columns))
        csv_df_display = st.data_editor(csv_df, use_container_width=True, num_rows="dynamic")
    except Exception as e:
        st.error(f"❌ Failed to read CSV:\n{e}")
        csv_df_display = None
else:
    csv_df_display = None

# Insert logic
if insert_button_clicked:
    if csv_df_display is not None:
        expected_columns = template_cols[table_choice]
        if list(csv_df_display.columns) != expected_columns:
            st.error(f"❌ Uploaded CSV columns do not match the expected format for `{table_choice}`.\n\nExpected: {expected_columns}\nGot: {list(csv_df_display.columns)}")
        else:
            if table_choice == "product_categories" and "category_id" in csv_df_display.columns:
                csv_df_display["category_id"] = pd.to_numeric(csv_df_display["category_id"], errors="coerce")
            elif table_choice == "products_word_bank" and "category_id" in csv_df_display.columns:
                csv_df_display["category_id"] = pd.to_numeric(csv_df_display["category_id"], errors="coerce")

            try:
                overwrite_table(table_choice, csv_df_display)
                st.success("✅ Uploaded data inserted into database.")
            except Exception as e:
                st.error(f"❌ Failed to insert CSV data:\n{e}")
    else:
        st.warning("⚠️ Please upload a valid CSV file first.")
