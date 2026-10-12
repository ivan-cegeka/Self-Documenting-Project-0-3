# Use Cases

### UC-1: Add a Company

- **Actor:** User
- **Goal:** Record a new company in the CRM.
- **Preconditions:** None.
- **Steps:**
  1. User opens the Companies page.
  2. User enters a name and optional industry, and submits.
  3. System validates the name is non-empty and not a duplicate.
  4. System creates the Company and shows it in the table.
- **Outcome:** A new Company row exists.

### UC-2: Add a Contact

- **Actor:** User
- **Goal:** Record a new contact, optionally linked to a Company.
- **Preconditions:** If linking to a Company, that Company must already exist.
- **Steps:**
  1. User opens the Contacts page.
  2. User enters a name, optional email/phone, and optionally selects a Company.
  3. System validates the name is non-empty, the email (if given) is well-formed, and the Company (if given) exists.
  4. System creates the Contact and shows it in the table.
- **Outcome:** A new Contact row exists, linked to its Company if one was chosen.

### UC-3: Log an Interaction

- **Actor:** User
- **Goal:** Record a call, email, meeting, note, or SMS message against a Contact.
- **Preconditions:** At least one Contact exists.
- **Steps:**
  1. User opens the Interactions page.
  2. User selects a Contact, an interaction type, a date, and an optional note.
  3. System validates the Contact exists and the type is one of the allowed types.
  4. System creates the Interaction and shows it in the contact's interaction list.
- **Outcome:** A new Interaction row exists, linked to its Contact.

### UC-4: Edit or Delete a Company/Contact

- **Actor:** User
- **Goal:** Correct or remove an existing Company or Contact.
- **Preconditions:** The record exists.
- **Steps:**
  1. User selects the record from a dropdown on its page.
  2. User edits the fields and clicks "Save changes", or clicks "Delete".
  3. System applies the update, or deletes the record (and, for Contacts, cascades to delete its Interactions).
- **Outcome:** The record is updated or removed.