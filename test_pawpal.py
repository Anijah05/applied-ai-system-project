"""Comprehensive test suite for PawPal+ system."""

import pytest
from unittest.mock import patch, MagicMock
from pawpal_system import CareTask, Pet, Owner, Scheduler, GeminiAdvisor


# ===== Test 1: Task Completion and Due Status =====

def test_task_completion():
    task = CareTask(title="Feed dog", duration_minutes=10, priority=8, category="feeding")
    assert task.is_completed is False
    assert task.is_due() is True
    task.mark_complete()
    assert task.is_completed is True
    assert task.is_due() is False


def test_recurring_task_stays_due():
    task = CareTask(
        title="Morning walk", duration_minutes=30, priority=9,
        category="exercise", is_recurring=True
    )
    task.mark_complete()
    assert task.is_completed is True
    assert task.is_due() is True


# ===== Test 2: Task Addition to Pets =====

def test_task_addition():
    pet = Pet(name="Buddy", species="Dog", age=2)
    assert len(pet.get_tasks()) == 0
    task1 = CareTask(title="Morning walk", duration_minutes=30, priority=9, category="exercise")
    task2 = CareTask(title="Feed breakfast", duration_minutes=10, priority=10, category="feeding")
    pet.add_task(task1)
    pet.add_task(task2)
    assert len(pet.get_tasks()) == 2
    assert task1 in pet.get_tasks()
    assert task2 in pet.get_tasks()


# ===== Test 3: Priority-Based Sorting =====

