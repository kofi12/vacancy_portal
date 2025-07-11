# TODO: Add Organization Entity to Backend

## 1. Create Organization Model

- [ x] Define `Organization` model in `models/models.py` with fields:
  - `id: int` (primary key)
  - `name: str`
  - `address: str`
  - `number_of_beds: int`
  - `operator_name: str`
  - `role: UserRole` (enum)

## 2. Create Database Migration

- [x ] Generate Alembic migration to create the `organizations` table.
- [ x] Apply the migration to your database.

## 3. Add CRUD Endpoints

- [ x] Create a new router/controller (e.g., `controller/organization_controller.py`).
- [x ] Implement endpoints:
  - [x ] Create organization
  - [x ] Get organization by ID
  - [ x] Update organization
  - [ x] Delete organization
  - [ x] List all organizations

## 4. Update Schemas

- [ x] Add Pydantic schemas for Organization (e.g., `OrganizationBase`, `OrganizationCreate`, `OrganizationRead`, `OrganizationUpdate`) in `models/schemas.py`.

## 5. Add DAO Functions

- [ x] Implement DAO functions for organization CRUD in `database/organization_dao.py`.

## 6. (Optional) Set Up Associations

- [x ] Link users or tenants to organizations via a foreign key if needed.
- [x] Update models and migrations accordingly.

## 7. Permissions & Access Control

- [ ] Ensure only users with the correct role (e.g., OWNER) can create or manage organizations.

## 8. Testing

- [ ] Write tests for organization endpoints and logic.

## 9. Documentation

- [ ] Document the new endpoints in your API docs and README.
