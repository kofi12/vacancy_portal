# Backend Change Request Template

## 1. **Summary of Change**

- Briefly describe the change you want to make.
  - Need to implement role-based endpoint protection
  - Roles: admin, scworker, owner

## 3. **Detailed Description**

- Provide a detailed description of the change, including:
  - Upon signup a role should be given based on the type of User
    - User can either be an owner(business owner) or scworker (social worker or nurse), admin will belong to me only
  - use JWTs to encode user informaton, pass around token in the Authorization: Bearer token header

## 4. **Endpoints Affected or Needed**

- List any new or modified API endpoints, including:
  - in tenant_controller.py
    - admin can access all endpoints
    - owner can't access create-waitlist-tenant and upload-pdf
    - scworker can't access create-tenant get(/tenant/*) put delete /all-tenants and download-pdf

## 5. **Database/Model Changes**

- Describe any changes to models or database schema.
  - In the User table, the role can be an Enum with these values (admin, scworker, owner)

## 6. **Authentication & Authorization**

- Describe any changes to auth logic, roles, or permissions.
  - Make the necessary changes to ensure proper authentication and authorization using JWTs

## 7. **Acceptance Criteria**

- List the conditions that must be met for this change to be considered complete.
  - Create the appropriate tests

## 8. **Other Notes or Requirements**

**Instructions:**  
Fill out each section as completely as possible. You can remove any sections that don't apply or add new ones as needed.  
Once you provide this file, I'll use it to guide the backend changes you want implemented!
