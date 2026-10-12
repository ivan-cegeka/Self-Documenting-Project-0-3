import streamlit as st
from src.db import get_engine, get_session_factory
from src import services, repository

st.title("Contacts")

engine = get_engine()
Session = get_session_factory(engine)

with Session() as session:
    companies = repository.list_companies(session)
company_options = {"(none)": None} | {c.name: c.id for c in companies}

with st.form("add_contact"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    company_label = st.selectbox("Company", list(company_options.keys()))
    submitted = st.form_submit_button("Add Contact")
    if submitted:
        with Session() as session:
            try:
                services.add_contact(
                    session,
                    name=name,
                    email=email or None,
                    phone=phone or None,
                    company_id=company_options[company_label],
                )
                st.success(f"Added {name}")
            except ValueError as e:
                st.error(str(e))

with Session() as session:
    contacts = repository.list_contacts(session)

st.dataframe(
    [
        {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone, "company_id": c.company_id}
        for c in contacts
    ],
    use_container_width=True,
)

if contacts:
    st.subheader("Edit or delete a contact")
    options = {f"{c.name} (#{c.id})": c.id for c in contacts}
    selected_label = st.selectbox("Select contact", list(options.keys()))
    selected_id = options[selected_label]
    with Session() as session:
        contact = repository.get_contact(session, selected_id)
    new_name = st.text_input("New name", value=contact.name, key="edit_contact_name")
    new_email = st.text_input("New email", value=contact.email or "", key="edit_contact_email")
    new_phone = st.text_input("New phone", value=contact.phone or "", key="edit_contact_phone")
    col1, col2 = st.columns(2)
    if col1.button("Save changes", key="save_contact"):
        with Session() as session:
            repository.update_contact(session, selected_id, name=new_name, email=new_email or None, phone=new_phone or None)
        st.rerun()
    if col2.button("Delete contact", key="delete_contact"):
        with Session() as session:
            repository.delete_contact(session, selected_id)
        st.rerun()
