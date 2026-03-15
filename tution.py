import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
DATA_DIR = "tuition_data"

FILES = {
    "students": os.path.join(DATA_DIR, "students.csv"),
    "attendance": os.path.join(DATA_DIR, "attendance.csv"),
    "fees": os.path.join(DATA_DIR, "fees.csv"),
    "holidays": os.path.join(DATA_DIR, "holidays.csv"),
}

# Create folder if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# --- LOAD OR CREATE DATA ---
def load_data(key, columns):
    path = FILES[key]

    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

    try:
        return pd.read_csv(path)
    except:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df


students_df = load_data(
    "students",
    ["id", "name", "standard", "batch", "parent_name", "phone"]
)

attendance_df = load_data(
    "attendance",
    ["date", "student_id", "status"]
)

fees_df = load_data(
    "fees",
    ["date", "student_id", "amount", "month", "method"]
)

holidays_df = load_data(
    "holidays",
    ["date", "batch"]
)

# --- PAGE SETUP ---
st.set_page_config(page_title="Tuition Manager", layout="wide")

st.sidebar.title("📚 Tuition Manager")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Student Management", "Attendance", "Fees", "Parent View"]
)

# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("📊 Dashboard Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Students", len(students_df))

    with col2:
        current_month_str = datetime.now().strftime("%Y-%m")

        if not fees_df.empty:
            month_fees = fees_df[
                fees_df["date"].astype(str).str.startswith(current_month_str, na=False)
            ]["amount"].sum()
        else:
            month_fees = 0

        st.metric("Fees Collected (This Month)", f"₹{month_fees}")

    with col3:
        st.metric("Total Batches", students_df["batch"].nunique())

    st.subheader("Students per Standard")

    if not students_df.empty:
        st.bar_chart(students_df["standard"].value_counts())
    else:
        st.info("No students added yet.")

# ---------------- STUDENT MANAGEMENT ----------------

elif page == "Student Management":

    st.title("👧👦 Student Management")

    with st.form("add_student_form"):

        st.subheader("Add New Student")

        c1, c2 = st.columns(2)

        with c1:
            name = st.text_input("Student Name")

            standard = st.selectbox(
                "Standard",
                [
                    "Jr KG","Sr KG","1st","2nd","3rd","4th",
                    "5th","6th","7th","8th","9th","10th"
                ]
            )

        with c2:
            batch = st.selectbox(
                "Batch",
                ["Morning","Afternoon","Evening"]
            )

            parent_name = st.text_input("Parent Name")

            phone = st.text_input("Phone Number")

        submitted = st.form_submit_button("Add Student")

        if submitted and name:

            new_id = 1 if students_df.empty else students_df["id"].max() + 1

            new_data = pd.DataFrame(
                [[new_id, name, standard, batch, parent_name, phone]],
                columns=[
                    "id","name","standard","batch","parent_name","phone"
                ]
            )

            students_df = pd.concat([students_df, new_data], ignore_index=True)

            students_df.to_csv(FILES["students"], index=False)

            st.success(f"Student '{name}' added successfully!")

            st.rerun()

    st.subheader("Current Students List")

    st.dataframe(students_df, use_container_width=True)

    st.markdown("---")

    # -------- DELETE STUDENT FEATURE --------

    st.subheader("Delete Student")

    if not students_df.empty:

        student_to_delete = st.selectbox(
            "Select Student to Delete",
            students_df["name"]
        )

        if st.button("Delete Student"):

            students_df = students_df[
                students_df["name"] != student_to_delete
            ]

            students_df.to_csv(FILES["students"], index=False)

            st.success(f"{student_to_delete} deleted successfully")

            st.rerun()

    else:
        st.info("No students available to delete.")
# ---------------- ATTENDANCE ----------------

