from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Faculty, Department

# Best-effort mapping reconstructed from the monitoring form + UI's known
# academic structure. VERIFY against the official UI department list before
# relying on this for real institutional records.
FACULTY_DEPARTMENTS = {
    "Faculty of Agriculture": [
        "Agricultural Economics",
        "Agronomy",
        "Animal Science",
        "Crop Protection and Environmental Biology",
    ],
    "Faculty of Arts": [
        "Arabic and Islamic Studies",
        "Archaeology and Anthropology",
        "Classics",
        "Communication and Language Arts",
        "English",
        "European Studies (French, German, Russian)",
        "History",
        "Linguistics and African Languages (including Igbo and Yoruba)",
        "Music",
        "Philosophy",
        "Religious Studies",
        "Theatre Arts",
    ],
    "Faculty of Basic Medical Sciences": [
        "Anatomy",
        "Biochemistry",
        "Physiology",
    ],
    "Faculty of Clinical Sciences": [
        "Medicine",
        "Surgery",
        "Obstetrics & Gynaecology",
        "Paediatrics",
        "Ophthalmology",
        "Psychiatry",
    ],
    "Faculty of Dentistry": [],
    "Faculty of Economics and Management Sciences": [
        "Economics",
    ],
    "Faculty of Education": [
        "Health Education",
        "Adult Education",
        "Educational Management",
        "Guidance and Counselling",
        "Human Kinetics and Health Education",
        "Library and Information Studies",
        "Special Education",
        "Teacher Education (Arts, Science, Social Sciences, Pre-Primary)",
    ],
    "Faculty of Law": [
        "Law",
    ],
    "Faculty of Pharmacy": [
        "Pharmaceutics and Industrial Pharmacy (and other specialized Pharmacy departments)",
    ],
    "Faculty of Public Health": [
        "Epidemiology, Medical Statistics and Environmental Health (EMSEH)",
        "Health Policy and Management",
        "Health Promotion and Education",
        "Human Nutrition and Dietetics",
    ],
    "Faculty of Renewable Natural Resources": [
        "Aquaculture and Fisheries Management",
        "Agricultural Extension and Rural Development",
        "Forest Resources Management",
        "Wildlife and Ecotourism Management",
        "Wood Products Engineering",
    ],
    "Faculty of Science": [
        "Botany",
        "Chemistry",
        "Computer Science",
        "Geography",
        "Geology",
        "Mathematics",
        "Microbiology",
        "Physics",
        "Statistics",
        "Zoology",
    ],
    "Faculty of Social Sciences": [
        "Political Science",
        "Psychology",
        "Sociology",
    ],
    "Faculty of Technology": [
        "Agricultural and Environmental Engineering",
        "Civil Engineering",
        "Electrical and Electronic Engineering",
        "Food Technology",
        "Industrial and Production Engineering",
        "Mechanical Engineering",
        "Petroleum Engineering",
    ],
    "Faculty of Veterinary Medicine": [
        "Veterinary Anatomy",
        "Veterinary Physiology, Biochemistry and Pharmacology (and other specialized Veterinary departments)",
    ],
    "The College of Medicine": [
        "Bioethics and Medical Humanities",
    ],
    "Institute for Advanced Medical Research and Training (IAMRAT)": [],
    "Institute of African Studies": [],
    "Institute of Child Health": [],
    "Institute of Education": [],
    "Institute for Peace and Strategic Studies (IPSS)": [
        "Peace, Security and Humanitarian Studies",
    ],
    "Yoruba Language Centre": [],
    "Centre for Child and Adolescent Mental Health": [],
    "Centre for Petroleum, Energy Economics and Law (CPEEL)": [
        "Mineral, Petroleum, Energy, Economics and Law",
    ],
    "Centre for Control and Prevention of Zoonoses": [],
    "Centre for Drug Discovery, Development and Production (CDDDP)": [],
    "Centre for Entrepreneurship and Innovation": [],
    "Pan African University Life and Earth Sciences Institute (PAULESI)": [],
    "Faculty of Computing": [
        "Data & Information Science",
    ],
    "Centre for Educational Media Resource Studies": [],
    "Distance Learning Centre (DLC)": [],
    "Multidisciplinary Studies": [
        "Sustainability Studies",
    ],
}


class Command(BaseCommand):
    help = "Seed Faculty and Department records from the UI QA monitoring form."

    def handle(self, *args, **options):
        created_faculties = 0
        created_departments = 0

        with transaction.atomic():
            for faculty_name, department_names in FACULTY_DEPARTMENTS.items():
                faculty, was_created = Faculty.objects.get_or_create(name=faculty_name)
                created_faculties += int(was_created)

                for dept_name in department_names:
                    _, was_created = Department.objects.get_or_create(
                        faculty=faculty, name=dept_name
                    )
                    created_departments += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Faculties created: {created_faculties}. "
                f"Departments created: {created_departments}."
            )
        )