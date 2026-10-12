from datetime import datetime
import streamlit as st
from src.db import get_engine, get_session_factory
from src import services, repository

st.title("Interactions")

engine = get_engine()
Session = get_session_factory(engine)

with Session() as session:
    contacts = repository.list_contacts(session)

if not contacts:
    st.info("Add a contact first before logging interactions.")
    st.stop()

contact_options = {f"{c.name} (#{c.id})": c.id for c in contacts}

with st.form("log_interaction"):
    contact_label = st.selectbox("Contact", list(contact_options.keys()))
    interaction_type = st.selectbox("Type", sorted(services.ALLOWED_INTERACTION_TYPES))
    occurred_date = st.date_input("Date")
    note = st.text_area("Note")
    submitted = st.form_submit_button("Log Interaction")
    if submitted:
        with Session() as session:
            try:
                services.log_interaction(
                    session,
                    contact_id=contact_options[contact_label],
                    type=interaction_type,
                    occurred_at=datetime.combine(occurred_date, datetime.min.time()),
                    note=note or None,
                )
                st.success("Logged")
            except ValueError as e:
                st.error(str(e))

selected_contact_id = contact_options[st.selectbox("View interactions for", list(contact_options.keys()), key="view_contact")]
with Session() as session:
    interactions = repository.list_interactions(session, selected_contact_id)

st.dataframe(
    [{"id": i.id, "type": i.type, "occurred_at": i.occurred_at, "note": i.note} for i in interactions],
    use_container_width=True,
)

if interactions:
    options = {f"{i.type} on {i.occurred_at} (#{i.id})": i.id for i in interactions}
    selected_label = st.selectbox("Select interaction to delete", list(options.keys()))
    if st.button("Delete interaction"):
        with Session() as session:
            repository.delete_interaction(session, options[selected_label])
        st.rerun()
