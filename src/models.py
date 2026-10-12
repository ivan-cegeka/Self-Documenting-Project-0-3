from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)

    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="contacts")
    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    contact: Mapped["Contact"] = relationship(back_populates="interactions")
