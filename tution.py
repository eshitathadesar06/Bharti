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
    students_df["phone"].astype(str)
    .str.replace(".0","",regex=False)
    .str.strip()
)

# ---------------- PAGE ----------------
st.set_page_config(page_title="Tuition Manager", layout="wide")
st.sidebar.title("📚 Tuition Manager")

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
        parent = students_df[students_df["phone"] == phone_clean]
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

    # ---------------- FIXED FEES THIS MONTH ----------------
    # Only include fees for students that exist
    valid_fees = fees_df.merge(
        students_df[["id"]],
        left_on="student_id",
        right_on="id",
        how="inner"
    )

    month = datetime.now().strftime("%Y-%m")
    month_fees = valid_fees[
        valid_fees["date"].astype(str).str.startswith(month)
    ]["amount"].astype(float).sum()
    # --------------------------------------------------------

    col2.metric("Fees This Month", f"₹{month_fees}")

    col3.metric("Total Batches", students_df["batch"].nunique())

    if not students_df.empty:
        st.bar_chart(students_df["standard"].value_counts())
        
# ---------------- STUDENT MANAGEMENT ----------------
elif page == "Student Management":
    st.title("👨‍🎓 Student Management")
    search = st.text_input("Search Student by Name", "")
    display_df = students_df.copy()
    if search:
        display_df = display_df[display_df["name"].str.contains(search, case=False, na=False)]
    st.subheader("Students List")
    st.dataframe(display_df, use_container_width=True)

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
            batch = st.selectbox("Batch", ["Morning","Afternoon","Evening"])
            parent = st.text_input("Parent Name")
            phone = st.text_input("Phone Number")
        submit = st.form_submit_button("Add Student")
        if submit and name:
            new_id = 1 if students_df.empty else int(students_df["id"].astype(int).max())+1
            new_row = pd.DataFrame([[new_id,name,standard,batch,parent,phone]], columns=students_df.columns)
            students_df = pd.concat([students_df,new_row], ignore_index=True)
            students_df.to_csv(FILES["students"], index=False)
            st.success("Student added!")
            st.rerun()

    st.subheader("Delete Student")
    if not students_df.empty:
        student_names = students_df["name"].tolist()
        selected = st.selectbox("Select Student", student_names)
        if st.button("Delete Student"):
            students_df = students_df[students_df["name"] != selected]
            students_df.to_csv(FILES["students"], index=False)
            st.success("Student deleted")
            st.rerun()

# ---------------- ATTENDANCE ----------------
elif page == "Attendance":
    st.title("📅 Attendance Management")
    date = st.date_input("Select Date", datetime.now())
    batch = st.selectbox("Select Batch", ["Morning","Afternoon","Evening"])
    date_str = date.strftime("%Y-%m-%d")

    holidays_file = os.path.join(DATA_DIR, "holidays.csv")
    if not os.path.exists(holidays_file):
        holidays_df = pd.DataFrame(columns=["date","batch"])
        holidays_df.to_csv(holidays_file, index=False)
    else:
        holidays_df = pd.read_csv(holidays_file, dtype=str)

    is_holiday = not holidays_df[(holidays_df["date"]==date_str) & (holidays_df["batch"]==batch)].empty

    col_h1, col_h2 = st.columns([2,2])
    with col_h1:
        if st.button("Mark as Holiday"):
            if is_holiday:
                st.warning(f"{date_str} already holiday for {batch}")
            else:
                holidays_df = pd.concat([holidays_df, pd.DataFrame([[date_str, batch]], columns=["date","batch"])], ignore_index=True)
                holidays_df.to_csv(holidays_file, index=False)
                st.success(f"{date_str} marked as holiday for {batch}")
                st.rerun()
    with col_h2:
        if st.button("Remove Holiday"):
            if is_holiday:
                holidays_df = holidays_df[~((holidays_df["date"]==date_str) & (holidays_df["batch"]==batch))]
                holidays_df.to_csv(holidays_file, index=False)
                st.success(f"Holiday removed for {date_str} {batch}")
                st.rerun()
            else:
                st.warning("No holiday set for this day/batch")

    if is_holiday:
        st.info(f"{date_str} is a holiday for {batch}. Attendance cannot be modified.")
    else:
        batch_students = students_df[students_df["batch"]==batch]
        search = st.text_input("Search Student in Batch", "")
        if search:
            batch_students = batch_students[batch_students["name"].str.contains(search, case=False, na=False)]
        if batch_students.empty:
            st.warning("No students in this batch")
        else:
            st.subheader("Mark Attendance")
            for _, row in batch_students.iterrows():
                sid = str(row["id"])
                name = row["name"]
                current_status = attendance_df[(attendance_df["date"]==date_str) & (attendance_df["student_id"]==sid)]["status"]
                current_status = current_status.iloc[0] if not current_status.empty else "Absent"
                new_status = st.selectbox(f"{name} ({row['standard']})", ["Present","Absent"], index=0 if current_status=="Absent" else 1, key=f"{sid}_{date_str}")
                if st.button(f"Save Attendance for {name}", key=f"save_{sid}_{date_str}"):
                    attendance_df = attendance_df[~((attendance_df["date"]==date_str) & (attendance_df["student_id"]==sid))]
                    attendance_df = pd.concat([attendance_df, pd.DataFrame([[date_str, sid, new_status]], columns=["date","student_id","status"])], ignore_index=True)
                    attendance_df.to_csv(FILES["attendance"], index=False)
                    st.success(f"Attendance updated for {name}")
                    st.rerun()
            st.subheader("Attendance Percentage")
            percentages = []
            for _, s in batch_students.iterrows():
                sid = str(s["id"])
                total_days = len(attendance_df[attendance_df["student_id"]==sid])
                present_days = len(attendance_df[(attendance_df["student_id"]==sid) & (attendance_df["status"]=="Present")])
                percent = (present_days/total_days*100) if total_days>0 else 0
                percentages.append([s["name"], percent])
            st.dataframe(pd.DataFrame(percentages, columns=["Student","Attendance %"]), use_container_width=True)
            
