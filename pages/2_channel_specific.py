import streamlit as st
import pandas as pd
import pyodbc
import time
import csv
from io import BytesIO
from utils.gpt_utils import generate_output_for_group

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
st.set_page_config(page_title="Channel-wise Title & Description Generator", layout="wide")
st.title("Channel Specific Product Listing")

