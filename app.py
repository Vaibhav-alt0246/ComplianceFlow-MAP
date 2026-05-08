import streamlit as st
import json
import os
from agents.crew_logic import ComplianceCrew
from tools.db_manager import create_compliance_ticket

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
            # Save uploaded file to disk
            pdf_path = f"data_assets/{st.session_state.uploaded_file.name}"
            with open(pdf_path, "wb") as f:
                f.write(st.session_state.uploaded_file.getbuffer())

            with st.spinner("Agents are analyzing the circular and auditing existing policies..."):
                try:
                    # Trigger the crew
                    crew_instance = ComplianceCrew()
                    result = crew_instance.run_extraction_and_audit(document_path=pdf_path)

                    # Parse the audit output JSON
                    audit_output = result.get("audit_output", "")
                    if audit_output:
                        try:
                            audit_json = json.loads(audit_output)
                            st.session_state.maps_data = audit_json.get("audit_results", [])
                        except json.JSONDecodeError:
                            st.error("Failed to parse audit results. Raw output:")
                            st.text(audit_output)
                            st.session_state.maps_data = []
                    else:
                        st.error("No audit output received from crew.")
                        st.session_state.maps_data = []

                    st.rerun()
                except Exception as e:
                    st.error(f"Crew execution failed: {e}")
                    import traceback
                    st.text(traceback.format_exc())

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

    approved_count = 0
    revision_count = 0

    for map_item in st.session_state.maps_data:
        map_id = map_item.get("map_id", "N/A")
        verdict = map_item.get("verdict", "UNKNOWN")
        confidence = map_item.get("confidence_score", 0.0)
        issues = map_item.get("issues", [])

        # Count verdicts
        if verdict == "APPROVE":
            approved_count += 1
        elif verdict == "REVISE":
            revision_count += 1

        # Color-code verdict
        if verdict == "APPROVE":
            verdict_color = "🟢"
        elif verdict == "REVISE":
            verdict_color = "🟡"
        else:
            verdict_color = "⚪"

        # Color-code confidence score
        if confidence > 0.90:
            confidence_color = "🟢"
        elif confidence > 0.70:
            confidence_color = "🟡"
        else:
            confidence_color = "🔴"

        with st.expander(f"{verdict_color} {map_id} - {verdict} (Confidence: {confidence:.0%})"):
            st.markdown(f"**MAP ID**: {map_id}")
            st.markdown(f"**Verdict**: {verdict}")
            st.markdown(f"**Confidence Score**: {confidence:.0%}")

            if issues:
                st.markdown("**Issues Found:**")
                for issue in issues:
                    issue_type = issue.get("issue_type", "N/A")
                    description = issue.get("description", "N/A")
                    policy_ref = issue.get("policy_reference", "N/A")
                    required_change = issue.get("required_change", "N/A")

                    st.markdown(f"- **{issue_type}**: {description}")
                    if policy_ref != "N/A":
                        st.markdown(f"  *Policy Reference*: {policy_ref}")
                    if required_change != "N/A":
                        st.markdown(f"  *Required Change*: {required_change}")
            else:
                st.markdown("✅ No issues found - MAP is ready for execution")

    st.markdown("---")
    st.markdown(f"**Summary**: {approved_count} Approved | {revision_count} Require Revision")

# ------------------------------------------------------------------
# Main Panel (Bottom): Approve Button
# ------------------------------------------------------------------
if st.session_state.maps_data and not st.session_state.execution_complete:
    st.write("")
    if st.button("Approve All & Dispatch to DB", type="primary", use_container_width=True):
        with st.spinner("Dispatching approved MAPs to database..."):
            tickets_created = 0
            errors = []

            for map_item in st.session_state.maps_data:
                verdict = map_item.get("verdict", "APPROVE")  # Default to APPROVE for human-approved MAPs
                map_id = map_item.get("map_id", f"MAP-{tickets_created + 1}")
                task_desc = map_item.get("action_title", f"Execute MAP {map_id}")
                dept = map_item.get("target_department", "IT_SECURITY")
                trigger = map_item.get("explainability_trigger", "Human-approved MAP")
                confidence = str(map_item.get("confidence_score", 0.95))

                try:
                    # Call the database tool (access underlying function via .func)
                    result = create_compliance_ticket.func(
                        task=task_desc,
                        department=dept,
                        explainability_trigger=trigger,
                        confidence_score=confidence
                    )
                    tickets_created += 1
                except Exception as e:
                    errors.append(f"Failed to create ticket for {map_id}: {e}")

            if errors:
                st.warning(f"Created {tickets_created} tickets with {len(errors)} errors:")
                for error in errors:
                    st.text(error)
            else:
                st.success(f"✅ Successfully created {tickets_created} tickets in database")

            # Clear session state
            st.session_state.execution_complete = True
            st.session_state.maps_data = None
            st.session_state.uploaded_file = None
            st.rerun()

# ------------------------------------------------------------------
# Execution Complete State
# ------------------------------------------------------------------
if st.session_state.execution_complete:
    st.success("Audit Trail Generated and Tickets Dispatched")
    st.write("All approved MAPs have been written to the database.")