# ---------------- FEES ----------------
elif page == "Fees":
    st.title("💰 Fee Collection")
    if students_df.empty:
        st.warning("Add students first")
    else:
        search = st.text_input("Search Student or Month", "")
        display_students = students_df.copy()
        if search:
            search_lower = search.lower()
            display_students = display_students[display_students.apply(
                lambda x: search_lower in str(x["name"]).lower() or 
                          search_lower in str(x["standard"]).lower() or 
                          search_lower in str(x["batch"]).lower(), axis=1
            )]
        if display_students.empty:
            st.warning("No students found for this search")
        else:
            student = st.selectbox("Student", display_students["name"])
            student_row = students_df[students_df["name"]==student]
            if student_row.empty:
                st.error("Selected student does not exist!")
            else:
                student_id = str(student_row.iloc[0]["id"])
                st.info(f"Standard: {student_row.iloc[0]['standard']} | Batch: {student_row.iloc[0]['batch']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    fee_date = st.date_input("Select Fee Date", datetime.now())
                    month = fee_date.strftime("%b %Y")
                with col2:
                    amount = st.number_input("Amount", min_value=0)
                with col3:
                    method = st.selectbox("Payment Method", ["Cash","UPI","Cheque"])
                if st.button("Record / Update Payment"):
                    date_now = fee_date.strftime("%Y-%m-%d")
                    # Remove previous entry for same student & month
                    fees_df = fees_df[~((fees_df["student_id"].astype(str)==student_id) & (fees_df["month"]==month))]
                    # Add new fee
                    fees_df = pd.concat([fees_df, pd.DataFrame([[date_now, student_id, amount, month, method]], columns=["date","student_id","amount","month","method"])], ignore_index=True)
                    fees_df.to_csv(FILES["fees"], index=False)
                    st.success(f"Fee for {student} ({month}) recorded/updated!")
                    st.rerun()

        # Display Fees Table (only valid students)
        display_fees = fees_df.merge(students_df[["id","name"]], left_on="student_id", right_on="id", how="inner")
        if search:
            search_lower = search.lower()
            display_fees = display_fees[display_fees.apply(lambda x: search_lower in str(x["name"]).lower() or search_lower in str(x["month"]).lower(), axis=1)]
        if display_fees.empty:
            st.info("No fee records found")
        else:
            display_fees = display_fees.rename(columns={"name":"Student Name","date":"Payment Date","month":"Fee Month","amount":"Amount","method":"Payment Method"})
            display_fees = display_fees[["Student Name","Fee Month","Payment Date","Amount","Payment Method"]]
            st.dataframe(display_fees, use_container_width=True)

            # Delete Fee Record (only valid students)
            st.subheader("Delete Fee Record")
            student_names = display_fees["Student Name"].unique().tolist()
            if student_names:
                del_student = st.selectbox("Select Student", student_names, key="del_fee_student")
                student_fees = display_fees[display_fees["Student Name"]==del_student]
                fee_months = student_fees["Fee Month"].tolist()
                del_month = st.selectbox("Select Month to Delete", fee_months, key="del_fee_month")
                if st.button("Delete Fee Record"):
                    del_sid = str(students_df[students_df["name"]==del_student]["id"].iloc[0])
                    fees_df = fees_df[~((fees_df["student_id"]==del_sid) & (fees_df["month"]==del_month))]
                    fees_df.to_csv(FILES["fees"], index=False)
                    st.success(f"Fee record deleted for {del_student}, {del_month}")
                    st.rerun()
                    
# ---------------- PARENT VIEW ----------------
elif page == "Parent View":
    st.title("👨‍👩‍👧 Parent Portal")
    phone = st.session_state.parent_phone
    child = students_df[students_df["phone"]==phone]
    if child.empty:
        st.warning("Student not found")
    else:
        child = child.iloc[0]
        st.subheader(child["name"])
        st.write("Standard:", child["standard"])
        st.write("Batch:", child["batch"])
        st.subheader("Fee History")
        fees = fees_df[fees_df["student_id"]==str(child["id"])]
        if fees.empty:
            st.info("No fees recorded")
        else:
            st.dataframe(fees)
        st.subheader("Attendance Percentage")
        student_att = attendance_df[attendance_df["student_id"]==str(child["id"])]
        total_days = len(student_att)
        present_days = len(student_att[student_att["status"]=="Present"])
        percent = (present_days/total_days*100) if total_days>0 else 0
        st.write(f"{percent:.2f}%")
