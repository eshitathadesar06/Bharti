import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ---------------- CONFIG ----------------

DATA_DIR = "tuition_data"

FILES = {
    "students": os.path.join(DATA_DIR, "students.csv"),
    "attendance": os.path.join(DATA_DIR, "attendance.csv"),
    "fees": os.path.join(DATA_DIR, "fees.csv"),
}

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- LOAD DATA ----------------

def load_data(key, columns):

    path = FILES[key]

    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

    try:
        df = pd.read_csv(path, dtype=str)
        df = df.fillna("")
        return df
    except:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df


students_df = load_data(
    "students",
    ["id","name","standard","batch","parent_name","phone"]
)

attendance_df = load_data(
    "attendance",
    ["date","student_id","status"]
)

fees_df = load_data(
    "fees",
    ["date","student_id","amount","month","method"]
)

# ---------------- CLEAN PHONE NUMBERS ----------------

students_df["phone"] = (
    students_df["phone"]
    .astype(str)
    .str.replace(".0","",regex=False)
    .str.strip()
)

# ---------------- PAGE ----------------

st.set_page_config(page_title="Bharti Tution", layout="wide")

st.sidebar.title("📚 Bharti Tution")

# ---------------- LOGIN ----------------

role = st.sidebar.selectbox("Login As", ["Teacher","Parent"])

if "role" not in st.session_state:
    st.session_state.role = None

# -------- TEACHER LOGIN --------

if role == "Teacher":

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):

        if username == "admin" and password == "teacher123":

            st.session_state.role = "teacher"
            st.rerun()

        else:
            st.sidebar.error("Invalid login")

# -------- PARENT LOGIN --------

elif role == "Parent":

    phone = st.sidebar.text_input("Enter Registered Phone Number")

    if st.sidebar.button("Login"):

        phone_clean = str(phone).replace(".0","").strip()

        parent = students_df[
            students_df["phone"] == phone_clean
        ]

        if not parent.empty:

            st.session_state.role = "parent"
            st.session_state.parent_phone = phone_clean
            st.rerun()

        else:
            st.sidebar.error("Phone number not found")

# Stop if not logged in

if st.session_state.role is None:

    st.title("Welcome to Tuition Manager")
    st.info("Please login from sidebar")

    st.stop()

# ---------------- TEACHER PANEL ----------------

if st.session_state.role == "teacher":

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard","Student Management","Attendance","Fees"]
    )

# ---------------- PARENT PANEL ----------------

elif st.session_state.role == "parent":

    page = "Parent View"


# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("📊 Dashboard")

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Students", len(students_df))

    month = datetime.now().strftime("%Y-%m")

    month_fees = fees_df[
        fees_df["date"].astype(str).str.startswith(month)
    ]["amount"].astype(float).sum()

    col2.metric("Fees This Month", f"₹{month_fees}")

    col3.metric("Total Batches", students_df["batch"].nunique())

    if not students_df.empty:

        st.bar_chart(students_df["standard"].value_counts())


# ---------------- STUDENT MANAGEMENT ----------------

elif page == "Student Management":

    st.title("👨‍🎓 Student Management")

    with st.form("add_student"):

        st.subheader("Add Student")

        c1,c2 = st.columns(2)

        with c1:

            name = st.text_input("Student Name")

            standard = st.selectbox(
                "Standard",
                ["Jr KG","Sr KG","1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th"]
            )

        with c2:

            batch = st.selectbox(
                "Batch",
                ["Morning","Afternoon","Evening"]
            )

            parent = st.text_input("Parent Name")
            phone = st.text_input("Phone Number")

        submit = st.form_submit_button("Add Student")

        if submit and name:

            new_id = 1 if students_df.empty else int(students_df["id"].astype(int).max())+1

            new_row = pd.DataFrame(
                [[new_id,name,standard,batch,parent,phone]],
                columns=students_df.columns
            )

            students_df = pd.concat([students_df,new_row], ignore_index=True)

            students_df.to_csv(FILES["students"], index=False)

            st.success("Student added!")

            st.rerun()

    st.subheader("Students List")

    st.dataframe(students_df, use_container_width=True)

    # -------- DELETE STUDENT --------

    st.subheader("Delete Student")

    if not students_df.empty:

        student_names = students_df["name"].tolist()

        selected = st.selectbox("Select Student", student_names)

        if st.button("Delete Student"):

            students_df = students_df[
                students_df["name"] != selected
            ]

            students_df.to_csv(FILES["students"], index=False)

            st.success("Student deleted")

            st.rerun()


