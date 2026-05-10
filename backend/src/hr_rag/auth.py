"""Authentication dependencies for protected endpoints.

In production, `get_current_employee_id` will inspect the Authorization
header (Bearer JWT, session cookie, etc.), verify the token, and resolve
the authenticated principal to an employee_id. For now it returns a
hardcoded id so endpoints have a stable subject during local development.
"""

_MOCK_EMPLOYEE_ID = "EMP001"


async def get_current_employee_id() -> str:
    return _MOCK_EMPLOYEE_ID
