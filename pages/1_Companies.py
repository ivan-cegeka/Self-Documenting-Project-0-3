import streamlit as st
from src.db import get_engine, get_session_factory
from src import services, repository

st.title("Companies")

engine = get_engine()
Session = get_session_factory(engine)

with st.form("add_company"):
    name = st.text_input("Name")
    industry = st.text_input("Industry")
    submitted = st.form_submit_button("Add Company")
    if submitted:
        with Session() as session:
            try:
                services.add_company(session, name=name, industry=industry or None)
                st.success(f"Added {name}")

            except ValueError as e:
                st.error(str(e))

with Session() as session:
    companies = repository.list_companies(session)

st.dataframe(
    [{"id": c.id, "name": c.name, "industry": c.industry} for c in companies],
    use_container_width=True,
)

if companies:
    st.subheader("Edit or delete a company")
    options = {f"{c.name} (#{c.id})": c.id for c in companies}
    selected_label = st.selectbox("Select company", list(options.keys()))
    selected_id = options[selected_label]
    with Session() as session:
        company = repository.get_company(session, selected_id)
    new_name = st.text_input("New name", value=company.name, key="edit_company_name")
    new_industry = st.text_input("New industry", value=company.industry or "", key="edit_company_industry")

    col1, col2 = st.columns(2)
    if col1.button("Save changes"):
        with Session() as session:
            repository.update_company(session, selected_id, name=new_name, industry=new_industry or None)
        st.rerun()
    if col2.button("Delete company"):
        with Session() as session:
            repository.delete_company(session, selected_id)
        st.rerun()
