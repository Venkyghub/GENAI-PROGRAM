import streamlit as st


st.set_page_config(
    page_title="Student Grade App",
    page_icon="📚"
)


# -----------------------------
# Session state
# -----------------------------
if "students" not in st.session_state:
    st.session_state.students = []


# -----------------------------
# Grade calculation
# -----------------------------
def calculate_grade(mark):
    if mark >= 90:
        return "A"
    elif mark >= 80:
        return "B"
    elif mark >= 70:
        return "C"
    elif mark >= 60:
        return "D"
    else:
        return "F"


# -----------------------------
# Title
# -----------------------------
st.title("📚 Student Grade App")
st.write("Add students and view their grades.")


# -----------------------------
# Add Student Form
# -----------------------------
st.subheader("Add Student")

with st.form("student_form"):

    name = st.text_input("Student Name")

    mark = st.number_input(
        "Mark",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0
    )

    submitted = st.form_submit_button("Add Student")

    if submitted:

        if not name.strip():
            st.error("Please enter a student name.")

        elif mark < 0 or mark > 100:
            st.error("Mark must be between 0 and 100.")

        else:

            st.session_state.students.append({
                "Name": name.strip(),
                "Mark": mark,
                "Grade": calculate_grade(mark)
            })

            st.success(f"{name} added successfully!")


# -----------------------------
# Student Table
# -----------------------------
st.subheader("Student List")

if len(st.session_state.students) > 0:

    st.table(st.session_state.students)

    marks = [
        student["Mark"]
        for student in st.session_state.students
    ]

    average = sum(marks) / len(marks)
    highest = max(marks)
    lowest = min(marks)

    # -----------------------------
    # Metrics
    # -----------------------------
    st.subheader("Class Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Class Average",
            f"{average:.2f}"
        )

    with col2:
        st.metric(
            "Highest Mark",
            f"{highest:.0f}"
        )

    with col3:
        st.metric(
            "Lowest Mark",
            f"{lowest:.0f}"
        )

else:

    st.info("No students added yet.")