# ADR-003: Google Drive Readonly Scope

**Context:** Agent requested full `drive` scope to create folders. User prefers minimal permissions.

**Decision:** Keep `drive.readonly` + `spreadsheets` scopes only. Manual folder creation by user.

**Rationale:**
- Principle of least privilege.
- Folder structure is static; agent only reads portfolio data.

**Consequences:**
- Agent cannot create Drive folders or files.
- User manages Drive structure manually.