def test_priority_sorting():
    owner = Owner(name="Alex", available_minutes=100)
    pet = Pet(name="Max", species="Dog", age=4)
    pet.add_task(CareTask(title="Brush fur", duration_minutes=10, priority=3, category="grooming"))
    pet.add_task(CareTask(title="Give medicine", duration_minutes=5, priority=10, category="medical"))
    pet.add_task(CareTask(title="Play fetch", duration_minutes=20, priority=6, category="play"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert len(plan) == 3
    assert plan[0].title == "Give medicine"
    assert plan[1].title == "Play fetch"
    assert plan[2].title == "Brush fur"


def test_sorting_with_equal_priorities():
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Mochi", species="Cat", age=2)
    pet.add_task(CareTask(title="Task A", duration_minutes=10, priority=5, category="feeding"))
    pet.add_task(CareTask(title="Task B", duration_minutes=10, priority=5, category="feeding"))
    pet.add_task(CareTask(title="Task C", duration_minutes=10, priority=8, category="feeding"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert plan[0].priority == 8
    assert len(plan) == 3


# ===== Test 4: Time Budget Constraints =====

def test_time_budget_respected():
    owner = Owner(name="Sam", available_minutes=60)
    pet = Pet(name="Rocky", species="Dog", age=5)
    pet.add_task(CareTask(title="Long walk", duration_minutes=45, priority=10, category="exercise"))
    pet.add_task(CareTask(title="Grooming", duration_minutes=30, priority=8, category="grooming"))
    pet.add_task(CareTask(title="Play time", duration_minutes=25, priority=6, category="play"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert sum(t.duration_minutes for t in plan) <= owner.available_minutes
    assert plan[0].title == "Long walk"
    assert len(plan) == 1


def test_exact_time_budget():
    owner = Owner(name="Taylor", available_minutes=60)
    pet = Pet(name="Luna", species="Cat", age=3)
    pet.add_task(CareTask(title="Task 1", duration_minutes=30, priority=10, category="feeding"))
    pet.add_task(CareTask(title="Task 2", duration_minutes=30, priority=9, category="play"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert sum(t.duration_minutes for t in plan) == 60
    assert len(plan) == 2


def test_all_tasks_exceed_budget():
    owner = Owner(name="Chris", available_minutes=30)
    pet = Pet(name="Bear", species="Dog", age=6)
    pet.add_task(CareTask(title="Long activity", duration_minutes=45, priority=10, category="exercise"))
    pet.add_task(CareTask(title="Another long task", duration_minutes=40, priority=9, category="grooming"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert len(plan) == 0


# ===== Test 5: Multi-Pet Task Aggregation =====

def test_multi_pet_task_aggregation():
    owner = Owner(name="Jamie", available_minutes=120)
    dog = Pet(name="Rex", species="Dog", age=4)
    cat = Pet(name="Mittens", species="Cat", age=2)
    bird = Pet(name="Tweety", species="Bird", age=1)

    dog.add_task(CareTask(title="Walk dog", duration_minutes=30, priority=9, category="exercise"))
    dog.add_task(CareTask(title="Feed dog", duration_minutes=10, priority=10, category="feeding"))
    cat.add_task(CareTask(title="Feed cat", duration_minutes=5, priority=10, category="feeding"))
    cat.add_task(CareTask(title="Clean litter", duration_minutes=10, priority=8, category="hygiene"))
    bird.add_task(CareTask(title="Feed bird", duration_minutes=5, priority=9, category="feeding"))

    owner.add_pet(dog)
    owner.add_pet(cat)
    owner.add_pet(bird)

    all_tasks = owner.get_all_tasks()
    assert len(all_tasks) == 5
    titles = [t.title for t in all_tasks]
    assert "Walk dog" in titles
    assert "Feed cat" in titles
    assert "Feed bird" in titles


def test_owner_with_no_pets():
    owner = Owner(name="Alex", available_minutes=100)
    assert len(owner.get_all_tasks()) == 0


def test_pets_with_no_tasks():
    owner = Owner(name="Morgan", available_minutes=100)
    owner.add_pet(Pet(name="Pet1", species="Dog", age=3))
    owner.add_pet(Pet(name="Pet2", species="Cat", age=2))
    assert len(owner.get_all_tasks()) == 0


# ===== Test 6: Input Validation =====

def test_invalid_priority():
    task = CareTask(title="Test", duration_minutes=10, priority=5, category="feeding")
    with pytest.raises(ValueError, match="Priority must be non-negative"):
        task.update_priority(-1)


def test_invalid_duration():
    task = CareTask(title="Test", duration_minutes=10, priority=5, category="feeding")
    with pytest.raises(ValueError, match="Duration must be positive"):
        task.update_duration(0)
    with pytest.raises(ValueError, match="Duration must be positive"):
        task.update_duration(-10)


def test_edit_nonexistent_task():
    pet = Pet(name="Buddy", species="Dog", age=3)
    task = CareTask(title="Nonexistent", duration_minutes=10, priority=5, category="feeding")
    with pytest.raises(ValueError, match="Task 'Nonexistent' not found"):
        pet.edit_task(task)


# ===== Test 7: Constraint Filtering =====

def test_category_constraint_filtering():
    owner = Owner(name="Pat", available_minutes=100)
    pet = Pet(name="Spot", species="Dog", age=4)
    pet.add_task(CareTask(title="Walk", duration_minutes=30, priority=9, category="exercise"))
    pet.add_task(CareTask(title="Feed", duration_minutes=10, priority=10, category="feeding"))
    pet.add_task(CareTask(title="Play", duration_minutes=20, priority=8, category="exercise"))
    owner.add_pet(pet)

    scheduler = Scheduler(constraints="category:exercise")
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert len(plan) == 2
    assert all(t.category == "exercise" for t in plan)


def test_no_constraints():
    owner = Owner(name="River", available_minutes=100)
    pet = Pet(name="Fluffy", species="Cat", age=2)
    pet.add_task(CareTask(title="Task 1", duration_minutes=10, priority=9, category="feeding"))
    pet.add_task(CareTask(title="Task 2", duration_minutes=10, priority=8, category="play"))
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())
    assert len(plan) == 2


def test_constraint_no_matching_tasks():
    owner = Owner(name="Casey", available_minutes=100)
    pet = Pet(name="Whiskers", species="Cat", age=3)
    pet.add_task(CareTask(title="Feed", duration_minutes=10, priority=10, category="feeding"))
    owner.add_pet(pet)

    scheduler = Scheduler(constraints="category:exercise")
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())
    assert len(plan) == 0


# ===== Test 8: Completed Tasks Excluded =====

def test_completed_tasks_excluded():
    owner = Owner(name="Avery", available_minutes=100)
    pet = Pet(name="Max", species="Dog", age=4)
    task1 = CareTask(title="Task 1", duration_minutes=20, priority=10, category="feeding")
    task2 = CareTask(title="Task 2", duration_minutes=20, priority=9, category="play")
    task1.mark_complete()
    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner, owner.get_all_tasks())

    assert len(plan) == 1
    assert plan[0].title == "Task 2"


# ===== Test 9: CareTask to_dict =====

def test_care_task_to_dict():
    """Verify to_dict returns all expected fields with correct values."""
    task = CareTask(
        title="Evening walk",
        duration_minutes=25,
        priority=7,
        category="exercise",
        is_recurring=True,
    )
    d = task.to_dict()
    assert d["title"] == "Evening walk"
    assert d["duration_minutes"] == 25
    assert d["priority"] == 7
    assert d["category"] == "exercise"
    assert d["is_recurring"] is True
    assert d["is_completed"] is False


# ===== Test 10: GeminiAdvisor fallback (no API key) =====

def test_gemini_advisor_disabled_without_key():
    """Verify GeminiAdvisor disables gracefully when no API key is set."""
    with patch.dict("os.environ", {}, clear=True):
        advisor = GeminiAdvisor()
    assert advisor.enabled is False


def test_gemini_advisor_fallback_explanation():
    """Verify fallback explanation is returned when AI is disabled."""
    with patch.dict("os.environ", {}, clear=True):
        advisor = GeminiAdvisor()
    result = advisor._fallback_explanation(
        owner_name="Jordan",
        scheduled_tasks=[
            {"title": "Morning walk", "duration_minutes": 30},
            {"title": "Feed breakfast", "duration_minutes": 10},
        ],
        available_minutes=120,
    )
    assert "Jordan" in result
    assert "40" in result
    assert "120" in result


def test_gemini_advisor_answer_when_disabled():
    """Verify answer_question returns a helpful message when disabled."""
    with patch.dict("os.environ", {}, clear=True):
        advisor = GeminiAdvisor()
    result = advisor.answer_question("What should I feed my cat?", context="")
    assert "GEMINI_API_KEY" in result


# ===== Test 11: Scheduler get_ai_explanation =====

def test_scheduler_get_ai_explanation_before_plan():
    """Verify get_ai_explanation returns a safe default before generate_plan is called."""
    scheduler = Scheduler()
    result = scheduler.get_ai_explanation()
    assert result is not None
    assert isinstance(result, str)


def test_scheduler_get_ai_explanation_after_plan():
    """Verify get_ai_explanation returns a non-empty string after generating a plan."""
    owner = Owner(name="Drew", available_minutes=60)
    pet = Pet(name="Buddy", species="Dog", age=3)
    pet.add_task(CareTask(title="Walk", duration_minutes=30, priority=10, category="exercise"))
    owner.add_pet(pet)

    with patch.dict("os.environ", {}, clear=True):
        scheduler = Scheduler()
        scheduler.generate_plan(owner, owner.get_all_tasks())

    explanation = scheduler.get_ai_explanation()
    assert explanation is not None
    assert len(explanation) > 0


# ===== Test 12: Scheduler reasoning still works (legacy) =====

def test_scheduler_explains_plan():
    """Verify legacy explain_plan still returns a string with key info."""
    owner = Owner(name="Drew", available_minutes=60, preferences="Morning walks preferred")
    pet = Pet(name="Buddy", species="Dog", age=3)
    pet.add_task(CareTask(title="Walk", duration_minutes=30, priority=10, category="exercise"))
    owner.add_pet(pet)

    with patch.dict("os.environ", {}, clear=True):
        scheduler = Scheduler()
        scheduler.generate_plan(owner, owner.get_all_tasks())

    reasoning = scheduler.explain_plan()
    assert reasoning is not None
    assert "Drew" in reasoning
    assert "60 minutes" in reasoning
    assert "Morning walks preferred" in reasoning