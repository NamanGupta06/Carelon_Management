import streamlit as st
import pandas as pd
import time


# Restrict direct access
if not st.session_state.get("logged_in"):
    st.warning("⚠️ You must log in first.")
    st.stop()

admin_domain_id = st.session_state.get("domain_id")
locked_manager_id = st.session_state.get("mail_id")

st.title("📁 Resource Manager")
st.write(f"Welcome, **{st.session_state.get('admin_name', 'Admin')}** 👋")

EXCEL_PATH = 'C:/Users/deves/Carelon_Management/Resources.xlsx'

@st.cache_data(ttl=1)
def load_resource_data(path):
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip().str.lower()
    if 'locked_manager_mailid' not in df.columns:
        df["locked_manager_mailid"] = ""
    if 'locked_manager_domainid' not in df.columns:
        df["locked_manager_domainid"] = ""
    return df

# Select inputs
band_options = ["I07", "I08", "I09", "I10", "I11", "I12"]
band_selected = st.selectbox("Choose the band: ", band_options)
skill_input = st.text_input("Enter Primary Skill Set", placeholder="e.g. Python, SQL, Java")

# Manual refresh
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Always load latest data
try:
    df_resource = load_resource_data(EXCEL_PATH)
except Exception as e:
    st.error(f"Error loading Resource.xlsx: {e}")
    st.stop()

# Filter data
filtered_df = df_resource[
    (df_resource["band_level"] == band_selected) &
    (df_resource["skill"].str.lower().str.contains(skill_input.lower().strip()))
].copy()

st.subheader("🔧 Update Assignment Availability")
if not filtered_df.empty:
    st.caption("🔒 Only the available_next_assignment column is editable if you are the locker or the status is Open.")

    # Add edit hint column
    def lock_note(row):
        if str(row["available_next_assignment"]).lower() == "locked" and \
           str(row.get("locked_manager_mailid", "")).lower() != str(locked_manager_id).lower():
            return "🔒 Locked by another admin"
        return "✅ Editable"

    filtered_df["edit_status"] = filtered_df.apply(lock_note, axis=1)

    # Define which rows are editable
    def is_editable(row):
        if str(row["available_next_assignment"]).lower() == "open":
            return True
        return str(row.get("locked_manager_mailid", "")).lower() == str(locked_manager_id).lower()

    row_edit_disabled = ~filtered_df.apply(is_editable, axis=1)

    # Define editor column config
    column_config = {
        "available_next_assignment": st.column_config.SelectboxColumn(
            "available_next_assignment",
            help="Change status to Open or Locked",
            options=["Open", "Locked"]
        ),
        "edit_status": st.column_config.TextColumn(
            "Status",
            help="Indicates if you're allowed to edit this row.",
            disabled=True
        )
    }

    # Show the editor
    edited_df = st.data_editor(
        filtered_df,
        column_config=column_config,
        disabled=row_edit_disabled.tolist(),
        use_container_width=True,
        key="editable_assignment"
    )

    # Save logic with strict validation
    if st.button("💾 Save Changes"):
        try:
            df_resource = load_resource_data(EXCEL_PATH)
            update_count = 0

            for idx in edited_df.index:
                new_status = edited_df.loc[idx, "available_next_assignment"]

                global_idx = df_resource[
                    (df_resource["band_level"] == band_selected) &
                    (df_resource["skill"].str.lower().str.contains(skill_input.lower().strip()))
                ].index[edited_df.index.get_loc(idx)]

                original_row = df_resource.loc[global_idx]
                old_status = original_row["available_next_assignment"]
                locked_by_me = str(original_row.get("locked_manager_mailid", "")).lower() == str(locked_manager_id).lower()

                # Enforce permission on backend
                if old_status.lower() == "locked" and not locked_by_me:
                    continue  # not allowed
                if old_status.lower() == "open" or locked_by_me:
                    if new_status != old_status:
                        df_resource.at[global_idx, "available_next_assignment"] = new_status
                        if new_status.lower() == "locked":
                            df_resource.at[global_idx, "locked_manager_domainid"] = admin_domain_id
                            df_resource.at[global_idx, "locked_manager_mailid"] = locked_manager_id
                        elif new_status.lower() == "open":
                            df_resource.at[global_idx, "locked_manager_domainid"] = ""
                            df_resource.at[global_idx, "locked_manager_mailid"] = ""
                        update_count += 1

            df_resource.to_excel(EXCEL_PATH, index=False)

            if update_count > 0:
                st.success(f"✅ {update_count} changes saved successfully.")
                st.cache_data.clear()
                time.sleep(3)  # Give user time to read
                st.rerun()
            else:
                st.info("ℹ️ No permitted changes to save.")
                time.sleep(5)
        except Exception as e:
            st.error(f"❌ Failed to save changes: {e}")
else:
    st.info("No matching resources found.")
