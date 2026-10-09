
# Default course policy for the hackathon sample

DEFAULT_POLICY = {
    "categories": {
        "Quizzes": {
            "weight": 15,
            "drop_lowest": 1,
            "drop_min_completed": 2,
            "adjust_above": 90,
            "adjust_to": 100
        },
        "Homework": {
            "weight": 15,
            "drop_lowest": 2,
            "drop_min_completed": 3
        },
        "Exams": {
            "weight": 40
        },
        "Final Exam": {
            "weight": 25
        },
        "Attendance": {
            "weight": 5,
            "drop_percent": 5,
            "present": 100,
            "late": 75,
            "absent": 0
        }
    },
    "final_replacement": {
        "enabled": True,
        "target_category": "Exams",
        "only_if_better": True
    },
    "letter_cutoffs": {
        "A": 90,
        "B": 80,
        "C": 70,
        "D": 60
    }
}


# Default scores from the hackathon sample

DEFAULT_SCORES = {
    "Quizzes": [
        {"name": "Quiz 1", "score": 80, "status": "completed"},
        {"name": "Quiz 2", "score": 92, "status": "completed"},
        {"name": "Quiz 3", "score": 70, "status": "completed"},
        {"name": "Quiz 4", "score": None, "status": "not_taken"}
    ],

    "Homework": [
        {"name": "Homework 1", "score": 100, "status": "completed"},
        {"name": "Homework 2", "score": 90, "status": "completed"},
        {"name": "Homework 3", "score": 80, "status": "completed"},
        {"name": "Homework 4", "score": 50, "status": "completed"}
    ],

    "Exams": [
        {"name": "Exam 1", "score": 78, "status": "completed"},
        {"name": "Exam 2", "score": 88, "status": "completed"}
    ],

    "Final Exam": [
        {"name": "Final Exam", "score": None, "status": "not_taken"}
    ],

    "Attendance": [
        {
            "name": f"Day {i + 1}",
            "score": 0 if i == 19 else 100,
            "status": "completed"
        }
        for i in range(20)
    ]
}
