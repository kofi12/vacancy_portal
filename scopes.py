AVAILABLE_SCOPES = {
    "view:dashboard": "Permission to view the dashboard",
    "view:waitlist": "Permission to view the waitlist",
    "write:waitlist": "Permission to modify the waitlist",
    "view:tenants": "Permission to view tenant information",
    "write:tenants": "Permission to modify tenant information",
    "view:profile": "Permission to view user profiles",
    "write:profile": "Permission to modify user profiles",
    "view:organization": "Permission to view organization details",
    "write:organization": "Permission to modify organization details",
    "view:documents": "Permission to view tenant documents",
    "write:documents": "Permission to upload and modify tenant documents",
    "view:users": "Permission to view user information",
    "write:users": "Permission to modify user information"

}

ROLE_SCOPES = {
    "admin": list(AVAILABLE_SCOPES.keys()),

    "scworker": ["view:dashboard", "write:waitlist", "view:profile",
                 "write:profile", "view:organization", "view:documents", "write:documents", "view:users", "write:users"],

    "owner": ["view:dashboard", "view:waitlist","write:waitlist", "view:profile", "write:profile",
              "view:organization", "write:organization", "view:documents", "view:users", "write:users"],

    "pending": ["write:tenants"],
}

