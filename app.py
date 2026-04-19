import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** is an intelligent pet care planning assistant powered by a priority-based
scheduling algorithm and Gemini AI. It helps busy pet owners optimize their daily care
routines across multiple pets.
"""
)

with st.expander("How it works", expanded=False):
    st.markdown(
        """
### Intelligent Scheduling + AI Explanation

**PawPal+** uses a priority-based scheduler that:

1. **Aggregates** tasks from all your pets
2. **Filters** tasks based on your constraints
3. **Prioritizes** urgent and important tasks first (1-10 scale)
4. **Optimizes** task selection to fit your available time budget
5. **Explains** its reasoning using Gemini AI in plain, friendly language

You can also **ask follow-up questions** about the schedule after it's generated.
"""
    )

st.divider()

# ── Session state init ────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "plan" not in st.session_state:
    st.session_state.plan = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Step 1: Owner Profile ─────────────────────────────────────────────────────
st.subheader("👤 Owner Profile")
if st.session_state.owner is None:
    with st.form("owner_form"):
        owner_name = st.text_input("Owner name", value="Jordan")
        available_minutes = st.number_input(
            "Available minutes per day", min_value=30, max_value=480, value=120
        )
        preferences = st.text_area(
            "Care preferences (optional)",
            placeholder="e.g., Prefer outdoor activities in the morning"
        )
        if st.form_submit_button("Create Owner Profile"):
            st.session_state.owner = Owner(
                name=owner_name,
                available_minutes=available_minutes,
                preferences=preferences if preferences else None,
            )
            st.success(f"✅ Owner profile created for {owner_name}!")
            st.rerun()
else:
    owner = st.session_state.owner
    st.info(f"**Owner:** {owner.name} | **Available time:** {owner.available_minutes} min/day")
    if owner.preferences:
        st.caption(f"Preferences: {owner.preferences}")
    if st.button("Reset Owner"):
        for key in ["owner", "current_pet", "scheduler", "plan", "chat_history"]:
            st.session_state[key] = None if key != "chat_history" else []
        st.rerun()

st.divider()

# ── Step 2: Add Pets ──────────────────────────────────────────────────────────
if st.session_state.owner is not None:
    st.subheader("🐾 Add Pets")

    with st.form("pet_form"):
        pet_name = st.text_input("Pet name", value="Mochi")
        species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
        if st.form_submit_button("Add Pet"):
            new_pet = Pet(name=pet_name, species=species, age=age)
            st.session_state.owner.add_pet(new_pet)
            st.success(f"✅ Added {pet_name} the {species}!")
            st.rerun()

    if st.session_state.owner.pets:
        st.markdown("### Your Pets")
        for i, pet in enumerate(st.session_state.owner.pets):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{pet.name}** ({pet.species}, {pet.age} yrs) — {len(pet.tasks)} task(s)")
            with col2:
                if st.button("Select", key=f"select_pet_{i}"):
                    st.session_state.current_pet = pet
                    st.rerun()
    else:
        st.info("No pets added yet. Create one above!")

    st.divider()

    # ── Step 3: Add Tasks ─────────────────────────────────────────────────────
    if st.session_state.current_pet is not None:
        current_pet = st.session_state.current_pet
        st.subheader(f"📋 Tasks for {current_pet.name}")

        with st.form("task_form"):
            col1, col2 = st.columns(2)
            with col1:
                task_title = st.text_input("Task title", value="Morning walk")
                duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=20)
            with col2:
                category = st.selectbox(
                    "Category", ["feeding", "exercise", "grooming", "hygiene", "play", "medical"]
                )
                priority = st.slider("Priority", min_value=1, max_value=10, value=5)
            is_recurring = st.checkbox("Recurring task", value=False)

            if st.form_submit_button("Add Task"):
                new_task = CareTask(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category,
                    is_recurring=is_recurring,
                )
                current_pet.add_task(new_task)
                st.success(f"✅ Added task: {task_title}")
                st.rerun()

        if current_pet.tasks:
            st.markdown("#### Current Tasks")
            for task in current_pet.tasks:
                status = "✅" if task.is_completed else "⏳"
                recurring = "🔄" if task.is_recurring else ""
                st.write(
                    f"{status} {recurring} **{task.title}** — {task.duration_minutes} min "
                    f"| Priority: {task.priority} | Category: {task.category}"
                )
        else:
            st.info(f"No tasks for {current_pet.name} yet.")

        st.divider()

    # ── Step 4: Generate Schedule ─────────────────────────────────────────────
    st.subheader("📅 Generate Daily Schedule")

    scheduler_constraints = st.text_input(
        "Scheduler constraints (optional)",
        placeholder="e.g., category:exercise"
    )

    if st.button("🎯 Generate Optimized Schedule"):
        if not st.session_state.owner.pets:
            st.error("Please add at least one pet first!")
        else:
            all_tasks = st.session_state.owner.get_all_tasks()
            if not all_tasks:
                st.warning("No tasks found. Please add tasks to your pets first!")
            else:
                scheduler = Scheduler(
                    constraints=scheduler_constraints if scheduler_constraints else None
                )
                with st.spinner("Building your schedule and asking Gemini AI to explain it..."):
                    plan = scheduler.generate_plan(st.session_state.owner, all_tasks)

                # Save to session so chat can reference it
                st.session_state.scheduler = scheduler
                st.session_state.plan = plan
                st.session_state.chat_history = []
                st.rerun()

    # ── Display Schedule ──────────────────────────────────────────────────────
    if st.session_state.plan is not None:
        plan = st.session_state.plan
        scheduler = st.session_state.scheduler
        owner = st.session_state.owner
        all_tasks = owner.get_all_tasks()

        total_time = sum(t.duration_minutes for t in plan)
        remaining_time = owner.available_minutes - total_time
        due_tasks = [t for t in all_tasks if t.is_due()]
        excluded_tasks = [t for t in due_tasks if t not in plan]

        st.success("✅ Schedule Generated!")

        if excluded_tasks:
            st.warning(
                f"⚠️ **{len(excluded_tasks)} task(s)** couldn't fit in your time budget."
            )
            with st.expander("View excluded tasks"):
                for task in excluded_tasks:
                    st.write(f"• **{task.title}** ({task.duration_minutes} min, Priority: {task.priority})")

        st.markdown("### 📋 Today's Optimized Schedule")

        if plan:
            for i, task in enumerate(plan, 1):
                if task.priority >= 8:
                    badge = "🔴 HIGH"
                elif task.priority >= 5:
                    badge = "🟡 MEDIUM"
                else:
                    badge = "🟢 LOW"
                recurring_badge = "🔄 Recurring" if task.is_recurring else ""

                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{i}. {task.title}** {recurring_badge}")
                        st.caption(f"Category: {task.category}")
                    with col2:
                        st.write(f"⏱️ {task.duration_minutes} min")
                    with col3:
                        st.write(badge)
                    st.divider()
        else:
            st.info("No tasks fit within your available time budget.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tasks scheduled", f"{len(plan)}/{len(all_tasks)}")
        with col2:
            st.metric("Total time", f"{total_time} min")
        with col3:
            if remaining_time >= 0:
                st.metric("Free time", f"{remaining_time} min", delta="Available")
            else:
                st.metric("Over budget", f"{abs(remaining_time)} min", delta_color="inverse")

        # ── Gemini AI Explanation ─────────────────────────────────────────────
        st.markdown("### 🧠 Gemini AI Explanation")
        ai_explanation = scheduler.get_ai_explanation()
        st.info(ai_explanation)

        with st.expander("Algorithm details"):
            st.write(scheduler.explain_plan())
            st.markdown("""
**Algorithm:** Priority-Based Greedy Scheduler
- Sorts tasks by priority (descending)
- Selects tasks that fit within time budget
- Excludes completed non-recurring tasks
- Applies user-defined constraints
            """)

        # ── Follow-up Chat ────────────────────────────────────────────────────
        st.markdown("### 💬 Ask a Follow-up Question")
        st.caption("Ask Gemini anything about today's schedule or general pet care advice.")

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input("e.g. Why was the morning walk prioritized?")
        if user_input:
            # Show user message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Get and show AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = scheduler.answer_question(
                        user_input,
                        chat_history=st.session_state.chat_history[:-1],
                    )
                st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    st.info("👆 Create an owner profile to get started!")