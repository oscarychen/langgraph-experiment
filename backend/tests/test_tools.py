from hr_rag.rag.tools import (
    HR_TOOLS,
    get_benefits_enrollment,
    get_employee_profile,
    get_leave_balance,
    get_payroll_info,
    submit_leave_request,
)

EMP = "EMP001"


def test_hr_tools_registry_contains_all_five():
    assert len(HR_TOOLS) == 5


def test_get_employee_profile_shape():
    result = get_employee_profile.invoke({"employee_id": EMP})
    assert result["employee_id"] == EMP
    assert {"name", "team", "hire_date", "manager"} <= result.keys()


def test_get_leave_balance_shape():
    result = get_leave_balance.invoke({"employee_id": EMP})
    assert result["employee_id"] == EMP
    assert isinstance(result["days_taken"], int)
    assert isinstance(result["days_remaining"], int)
    breakdown = result["type_breakdown"]
    for leave_type in ("vacation", "sick", "personal"):
        assert leave_type in breakdown
        assert {"taken", "remaining"} <= breakdown[leave_type].keys()


def test_get_payroll_info_shape():
    result = get_payroll_info.invoke({"employee_id": EMP})
    assert result["employee_id"] == EMP
    assert {"pay_cycle", "last_pay_date", "deductions"} <= result.keys()
    assert isinstance(result["deductions"], dict)


def test_get_benefits_enrollment_shape():
    result = get_benefits_enrollment.invoke({"employee_id": EMP})
    assert result["employee_id"] == EMP
    assert isinstance(result["enrolled_benefits"], list)
    assert result["enrolled_benefits"]
    assert "coverage_tier" in result


def test_submit_leave_request_success():
    result = submit_leave_request.invoke(
        {
            "employee_id": EMP,
            "leave_type": "vacation",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
        }
    )
    assert "error" not in result
    assert result["status"] == "submitted"
    assert result["confirmation_number"]
    assert result["leave_type"] == "vacation"


def test_submit_leave_request_rejects_invalid_type():
    result = submit_leave_request.invoke(
        {
            "employee_id": EMP,
            "leave_type": "sabbatical",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
        }
    )
    assert "error" in result
