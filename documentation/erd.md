```mermaid
erDiagram
    COMPANY ||--o{ CONTACT : employs
    CONTACT ||--o{ INTERACTION : has

    COMPANY {
        int id PK
        string name
        string industry
    }
    CONTACT {
        int id PK
        string name
        string email
        string phone
        int company_id FK
    }
    INTERACTION {
        int id PK
        int contact_id FK
        string type
        string note
        datetime occurred_at
    }
```

A Company has zero or more Contacts; a Contact optionally belongs to one
Company. A Contact has zero or more Interactions; deleting a Contact
cascades to delete its Interactions (see `src/models.py`).