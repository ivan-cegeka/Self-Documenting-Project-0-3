from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models import Company, Contact, Interaction


# --- Company ---

def create_company(session: Session, name: str, industry: str | None = None) -> Company:
    company = Company(name=name, industry=industry)
    session.add(company)
    session.commit()
    return company


def get_company(session: Session, company_id: int) -> Company | None:
    return session.get(Company, company_id)


def list_companies(session: Session) -> list[Company]:
    return list(session.scalars(select(Company).order_by(Company.name)))


def update_company(
    session: Session, company_id: int, name: str | None = None, industry: str | None = None
) -> Company:
    company = session.get(Company, company_id)
    if company is None:
        raise ValueError(f"No company with id {company_id}")
    if name is not None:
        company.name = name
    if industry is not None:
        company.industry = industry
    session.commit()
    return company


def delete_company(session: Session, company_id: int) -> None:
    company = session.get(Company, company_id)
    if company is not None:
        session.delete(company)
        session.commit()


# --- Contact ---

def create_contact(
    session: Session,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    company_id: int | None = None,
) -> Contact:
    contact = Contact(name=name, email=email, phone=phone, company_id=company_id)
    session.add(contact)
    session.commit()
    return contact


def get_contact(session: Session, contact_id: int) -> Contact | None:
    return session.get(Contact, contact_id)


def list_contacts(session: Session, company_id: int | None = None) -> list[Contact]:
    stmt = select(Contact).order_by(Contact.name)
    if company_id is not None:
        stmt = stmt.where(Contact.company_id == company_id)
    return list(session.scalars(stmt))


def update_contact(
    session: Session,
    contact_id: int,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company_id: int | None = None,
) -> Contact:
    contact = session.get(Contact, contact_id)
    if contact is None:
        raise ValueError(f"No contact with id {contact_id}")
    if name is not None:
        contact.name = name
    if email is not None:
        contact.email = email
    if phone is not None:
        contact.phone = phone
    if company_id is not None:
        contact.company_id = company_id
    session.commit()
    return contact


def delete_contact(session: Session, contact_id: int) -> None:
    contact = session.get(Contact, contact_id)
    if contact is not None:
        session.delete(contact)  # cascades to delete this contact's interactions
        session.commit()


# --- Interaction ---

def create_interaction(
    session: Session,
    contact_id: int,
    type: str,
    occurred_at: datetime,
    note: str | None = None,
) -> Interaction:
    interaction = Interaction(contact_id=contact_id, type=type, occurred_at=occurred_at, note=note)
    session.add(interaction)
    session.commit()
    return interaction


def list_interactions(session: Session, contact_id: int) -> list[Interaction]:
    stmt = (
        select(Interaction)
        .where(Interaction.contact_id == contact_id)
        .order_by(Interaction.occurred_at.desc())
    )
    return list(session.scalars(stmt))


def delete_interaction(session: Session, interaction_id: int) -> None:
    interaction = session.get(Interaction, interaction_id)
    if interaction is not None:
        session.delete(interaction)
        session.commit()
