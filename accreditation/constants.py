from decimal import Decimal


CYCLE_STATUSES = [
    ("draft", "Draft"),
    ("active", "Active"),
    ("submission_open", "Submission Open"),
    ("internal_review", "Internal Review"),
    ("correction_required", "Correction Required"),
    ("ready_for_visit", "Ready for Visit"),
    ("external_visit_completed", "External Visit Completed"),
    ("final_report_approved", "Final Report Approved"),
    ("closed", "Closed"),
]

VALUE_TYPES = [
    ("numeric", "Numeric"),
    ("text", "Text"),
    ("date", "Date"),
    ("boolean", "Boolean"),
    ("percentage", "Percentage"),
    ("score", "Score"),
]

VALIDATION_STATUSES = [
    ("pending", "Pending"),
    ("validated", "Validated"),
    ("rejected", "Rejected"),
    ("needs_correction", "Needs Correction"),
]

EVIDENCE_STATUSES = [
    ("missing", "Missing"),
    ("uploaded", "Uploaded"),
    ("under_review", "Under Review"),
    ("verified", "Verified"),
    ("rejected", "Rejected"),
    ("replacement_required", "Replacement Required"),
]

SCORE_STATUSES = [
    ("good", "Good"),
    ("warning", "Warning"),
    ("critical", "Critical"),
    ("no_data", "No Data"),
]

RISK_CLASSIFICATIONS = [
    ("accreditation_ready", "Accreditation Ready"),
    ("moderate_risk", "Moderate Risk"),
    ("high_risk", "High Risk"),
]

ALERT_SEVERITIES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

ALERT_STATUSES = [
    ("open", "Open"),
    ("acknowledged", "Acknowledged"),
    ("in_progress", "In Progress"),
    ("resolved", "Resolved"),
    ("escalated", "Escalated"),
]

ACTION_PRIORITIES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

ACTION_STATUSES = [
    ("open", "Open"),
    ("assigned", "Assigned"),
    ("in_progress", "In Progress"),
    ("submitted_for_validation", "Submitted for Validation"),
    ("validated", "Validated"),
    ("verified", "Verified"),
    ("rejected", "Rejected"),
    ("overdue", "Overdue"),
    ("escalated", "Escalated"),
    ("closed", "Closed"),
]