# ---------------- ATTENDANCE ----------------

elif page == "Attendance":

    st.title("📅 Attendance")

    date = st.date_input("Date", datetime.now())

    batch = st.selectbox(
        "Batch",
        ["Morning","Afternoon","Evening"]
    )

    date_str = date.strftime("%Y-%m-%d")

    batch_students = students_df[
        students_df["batch"] == batch
    ]

    if batch_students.empty:

        st.warning("No students in this batch")

    else:

        st.subheader("Mark Attendance")

        for _, row in batch_students.iterrows():

            sid = str(row["id"])
            name = row["name"]

            # check existing attendance
            existing = attendance_df[
                (attendance_df["date"] == date_str)
                & (attendance_df["student_id"].astype(str) == sid)
            ]

            default_status = "Present"

            if not existing.empty:
                default_status = existing.iloc[0]["status"]

            col1, col2 = st.columns([3,2])

            with col1:
                st.write(f"**{name} ({row['standard']})**")

            with col2:

                status = st.radio(
                    "Status",
                    ["Present","Absent"],
                    index=0 if default_status=="Present" else 1,
                    key=f"{sid}_{date_str}"
                )

                if st.button("Save", key=f"save_{sid}_{date_str}"):

                    attendance_df = attendance_df[
                        ~(
                            (attendance_df["date"] == date_str)
                            & (attendance_df["student_id"].astype(str) == sid)
                        )
                    ]

                    new_row = pd.DataFrame(
                        [[date_str, sid, status]],
                        columns=["date","student_id","status"]
                    )

                    attendance_df = pd.concat(
                        [attendance_df, new_row],
                        ignore_index=True
                    )

                    attendance_df.to_csv(FILES["attendance"], index=False)

                    st.success(f"{name} marked {status}")

# ---------------- FEES ----------------

elif page == "Fees":

    st.title("💰 Fee Collection")

    if students_df.empty:

        st.warning("Add students first")

    else:

        student = st.selectbox(
            "Student",
            students_df["name"]
        )

        data = students_df[
            students_df["name"]==student
        ].iloc[0]

        amount = st.number_input("Amount", min_value=0)

        method = st.selectbox(
            "Method",
            ["Cash","UPI"]
        )

        month = st.text_input(
            "Month",
            datetime.now().strftime("%b %Y")
        )

        if st.button("Record Payment"):

            new = pd.DataFrame(
                [[
                    datetime.now().strftime("%Y-%m-%d"),
                    data["id"],
                    amount,
                    month,
                    method
                ]],
                columns=fees_df.columns
            )

            fees_df = pd.concat([fees_df,new], ignore_index=True)

            fees_df.to_csv(FILES["fees"], index=False)

            st.success("Payment recorded")


# ---------------- PARENT VIEW ----------------

elif page == "Parent View":

    st.title("👨‍👩‍👧 Parent Portal")

    phone = st.session_state.parent_phone

    child = students_df[
        students_df["phone"] == phone
    ]

    if child.empty:

        st.warning("Student not found")

    else:

        child = child.iloc[0]

        st.subheader(child["name"])

        st.write("Standard:", child["standard"])
        st.write("Batch:", child["batch"])

        st.subheader("Fee History")

        fees = fees_df[
            fees_df["student_id"].astype(str) == str(child["id"])
        ]

        if fees.empty:

            st.info("No fees recorded")

        else:

            # Add student name column
            fees_display = fees.copy()
            fees_display["Student Name"] = child["name"]

            # Reorder columns
            fees_display = fees_display[
                ["Student Name","date","amount","month","method"]
            ]

            st.dataframe(fees_display, use_container_width=True)
