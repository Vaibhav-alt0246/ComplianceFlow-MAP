import streamlit as st

st.set_page_config(page_title="SuRaksha AI: Agentic Compliance Orchestrator", layout="wide")

# Initialize session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "maps_data" not in st.session_state:
    st.session_state.maps_data = None
if "execution_complete" not in st.session_state:
    st.session_state.execution_complete = False

st.title("SuRaksha AI: Agentic Compliance Orchestrator")

# ------------------------------------------------------------------
# Left Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.header("Upload RBI Circular")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.success(f"Uploaded: {uploaded_file.name}")

    st.write("")
    st.write("")

    if st.button("Run Agentic Swarm", type="primary", use_container_width=True):
        if not st.session_state.uploaded_file:
            st.error("Please upload a PDF first.")
        else:
            # Mock crew execution - returns sample MAP data
            st.session_state.maps_data = [
                {
                    "map_id": "MAP-001",
                    "action_title": "Implement 14-character password policy",
                    "target_department": "IT_SECURITY",
                    "explainability_trigger": "Policy requires minimum 14 characters",
                    "confidence_score": 0.95
                },
                {
                    "map_id": "MAP-002",
                    "action_title": "Deploy MFA for all database access",
                    "target_department": "IT_SECURITY",
                    "explainability_trigger": "MFA mandatory for internal database access",
                    "confidence_score": 0.88
                },
                {
                    "map_id": "MAP-003",
                    "action_title": "Configure 15-minute session timeout",
                    "target_department": "OPERATIONS",
                    "explainability_trigger": "Sessions must terminate after 15 minutes inactivity",
                    "confidence_score": 0.65
                }
            ]
            st.rerun()

# ------------------------------------------------------------------
# Main Panel (Top): Loading Spinner Placeholder
# ------------------------------------------------------------------
if st.session_state.uploaded_file and not st.session_state.maps_data:
    st.subheader("Processing")
    st.info("Upload a PDF and click 'Run Agentic Swarm' to begin analysis.")

# ------------------------------------------------------------------
# Main Panel (Middle - HITL): Pending Human Approval
# ------------------------------------------------------------------
if st.session_state.maps_data and not st.session_state.execution_complete:
    st.header("Pending Human Approval")

    for map_item in st.session_state.maps_data:
        task = map_item.get("action_title", "N/A")
        dept = map_item.get("target_department", "N/A")
        trigger = map_item.get("explainability_trigger", "N/A")
        confidence = map_item.get("confidence_score", 0.0)

        # Color-code confidence score
        if confidence > 0.90:
            confidence_color = "🟢"
        elif confidence > 0.70:
            confidence_color = "🟡"
        else:
            confidence_color = "🔴"

        with st.expander(f"{confidence_color} {task}"):
            st.markdown(f"**Task**: {task}")
            st.markdown(f"**Assigned Department**: {dept}")
            st.markdown(f"**Explainability Trigger**: {trigger}")
            st.markdown(f"**Confidence Score**: {confidence:.0%}")

# ------------------------------------------------------------------
# Main Panel (Bottom): Approve Button
# ------------------------------------------------------------------
if st.session_state.maps_data and not st.session_state.execution_complete:
    st.write("")
    if st.button("Approve All & Dispatch to DB", type="primary", use_container_width=True):
        st.session_state.execution_complete = True
        st.success("Audit Trail Generated and Tickets Dispatched")
        st.rerun()

# ------------------------------------------------------------------
# Execution Complete State
# ------------------------------------------------------------------
if st.session_state.execution_complete:
    st.success("Audit Trail Generated and Tickets Dispatched")
    st.write("All approved MAPs have been written to the database.")
