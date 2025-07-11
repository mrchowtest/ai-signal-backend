import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Signal History", layout="wide")

conn = sqlite3.connect("signals.db")
df = pd.read_sql("SELECT * FROM signals ORDER BY timestamp DESC", conn)
conn.close()

st.title("📊 Signal History Dashboard")
st.dataframe(df, use_container_width=True)