DEFAULT_COMPONENTS = [
    {
        "code": "staffing",
        "name": "Academic Staffing Monitoring",
        "description": "Staff quantity, quality, NUC minimum compliance, and staff development indicators.",
        "weight": Decimal("25.00"),
        "collection_frequency": "semesterly",
        "information_suppliers": "Heads of Departments, Faculty Officers, Establishments Unit",
        "collection_method": "Semesterly forms, HR database integration, annual verification",
        "dashboard_output": "Academic Staffing Readiness Index",
    },
    {
        "code": "curriculum_delivery",
        "name": "Curriculum Delivery Monitoring",
        "description": "CCMAS alignment, approved outlines, LMS usage, teaching delivery, and course coverage.",
        "weight": Decimal("20.00"),
        "collection_frequency": "monthly",
        "information_suppliers": "Course Coordinators, HODs, QA Focal Persons",
        "collection_method": "Monthly forms, LMS reports, departmental submissions",
        "dashboard_output": "Curriculum Delivery Score",
    },
    {
        "code": "student_outcomes",
        "name": "Student Learning Experience Monitoring",
        "description": "Student satisfaction, retention, learning support, pass rate, and graduate outcomes.",
        "weight": Decimal("10.00"),
        "collection_frequency": "semesterly",
        "information_suppliers": "Students, departments, QA Focal Persons",
        "collection_method": "Online surveys, QR-coded feedback forms, departmental returns",
        "dashboard_output": "Student Experience Index",
    },
    {
        "code": "examination_quality",
        "name": "Examination Quality Monitoring",
        "description": "Examination administration, invigilation, malpractice incidence, and result-release timeliness.",
        "weight": Decimal("0.00"),
        "collection_frequency": "semesterly",
        "information_suppliers": "Students, Faculty Examination Officers",
        "collection_method": "Examination evaluation forms and incident reporting",
        "dashboard_output": "Examination Quality Index",
    },
    {
        "code": "laboratory_facilities",
        "name": "Laboratory and Practical Facilities Monitoring",
        "description": "Laboratory functionality, equipment readiness, practical-theory balance, and utilization.",
        "weight": Decimal("0.00"),
        "collection_frequency": "quarterly",
        "information_suppliers": "Laboratory Coordinators, HODs",
        "collection_method": "Quarterly facility audits and photographic evidence",
        "dashboard_output": "Laboratory Readiness Score",
    },
    {
        "code": "library_resources",
        "name": "Library and Learning Resources Monitoring",
        "description": "Current textbooks, journals, e-resources, usage, and collection currency.",
        "weight": Decimal("10.00"),
        "collection_frequency": "semesterly",
        "information_suppliers": "University Librarian, Faculty Librarians",
        "collection_method": "Semester reports and library management system exports",
        "dashboard_output": "Library Resource Index",
    },
    {
        "code": "infrastructure",
        "name": "Infrastructure Monitoring",
        "description": "Classroom adequacy, seating utilization, power, internet uptime, ventilation, and accessibility.",
        "weight": Decimal("15.00"),
        "collection_frequency": "quarterly",
        "information_suppliers": "Works and Maintenance Unit, Faculty Officers, Students",
        "collection_method": "Quarterly infrastructure audits and student feedback",
        "dashboard_output": "Infrastructure Quality Index",
    },
    {
        "code": "research",
        "name": "Research and Innovation Monitoring",
        "description": "Publications, grants, conferences, and postgraduate supervision completion.",
        "weight": Decimal("10.00"),
        "collection_frequency": "annual",
        "information_suppliers": "Academic Staff, Research Management Office",
        "collection_method": "Annual returns and institutional repositories",
        "dashboard_output": "Research Productivity Index",
    },
    {
        "code": "student_support",
        "name": "Student Support Services Monitoring",
        "description": "Academic advising, complaint resolution, counselling, disability support, and student services.",
        "weight": Decimal("0.00"),
        "collection_frequency": "semesterly",
        "information_suppliers": "Students, Student Affairs Division, UHS",
        "collection_method": "Complaint systems, hall evaluation surveys, and support-service returns",
        "dashboard_output": "Student Support Index",
    },
    {
        "code": "qa_compliance",
        "name": "QA Committee Performance Monitoring",
        "description": "Committee constitution, meetings, reports, action plans, and QA Committee Effectiveness Index.",
        "weight": Decimal("10.00"),
        "collection_frequency": "quarterly",
        "information_suppliers": "QA Focal Persons",
        "collection_method": "Quarterly QA Committee Reporting Form",
        "dashboard_output": "QA Committee Effectiveness Index",
    },
]


