import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Tuition Manager", layout="wide")

# ---------------- DATA FOLDER ---------------- #

DATA_DIR = "tuition_data"
os.makedirs(DATA_DIR, exist_ok=True)

students_file = f"{DATA_DIR}/students.csv"
attendance_file = f"{DATA_DIR}/attendance.csv"
fees_file = f"{DATA_DIR}/fees.csv"

# ---------------- CREATE FILES ---------------- #

if not os.path.exists(students_file):
    pd.DataFrame(columns=["id","name","standard","batch","phone"]).to_csv(students_file,index=False)

if not os.path.exists(attendance_file):
    pd.DataFrame(columns=["date","student_id","status"]).to_csv(attendance_file,index=False)

if not os.path.exists(fees_file):
    pd.DataFrame(columns=["student_id","month","amount"]).to_csv(fees_file,index=False)

students_df = pd.read_csv(students_file, dtype=str)
attendance_df = pd.read_csv(attendance_file, dtype=str)
fees_df = pd.read_csv(fees_file, dtype=str)

# ---------------- LOGIN ---------------- #

role = st.sidebar.selectbox("Login As", ["Teacher","Parent"], key="login_role")

# =====================================================
# ==================== TEACHER ========================
# =====================================================

if role == "Teacher":

    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard","Student Management","Attendance","Fees","Parent View"]
    )

# ---------------- DASHBOARD ---------------- #

    if page == "Dashboard":

        st.title("Tuition Dashboard")

        total_students = len(students_df)

        total_attendance = len(attendance_df)

        col1, col2 = st.columns(2)

        col1.metric("Total Students", total_students)
        col2.metric("Total Attendance Records", total_attendance)

# ---------------- STUDENT MANAGEMENT ---------------- #

    elif page == "Student Management":

        st.title("Student Management")

        name = st.text_input("Student Name")
        standard = st.text_input("Standard")
        batch = st.text_input("Batch")
        phone = st.text_input("Parent Phone Number")

        if st.button("Add Student"):

            new_id = str(len(students_df) + 1)

            new_student = pd.DataFrame([{
                "id": new_id,
                "name": name,
                "standard": standard,
                "batch": batch,
                "phone": phone
            }])

            students_df_updated = pd.concat([students_df, new_student])
            students_df_updated.to_csv(students_file, index=False)

            st.success("Student Added Successfully")

        st.subheader("All Students")
        st.dataframe(students_df)

# ---------------- ATTENDANCE ---------------- #

    elif page == "Attendance":

        st.title("Attendance")

        if students_df.empty:
            st.warning("No students added yet")
        else:

            attendance_date = st.date_input("Select Date", value=date.today())

            # Standard Filter
            standards = ["All"] + sorted(students_df["standard"].dropna().unique())
            standard_filter = st.selectbox("Filter by Standard", standards)

            # Batch Filter
            batches = ["All"] + sorted(students_df["batch"].dropna().unique())
            batch_filter = st.selectbox("Filter by Batch", batches)

            filtered_students = students_df.copy()

            if standard_filter != "All":
                filtered_students = filtered_students[
                    filtered_students["standard"] == standard_filter
                ]

            if batch_filter != "All":
                filtered_students = filtered_students[
                    filtered_students["batch"] == batch_filter
                ]

            for _, student in filtered_students.iterrows():

                status = st.selectbox(
                    f"{student['name']} (Std {student['standard']} - {student['batch']})",
                    ["Present","Absent","Holiday"],
                    key=f"att_{student['id']}"
                )

                if st.button(f"Save Attendance {student['id']}", key=f"btn_{student['id']}"):

                    new_record = pd.DataFrame([{
                        "date": attendance_date,
                        "student_id": student["id"],
                        "status": status
                    }])

                    updated_attendance = pd.concat([attendance_df, new_record])
                    updated_attendance.to_csv(attendance_file, index=False)

                    st.success("Attendance Saved")

# ---------------- FEES ---------------- #

    elif page == "Fees":

        st.title("Fees Management")

        student = st.selectbox(
            "Select Student",
            students_df["name"] + " (ID:" + students_df["id"] + ")"
        )

        month = st.text_input("Month (Example: March-2026)")
        amount = st.number_input("Fees Amount")

        if st.button("Save Fees"):

            student_id = student.split("ID:")[1].replace(")","")

            # Remove previous entry of same month
            filtered = fees_df[
                ~((fees_df["student_id"] == student_id) &
                (fees_df["month"] == month))
            ]

            new_fee = pd.DataFrame([{
                "student_id": student_id,
                "month": month,
                "amount": amount
            }])

            updated_fees = pd.concat([filtered, new_fee])
            updated_fees.to_csv(fees_file, index=False)

            st.success("Fees Saved (Previous entry overwritten if existed)")

        st.subheader("All Fees Records")
        st.dataframe(fees_df)

# ---------------- PARENT VIEW (Teacher Preview) ---------------- #

    elif page == "Parent View":

        st.title("Parent Portal Preview")

        phone = st.text_input("Enter Parent Phone Number")

        if phone:

            children = students_df[students_df["phone"] == phone]

            if children.empty:
                st.error("No student found for this phone number")

            else:

                for _, child in children.iterrows():

                    st.subheader(child["name"])

                    st.write("Standard:", child["standard"])
                    st.write("Batch:", child["batch"])

                    child_att = attendance_df[
                        attendance_df["student_id"] == child["id"]
                    ]

                    if child_att.empty:
                        st.info("No attendance records")

                    else:

                        total = len(child_att)

                        present = len(
                            child_att[child_att["status"] == "Present"]
                        )

                        percent = round((present / total) * 100, 2)

                        st.write("Attendance Percentage:", percent,"%")
                        st.dataframe(child_att)

                    st.subheader("Fees")

                    child_fees = fees_df[
                        fees_df["student_id"] == child["id"]
                    ]

                    if child_fees.empty:
                        st.info("No fees records")
                    else:
                        st.dataframe(child_fees)

# =====================================================
# ===================== PARENT ========================
# =====================================================

if role == "Parent":

    st.title("Parent Portal")

    phone = st.text_input("Enter Your Phone Number")

    if phone:

        children = students_df[students_df["phone"] == phone]

        if children.empty:
            st.error("No student linked with this phone number")

        else:

            for _, child in children.iterrows():

                st.subheader(child["name"])

                st.write("Standard:", child["standard"])
                st.write("Batch:", child["batch"])

                child_att = attendance_df[
                    attendance_df["student_id"] == child["id"]
                ]

                if child_att.empty:
                    st.info("No attendance records")

                else:

                    total = len(child_att)

                    present = len(
                        child_att[child_att["status"] == "Present"]
                    )

                    percent = round((present / total) * 100, 2)

                    st.write("Attendance Percentage:", percent,"%")
                    st.dataframe(child_att)

                st.subheader("Fees")

                child_fees = fees_df[
                    fees_df["student_id"] == child["id"]
                ]

                if child_fees.empty:
                    st.info("No fees records")
                else:
                    st.dataframe(child_fees)
