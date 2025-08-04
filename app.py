import streamlit as st
import pandas as pd

#Loading the excel
def load_admin_credentials(path):
    df = pd.read_excel('C:/Users/deves/Carelon_Management/Admin_credentials.xlsx')
    df.columns = df.columns.str.lower().str.strip()  # Normalize column names
    return df

EXCEL_PATH = "C:/Users/deves/Carelon_Management/Admin_credentials.xlsx"
try:
    admin_df = load_admin_credentials(EXCEL_PATH)
except Exception as e:
    st.error(f"Error loading Excel: {e}")
    st.stop()

#Setting the page configuration
st.set_page_config(page_title="Admin Login", layout = "centered")

st.title("🔐 Admin Login")

#Creating the form for admin
with st.form("login form"):
    domain_id = st.text_input("Enter Domain Id", placeholder = "AL8####")
    name = st.text_input("Enter your name", placeholder = "Naman Gupta")
    mail_id = st.text_input("Enter your mail id", placeholder = "Naman@carelon.com")
    submitted = st.form_submit_button("Login")

# --- Validation Logic ---
if submitted:
    matched = admin_df[
        (admin_df["domain_id"].str.lower() == domain_id.lower()) &
        (admin_df["name"].str.lower() == name.lower()) &
        (admin_df["mail_id"].str.lower() == mail_id.lower())
    ]
    
    if not matched.empty:
        st.session_state["domain_id"] = domain_id
        st.session_state["mail_id"] = mail_id
        st.success(f"✅ Logged in Successful, Redirecting you to Resource Manager")
        st.session_state["logged_in"] = True
        st.session_state["admin_name"] = name
        st.switch_page("pages/resource_manager.py")
        st.stop()
    else:
        st.error("❌ Invalid Domain ID or Name.")