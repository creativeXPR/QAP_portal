DOCUMENT_TYPES = [
    ("pdf", "PDF"),
    ("word", "Word"),
    ("powerpoint", "PowerPoint"),
    ("spreadsheet", "Spreadsheet"),
    ("image", "Image"),
    ("link", "Link"),
    ("other", "Other"),
]

RELATED_MODULES = [
    ("general_dqa", "General DQA"),
    ("accreditation", "Accreditation"),
    ("qa_committee", "QA Committee"),
    ("student_assessment", "Student Assessment"),
    ("examination_quality", "Examination Quality"),
    ("student_complaints", "Student Complaints"),
    ("lecture_monitoring", "Lecture Monitoring"),
    ("service_delivery", "Service Delivery"),
    ("institutional_policy", "Institutional Policy"),
    ("platform_documentation", "Platform Documentation"),
]

VISIBILITY_LEVELS = [
    ("private", "Private"),
    ("dqa_only", "DQA Only"),
    ("qa_focal_persons", "QA Focal Persons"),
    ("hods_and_deans", "HODs and Deans"),
    ("committee_members", "Committee Members"),
    ("all_authenticated", "All Authenticated Users"),
    ("public", "Public"),
]

DOCUMENT_STATUSES = [
    ("draft", "Draft"),
    ("pending_review", "Pending Review"),
    ("approved", "Approved"),
    ("published", "Published"),
    ("rejected", "Rejected"),
    ("archived", "Archived"),
    ("expired", "Expired"),
]

REVIEW_DECISIONS = [
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("returned_for_correction", "Returned for Correction"),
]

ACCESS_ACTIONS = [
    ("viewed", "Viewed"),
    ("downloaded", "Downloaded"),
    ("previewed", "Previewed"),
]

DEFAULT_CATEGORIES = [
    ("Policy Documents", "policy-documents", "Official Quality Assurance policy documents."),
    ("Strategy Documents", "strategy-documents", "DQA strategy and planning documents."),
    ("Orientation Materials", "orientation-materials", "QA Focal Persons orientation and debriefing materials."),
    ("Accreditation Documents", "accreditation-documents", "Accreditation templates and reference documents."),
    ("Standard Operating Procedures", "standard-operating-procedures", "DQA SOPs and process documents."),
    ("User Manuals", "user-manuals", "Platform and process user manuals."),
    ("Reporting Templates", "reporting-templates", "Official DQA reporting templates."),
    ("Data Governance Documents", "data-governance-documents", "Data governance guidelines and policies."),
    ("Security Guidelines", "security-guidelines", "Security guidelines for platform and data use."),
    ("General Reference Documents", "general-reference-documents", "Other official DQA reference documents."),
]

ALLOWED_EXTENSIONS = {
    "pdf": {".pdf"},
    "word": {".doc", ".docx", ".odt"},
    "powerpoint": {".ppt", ".pptx"},
    "spreadsheet": {".xls", ".xlsx", ".csv"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "other": set(),
}