elif page == "Attendance":

    st.title("📅 Attendance Manager")

    # GLOBAL HOLIDAY

    with st.expander("🗓️ Mark Global Holiday (All Batches)"):

        st.warning("Use this to mark a holiday for the ENTIRE tuition class.")

        h_date = st.date_input("Select Holiday Date", datetime.now())

        h_date_str = h_date.strftime("%Y-%m-%d")

        if st.button("Mark as Global Holiday"):

            batches = students_df["batch"].unique()

            if len(batches) == 0:

                st.error("No batches found. Add students first.")

            else:

                for b in batches:

                    if not (
                        (holidays_df["date"] == h_date_str)
                        & (holidays_df["batch"] == b)
                    ).any():

                        new_hol = pd.DataFrame(
                            [[h_date_str, b]],
                            columns=["date", "batch"]
                        )

                        holidays_df = pd.concat(
                            [holidays_df, new_hol],
                            ignore_index=True
                        )

                holidays_df.to_csv(FILES["holidays"], index=False)

                st.success(
                    f"Marked {h_date_str} as a Holiday for all batches!"
                )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        selected_date = st.date_input("Date", datetime.now())
        date_str = selected_date.strftime("%Y-%m-%d")

    with col2:
        selected_batch = st.selectbox(
            "Batch",
            ["Morning","Afternoon","Evening"]
        )

    is_holiday = (
        (holidays_df["date"] == date_str)
        & (holidays_df["batch"] == selected_batch)
    ).any()

    if is_holiday:

        st.info("🗓️ This day is marked as a HOLIDAY.")

        if st.button(f"Revoke Holiday for {selected_batch}"):

            holidays_df = holidays_df[
                ~(
                    (holidays_df["date"] == date_str)
                    & (holidays_df["batch"] == selected_batch)
                )
            ]

            holidays_df.to_csv(FILES["holidays"], index=False)

            st.rerun()

    else:

        batch_students = students_df[
            students_df["batch"] == selected_batch
        ]

        if batch_students.empty:

            st.warning("No students in this batch.")

        else:

            st.subheader("Mark Attendance")

            today_att = attendance_df[
                attendance_df["date"] == date_str
            ]

            for _, row in batch_students.iterrows():

                sid = row["id"]
                sname = row["name"]

                current_att = today_att[
                    today_att["student_id"] == sid
                ]

                status = "Present"

                if not current_att.empty:
                    status = current_att.iloc[0]["status"]

                col1, col2 = st.columns([1,4])

                with col1:

                    label = "✅ Present" if status == "Present" else "❌ Absent"

                    if st.button(label, key=f"{sid}_{date_str}"):

                        new_status = "Absent" if status == "Present" else "Present"

                        attendance_df = attendance_df[
                            ~(
                                (attendance_df["date"] == date_str)
                                & (attendance_df["student_id"] == sid)
                            )
                        ]

                        new_row = pd.DataFrame(
                            [[date_str, sid, new_status]],
                            columns=["date","student_id","status"]
                        )

                        attendance_df = pd.concat(
                            [attendance_df, new_row],
                            ignore_index=True
                        )

                        attendance_df.to_csv(FILES["attendance"], index=False)

                        st.rerun()

                with col2:
                    st.write(f"**{sname}** ({row['standard']})")

# ---------------- FEES ----------------

elif page == "Fees":

    st.title("💰 Fee Collection")

    tab1, tab2 = st.tabs(["Collect Fee","Defaulters List"])

    with tab1:

        if students_df.empty:

            st.warning("Please add students first.")

        else:

            student_names = students_df["name"].tolist()

            selected_student = st.selectbox(
                "Select Student",
                student_names
            )

            student_data = students_df[
                students_df["name"] == selected_student
            ].iloc[0]

            st.info(
                f"Standard: {student_data['standard']} | Batch: {student_data['batch']}"
            )

            c1,c2,c3 = st.columns(3)

            with c1:
                fee_month = st.text_input(
                    "Month",
                    datetime.now().strftime("%b %Y")
                )

            with c2:
                amount = st.number_input("Amount", min_value=0)

            with c3:
                method = st.selectbox(
                    "Method",
                    ["Cash","UPI","Cheque"]
                )

            if st.button("Record Payment"):

                date_now = datetime.now().strftime("%Y-%m-%d")

                new_fee = pd.DataFrame(
                    [[date_now, student_data["id"], amount, fee_month, method]],
                    columns=["date","student_id","amount","month","method"]
                )

                fees_df = pd.concat([fees_df,new_fee], ignore_index=True)

                fees_df.to_csv(FILES["fees"], index=False)

                st.success(f"Collected ₹{amount} from {selected_student}")

# ---------------- PARENT VIEW ----------------

elif page == "Parent View":

    st.title("👨‍👩‍👧 Parent Portal")

    if students_df.empty:

        st.warning("No students registered.")

    else:

        selected_child = st.selectbox(
            "Select Student",
            students_df["name"].unique()
        )

        child = students_df[
            students_df["name"] == selected_child
        ].iloc[0]

        child_id = child["id"]

        st.subheader("Fee History")

        child_fees = fees_df[
            fees_df["student_id"] == child_id
        ]

        if child_fees.empty:
            st.info("No fee records found.")

        else:
            st.dataframe(child_fees)
