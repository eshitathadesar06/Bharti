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

    col1, col2, col3 = st.columns(3)

    # Total Students
    total_students = len(students_df)
    col1.metric("Total Students", total_students)

    # Current Month
    current_month = datetime.now().strftime("%Y-%m")

    # Calculate Monthly Fees Safely
    if total_students > 0 and not fees_df.empty:

        # Only count fees from existing students
        valid_student_ids = students_df["id"].astype(str)

        filtered_fees = fees_df[
            (fees_df["date"].astype(str).str.startswith(current_month)) &
            (fees_df["student_id"].astype(str).isin(valid_student_ids))
        ]

        if not filtered_fees.empty:
            month_fees = filtered_fees["amount"].astype(float).sum()
        else:
            month_fees = 0

    else:
        month_fees = 0

    col2.metric("Fees Collected (This Month)", f"₹{month_fees}")

    # Total Batches
    if not students_df.empty:
        total_batches = students_df["batch"].nunique()
    else:
        total_batches = 0

    col3.metric("Total Batches", total_batches)

    # Students per Standard Chart
    st.subheader("Students per Standard")

    if not students_df.empty:
        st.bar_chart(students_df["standard"].value_counts())
    else:
        st.info("No students added yet.")

# ---------------- STUDENT MANAGEMENT ----------------

elif page == "Student Management":

    st.title("👨‍🎓 Student Management")

    with st.form("add_student"):

        st.subheader("Add Student")

        c1, c2 = st.columns(2)

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

            # Clean phone input
            phone_clean = str(phone).replace(".0","").strip()

            # Check if student already exists
            duplicate = students_df[
                (students_df["name"].str.lower() == name.lower()) &
                (students_df["phone"].astype(str) == phone_clean)
            ]

            if not duplicate.empty:

                st.warning("⚠ Student already exists!")

            else:

                new_id = 1 if students_df.empty else int(students_df["id"].astype(int).max()) + 1

                new_row = pd.DataFrame(
                    [[new_id, name, standard, batch, parent, phone_clean]],
                    columns=students_df.columns
                )

                students_df = pd.concat([students_df, new_row], ignore_index=True)

                students_df.to_csv(FILES["students"], index=False)

                st.success("Student added successfully!")

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
        # ---------------- STUDENT SELECTION ----------------
        # Display name + ID to avoid duplicates
        student_options = students_df.apply(lambda x: f"{x['name']} ({x['id']})", axis=1)
        student_selection = st.selectbox("Student", student_options)

        # Keep student_id as string to match students_df
        student_id = student_selection.split("(")[-1].replace(")", "")

        # Fetch student safely
        selected_student = students_df[students_df["id"].astype(str) == student_id]
        if selected_student.empty:
            st.error("Selected student not found!")
            st.stop()

        data = selected_student.iloc[0]
        st.info(f"Standard: {data['standard']} | Batch: {data['batch']}")

        # ---------------- INPUTS ----------------
        col1, col2, col3 = st.columns(3)

        with col1:
            month_input = st.text_input(
                "Fee Month",
                datetime.now().strftime("%b %Y")
            )
            # Normalize month format
            try:
                month = pd.to_datetime(month_input, errors='coerce').strftime("%b %Y")
            except:
                month = month_input  # fallback if parsing fails

        with col2:
            amount = st.number_input("Amount", min_value=0)

        with col3:
            method = st.selectbox("Payment Method", ["Cash", "UPI", "Cheque"])

        # ---------------- RECORD / UPDATE ----------------
        if st.button("Record / Update Payment"):
            date_now = datetime.now().strftime("%Y-%m-%d")

            # Ensure student_id column is string
            fees_df["student_id"] = fees_df["student_id"].astype(str)

            # Remove previous entry for same student & month
            fees_df = fees_df[~((fees_df["student_id"] == student_id) & (fees_df["month"] == month))]

            # Add new fee
            new_fee = pd.DataFrame(
                [[date_now, student_id, amount, month, method]],
                columns=["date", "student_id", "amount", "month", "method"]
            )

            fees_df = pd.concat([fees_df, new_fee], ignore_index=True)
            fees_df.to_csv(FILES["fees"], index=False)

            st.success(f"Fee for {data['name']} ({month}) recorded/updated!")

        # ---------------- SHOW CURRENT FEES ----------------
        st.subheader("Fee Records")

        if fees_df.empty:
            st.info("No fee records yet.")
        else:
            fees_display = fees_df.copy()
            fees_display["student_id"] = fees_display["student_id"].astype(str)

            # Merge student names safely
            fees_display = fees_display.merge(
                students_df[["id", "name"]].astype(str),
                left_on="student_id",
                right_on="id",
                how="left"
            )

            fees_display = fees_display.rename(columns={
                "name": "Student Name",
                "date": "Payment Date",
                "month": "Fee Month",
                "amount": "Amount",
                "method": "Payment Method"
            })

            fees_display = fees_display[
                ["Student Name", "Fee Month", "Payment Date", "Amount", "Payment Method"]
            ]

            st.dataframe(fees_display, use_container_width=True)


# ---------------- PARENT VIEW ----------------

elif page == "Parent View":

    st.title("👨‍👩‍👧 Parent Portal")

    phone = st.session_state.parent_phone

    # Get all students linked to this phone number
    children = students_df[
        students_df["phone"].astype(str) == str(phone)
    ]

    if children.empty:

        st.warning("No students found for this phone number")

    else:

        # Always show student selection dropdown
        child_names = children["name"].tolist()

        selected_child = st.selectbox(
            "Select Student",
            child_names
        )

        child = children[
            children["name"] == selected_child
        ].iloc[0]

        st.subheader(child["name"])

        st.write("Standard:", child["standard"])
        st.write("Batch:", child["batch"])

        # -------- FEE HISTORY --------

        st.subheader("Fee History")

        fees = fees_df[
            fees_df["student_id"].astype(str) == str(child["id"])
        ]

        if fees.empty:

            st.info("No fees recorded")

        else:

            fees_display = fees.copy()

            fees_display["Student Name"] = child["name"]

            fees_display = fees_display.rename(columns={
                "date": "Payment Date",
                "month": "Fee Month",
                "amount": "Amount",
                "method": "Payment Method"
            })

            fees_display = fees_display[
                ["Student Name","Fee Month","Payment Date","Amount","Payment Method"]
            ]

            st.dataframe(fees_display, use_container_width=True)
