import re
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from src import repository

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_INTERACTION_TYPES = {"call", "email", "meeting", "note"}


def add_company(session: Session, name: str, industry: str | None = None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Company name is required")
    duplicate = any(c.name.lower() == name.lower() for c in repository.list_companies(session))
    if duplicate:
        raise ValueError(f"A company named '{name}' already exists")
    st.toast(f"Company '{name}' created")
    return repository.create_company(session, name=name, industry=industry)


def add_contact(
    session: Session,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    company_id: int | None = None,
):
    name = (name or "").strip()
    if not name:
        raise ValueError("Contact name is required")
    if email and EMAIL_RE.match(email):
        raise ValueError(f"'{email}' is not a valid email address")
    if company_id is not None and repository.get_company(session, company_id) is None:
        raise ValueError(f"No company with id {company_id}")
    return repository.create_contact(session, name=name, email=email, phone=phone, company_id=company_id)


def log_interaction(
    session: Session,
    contact_id: int,
    type: str,
    occurred_at: datetime,
    note: str | None = None,
):
    if repository.get_contact(session, contact_id) is None:
        raise ValueError(f"No contact with id {contact_id}")
    if type not in ALLOWED_INTERACTION_TYPES:
        raise ValueError(
            f"'{type}' is not a valid interaction type; expected one of {sorted(ALLOWED_INTERACTION_TYPES)}"
        )
    return repository.create_interaction(session, contact_id=contact_id, type=type, occurred_at=occurred_at, note=note)
