# Project Requirements & Instructions

## 1. **Entities & Roles**

- **List all entities (e.g., User, Organization, Admin, etc.) and their relationships.**
  - User: belongs t
  - Organization: has many Users

## 2. **Roles & Permissions**

- **List each role and what actions/endpoints/resources they can access.**
  - Example:
    - Admin: Can manage users, view all data, access admin endpoints
    - Member: Can view own data, submit forms
    - Worker: Can view assigned tasks

## 3. **Authentication & Authorization**

- **Describe your desired login flow and token handling.**
  - Example:
    - Use Google SSO for login
    - Issue JWT access token with role and org info
    - Store token in HttpOnly cookie or Authorization header

## 4. **API Endpoints**

- **List key endpoints and which roles can access them.**
  - Example:
    - `/api/admin/users` — Admin only
    - `/api/profile` — All authenticated users

## 5. **Frontend Requirements**

- **Describe the platforms and frameworks you want to use.**
  - Example:
    - Web: Next.js
    - Mobile: Expo/React Native
- **List key pages/screens and features.**
  - Example:
    - Login page, Dashboard, Profile, Admin panel

## 6. **Design**

- **Attach or link to your design files (Figma, images, etc.), or describe the look and feel you want.**
  - Example:
    - Figma link: [your-link-here]
    - Color scheme: Blue/white, modern, clean

## 7. **Other Requirements**

- **Anything else I should know?**
  - Example:
    - Multi-language support
    - Accessibility requirements
    - Offline support for mobile

---

**Instructions:**  
Fill out each section as completely as possible. You can remove any sections that don't apply or add new ones as needed.  
Once you provide this file, I'll use it as the blueprint for your backend and frontend implementation!