DEFAULT_METRICS = {
    "staffing": [
        ("total_students", "Total Students", "numeric", None, None, False),
        ("total_academic_staff", "Total Academic Staff", "numeric", None, None, False),
        ("staff_with_phd", "Staff with PhD", "numeric", None, None, False),
        ("staff_meeting_nuc_requirement", "Staff Meeting NUC Requirement", "numeric", None, None, False),
        ("required_staff", "Required Staff", "numeric", None, None, False),
        ("staff_to_student_ratio", "Staff-to-Student Ratio", "numeric", "staff_to_student_ratio", Decimal("20.00"), True),
        ("phd_staff_percentage", "PhD Staff Percentage", "percentage", "phd_staff_percentage", Decimal("60.00"), True),
        ("nuc_minimum_compliance", "NUC Minimum Compliance", "percentage", "nuc_minimum_compliance", Decimal("100.00"), True),
    ],
    "curriculum_delivery": [
        ("lectures_scheduled", "Lectures Scheduled", "numeric", None, None, False),
        ("lectures_held", "Lectures Held", "numeric", None, None, False),
        ("topics_planned", "Topics Planned", "numeric", None, None, False),
        ("topics_completed", "Topics Completed", "numeric", None, None, False),
        ("ccmass_aligned_courses", "CCMAS Aligned Courses", "numeric", None, None, False),
        ("total_courses", "Total Courses", "numeric", None, None, False),
        ("lecture_delivery_rate", "Lecture Delivery Rate", "percentage", "lecture_delivery_rate", Decimal("80.00"), True),
        ("course_coverage", "Course Coverage", "percentage", "course_coverage", Decimal("80.00"), True),
        ("curriculum_compliance", "Curriculum Compliance", "percentage", "curriculum_compliance", Decimal("80.00"), True),
    ],
    "student_outcomes": [
        ("total_student_rating", "Total Student Rating", "numeric", None, None, False),
        ("maximum_possible_rating", "Maximum Possible Rating", "numeric", None, None, False),
        ("returning_students", "Returning Students", "numeric", None, None, False),
        ("total_students", "Total Students", "numeric", None, None, False),
        ("students_passed", "Students Passed", "numeric", None, None, False),
        ("students_examined", "Students Examined", "numeric", None, None, False),
        ("student_satisfaction_index", "Student Satisfaction Index", "percentage", "student_satisfaction_index", Decimal("75.00"), True),
        ("retention_rate", "Retention Rate", "percentage", "retention_rate", Decimal("80.00"), True),
        ("pass_rate", "Pass Rate", "percentage", "pass_rate", Decimal("70.00"), True),
    ],
    "examination_quality": [
        ("cases", "Malpractice Cases", "numeric", None, None, False),
        ("candidates", "Candidates", "numeric", None, None, False),
        ("exam_date", "Exam Date", "date", None, None, False),
        ("result_release_date", "Result Release Date", "date", None, None, False),
        ("malpractice_rate", "Malpractice Rate", "numeric", "malpractice_rate", Decimal("1.00"), True),
        ("result_release_turnaround_time", "Result Release Turnaround Time", "numeric", "result_release_turnaround_time", Decimal("30.00"), True),
    ],
    "laboratory_facilities": [
        ("functional_equipment", "Functional Equipment", "numeric", None, None, False),
        ("total_equipment", "Total Equipment", "numeric", None, None, False),
        ("functionality_rate", "Functionality Rate", "percentage", "functionality_rate", Decimal("80.00"), True),
    ],
    "library_resources": [
        ("core_texts_under_5_years", "Core Texts Under 5 Years", "numeric", None, None, False),
        ("total_core_texts", "Total Core Texts", "numeric", None, None, False),
        ("students_using_library", "Students Using Library", "numeric", None, None, False),
        ("total_students", "Total Students", "numeric", None, None, False),
        ("current_text_percentage", "Current Text Percentage", "percentage", "current_text_percentage", Decimal("70.00"), True),
        ("library_usage_rate", "Library Usage Rate", "percentage", "library_usage_rate", Decimal("60.00"), True),
    ],
    "infrastructure": [
        ("number_of_students", "Number of Students", "numeric", None, None, False),
        ("available_seats", "Available Seats", "numeric", None, None, False),
        ("hours_available", "Internet Hours Available", "numeric", None, None, False),
        ("total_required_hours", "Total Required Internet Hours", "numeric", None, None, False),
        ("seating_capacity_utilization", "Seating Capacity Utilization", "percentage", "seating_capacity_utilization", Decimal("100.00"), True),
        ("internet_uptime", "Internet Uptime", "percentage", "internet_uptime", Decimal("80.00"), True),
    ],
    "research": [
        ("total_publications", "Total Publications", "numeric", None, None, False),
        ("total_academic_staff", "Total Academic Staff", "numeric", None, None, False),
        ("completed_supervisions", "Completed Supervisions", "numeric", None, None, False),
        ("total_supervisions", "Total Supervisions", "numeric", None, None, False),
        ("publications_per_staff", "Publications Per Staff", "numeric", "publications_per_staff", Decimal("1.00"), True),
        ("postgraduate_supervision_completion_rate", "Postgraduate Supervision Completion Rate", "percentage", "postgraduate_supervision_completion_rate", Decimal("70.00"), True),
    ],
    "student_support": [
        ("resolved_complaints", "Resolved Complaints", "numeric", None, None, False),
        ("total_complaints", "Total Complaints", "numeric", None, None, False),
        ("sum_resolution_time", "Sum Resolution Time", "numeric", None, None, False),
        ("total_resolved_complaints", "Total Resolved Complaints", "numeric", None, None, False),
        ("complaint_resolution_rate", "Complaint Resolution Rate", "percentage", "complaint_resolution_rate", Decimal("80.00"), True),
        ("average_complaint_resolution_time", "Average Complaint Resolution Time", "numeric", "average_complaint_resolution_time", Decimal("14.00"), True),
    ],
    "qa_compliance": [
        ("total_qa_score", "Total QA Score", "numeric", None, None, False),
        ("maximum_possible_score", "Maximum Possible Score", "numeric", None, None, False),
        ("qacei", "QA Committee Effectiveness Index", "score", "qacei", Decimal("5.00"), True),
    ],
}

PARI_COMPONENT_CODES = [
    "staffing",
    "curriculum_delivery",
    "infrastructure",
    "library_resources",
    "research",
    "student_outcomes",
    "qa_compliance",
]
