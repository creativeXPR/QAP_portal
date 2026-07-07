from datetime import date

from django.test import TestCase

from .services import calculate_formula, safe_divide


class FormulaServiceTests(TestCase):
    def test_all_required_formulas(self):
        cases = {
            "staff_to_student_ratio": ({"total_students": 200, "total_academic_staff": 10}, 20),
            "phd_staff_percentage": ({"staff_with_phd": 8, "total_academic_staff": 10}, 80),
            "nuc_minimum_compliance": ({"staff_meeting_nuc_requirement": 9, "required_staff": 10}, 90),
            "lecture_delivery_rate": ({"lectures_held": 34, "lectures_scheduled": 40}, 85),
            "course_coverage": ({"topics_completed": 16, "topics_planned": 20}, 80),
            "curriculum_compliance": ({"ccmass_aligned_courses": 18, "total_courses": 20}, 90),
            "student_satisfaction_index": ({"total_student_rating": 420, "maximum_possible_rating": 500}, 84),
            "retention_rate": ({"returning_students": 90, "total_students": 100}, 90),
            "pass_rate": ({"students_passed": 70, "students_examined": 100}, 70),
            "malpractice_rate": ({"cases": 2, "candidates": 1000}, 2),
            "result_release_turnaround_time": ({"exam_date": date(2026, 7, 1), "result_release_date": date(2026, 7, 21)}, 20),
            "functionality_rate": ({"functional_equipment": 45, "total_equipment": 50}, 90),
            "current_text_percentage": ({"core_texts_under_5_years": 30, "total_core_texts": 40}, 75),
            "library_usage_rate": ({"students_using_library": 60, "total_students": 100}, 60),
            "seating_capacity_utilization": ({"number_of_students": 80, "available_seats": 100}, 80),
            "internet_uptime": ({"hours_available": 72, "total_required_hours": 90}, 80),
            "publications_per_staff": ({"total_publications": 20, "total_academic_staff": 10}, 2),
            "postgraduate_supervision_completion_rate": ({"completed_supervisions": 14, "total_supervisions": 20}, 70),
            "complaint_resolution_rate": ({"resolved_complaints": 8, "total_complaints": 10}, 80),
            "average_complaint_resolution_time": ({"sum_resolution_time": 40, "total_resolved_complaints": 8}, 5),
            "qacei": ({"total_qa_score": 45, "maximum_possible_score": 50}, 4.5),
        }
        for formula_key, (values, expected) in cases.items():
            with self.subTest(formula_key=formula_key):
                self.assertEqual(calculate_formula(formula_key, values), expected)

    def test_missing_values_and_division_by_zero_return_none(self):
        self.assertIsNone(safe_divide(1, 0))
        self.assertIsNone(calculate_formula("lecture_delivery_rate", {"lectures_held": 10, "lectures_scheduled": 0}))
        self.assertIsNone(calculate_formula("course_coverage", {"topics_completed": None, "topics_planned": 5}))
