"""HR data tools exposed to the LangGraph agent.

All functions return hardcoded mock data. They will be replaced with real
backing services (HRIS, payroll, benefits) once those integrations exist.
"""

from langchain_core.tools import tool


@tool
def get_employee_profile(employee_id: str) -> dict:
    """Look up basic profile information for an employee.

    Args:
        employee_id: Unique employee identifier (e.g., "EMP001").

    Returns:
        Dict with name, team, hire_date (YYYY-MM-DD), and manager.
    """
    return {
        "employee_id": employee_id,
        "name": "Alex Johnson",
        "team": "Engineering",
        "hire_date": "2022-03-15",
        "manager": "Jamie Smith",
    }


@tool
def get_leave_balance(employee_id: str) -> dict:
    """Look up the employee's current leave balance.

    Returns days taken so far this year, days remaining, and a per-type
    breakdown for vacation, sick, and personal leave.

    Args:
        employee_id: Unique employee identifier.

    Returns:
        Dict with days_taken, days_remaining, and type_breakdown.
    """
    return {
        "employee_id": employee_id,
        "days_taken": 8,
        "days_remaining": 17,
        "type_breakdown": {
            "vacation": {"taken": 5, "remaining": 10, "annual_allotment": 15},
            "sick": {"taken": 2, "remaining": 5, "annual_allotment": 7},
            "personal": {"taken": 1, "remaining": 2, "annual_allotment": 3},
        },
    }


@tool
def get_payroll_info(employee_id: str) -> dict:
    """Look up the employee's most recent payroll information.

    Args:
        employee_id: Unique employee identifier.

    Returns:
        Dict with pay_cycle, last_pay_date, last_pay_amount (gross), and
        deductions broken down by category.
    """
    return {
        "employee_id": employee_id,
        "pay_cycle": "biweekly",
        "last_pay_date": "2026-05-01",
        "last_pay_amount": 4200.00,
        "currency": "USD",
        "deductions": {
            "federal_tax": 630.00,
            "state_tax": 210.00,
            "health_insurance": 180.00,
            "retirement_401k": 252.00,
        },
    }


@tool
def get_benefits_enrollment(employee_id: str) -> dict:
    """Look up the employee's current benefits enrollment.

    Args:
        employee_id: Unique employee identifier.

    Returns:
        Dict with enrolled_benefits (list of plan names) and coverage_tier.
    """
    return {
        "employee_id": employee_id,
        "enrolled_benefits": [
            "Medical PPO",
            "Dental Standard",
            "Vision Basic",
            "401(k) Plan",
            "Life Insurance (1x salary)",
        ],
        "coverage_tier": "employee + spouse",
    }


@tool
def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Submit a new leave request on behalf of the employee.

    Args:
        employee_id: Unique employee identifier.
        leave_type: One of "vacation", "sick", or "personal".
        start_date: First day of leave, ISO format (YYYY-MM-DD).
        end_date: Last day of leave, ISO format (YYYY-MM-DD).

    Returns:
        Dict with confirmation_number and status on success, or an
        error field if leave_type is invalid.
    """
    valid_types = {"vacation", "sick", "personal"}
    if leave_type not in valid_types:
        return {
            "error": f"Invalid leave_type '{leave_type}'. "
            f"Must be one of: {sorted(valid_types)}.",
        }
    return {
        "confirmation_number": "LR-2026-00042",
        "status": "submitted",
        "employee_id": employee_id,
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
    }


@tool
def search_hr_documents(query: str) -> str:
    """Search HR policy documents for additional context.

    Call this when the retrieved excerpts already in the conversation don't
    cover the user's question. The graph router intercepts this call and
    runs the retrieval pipeline; the function body is never executed.

    Args:
        query: A focused, standalone search query (not a question to the user).
    """
    # Intercepted by route_after_agent in rag/nodes.py — never invoked.
    raise NotImplementedError("search_hr_documents is a signaling tool")


HR_TOOLS = [
    get_employee_profile,
    get_leave_balance,
    get_payroll_info,
    get_benefits_enrollment,
    submit_leave_request,
]

SEARCH_TOOL_NAME = "search_hr_documents"
