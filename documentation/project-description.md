# CRM Lite — Project Description

CRM Lite is a small Streamlit application for tracking companies, the
contacts who work at them, and the interactions a user has with those
contacts (calls, emails, meetings, notes, and SMS messages). It gives a single user a
lightweight way to keep track of who they know, which company each
person belongs to, and the history of calls, emails, meetings, notes, and SMS messages
exchanged with each contact.

## Ubiquitous Language

- **Company** — an organization a Contact may belong to. A Company has a
  name (unique) and an optional industry.
- **Contact** — a person tracked in the CRM. A Contact has a name and
  optional email/phone, and optionally belongs to one Company.
- **Interaction** — a logged touchpoint with a Contact: a call, email,
  meeting, note, or SMS message, with a timestamp and optional free-text note.