import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# -------------------- Data Setup --------------------
# Load or create student and fees data
try:
    students_df = pd.read_csv("students.csv")
except:
    students_df = pd.DataFrame(columns=['StudentID','Name','Batch','Phone','MotherName','ParentID'])

try:
    attendance_df = pd.read_csv("attendance.csv")
except:
    attendance_df = pd.DataFrame(columns=['StudentID','Date','Status'])

try:
    fees_df = pd.read_csv("fees.csv")
except:
    fees_df = pd.DataFrame(columns=['StudentID','Month','Amount'])

try:
    announcements_df = pd.read_csv("announcements.csv")
except:
    announcements_df = pd.DataFrame(columns=['Date','Announcement'])

# -------------------- Sidebar Navigation --------------------
st.sidebar.title("Tuition Manager")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Students", "Fees", "Parent Portal", "Announcements"])

# -------------------- Dashboard --------------------
if menu == "Dashboard":
    st.title("Dashboard")
    
    total_students = len(students_df)
    today = datetime.today().date()
    today_attendance = attendance_df[attendance_df['Date'] == str(today)]
    attended_students = today_attendance[today_attendance['Status'] == "Present"]
    monthly_attendance_percent = (len(attended_students)/total_students*100) if total_students > 0 else 0
    
    st.subheader("Metrics")
    st.write(f"**Total Students:** {total_students}")
    st.write(f"**Today's Attendance:** {len(attended_students)}")
    st.write(f"**Monthly Attendance %:** {monthly_attendance_percent:.2f}%")
    
    # Attendance Graph
    st.subheader("Attendance Graph")
    if not attendance_df.empty:
        attendance_df['Date'] = pd.to_datetime(attendance_df['Date'])
        daily_attendance = attendance_df[attendance_df['Status']=="Present"].groupby('Date').count()['StudentID']
        plt.figure(figsize=(10,4))
        daily_attendance.plot(kind='bar', color='skyblue')
        plt.ylabel("Present Students")
        plt.xlabel("Date")
        plt.title("Daily Attendance")
        st.pyplot(plt)
    else:
        st.write("No attendance data yet.")

# -------------------- Students --------------------
elif menu == "Students":
    st.title("Student Management")
    
    batch_filter = st.selectbox("Select Batch", ["All"] + list(students_df['Batch'].unique()))
    search_name = st.text_input("Search by Name")
    
    filtered_df = students_df.copy()
    if batch_filter != "All":
        filtered_df = filtered_df[filtered_df['Batch']==batch_filter]
    if search_name:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(search_name, case=False)]
    
    st.dataframe(filtered_df)
    
    # Attendance entry
    st.subheader("Mark Attendance")
    student_options = filtered_df['Name'].tolist()
    selected_student = st.selectbox("Select Student", student_options)
    status = st.radio("Status", ["Present", "Absent"])
    
    if st.button("Submit Attendance"):
        student_id = students_df[students_df['Name']==selected_student]['StudentID'].values[0]
        today_str = str(datetime.today().date())
        
        # Overwrite if exists
        attendance_df = attendance_df[~((attendance_df['StudentID']==student_id) & (attendance_df['Date']==today_str))]
        attendance_df = pd.concat([attendance_df, pd.DataFrame({'StudentID':[student_id],'Date':[today_str],'Status':[status]})])
        attendance_df.to_csv("attendance.csv", index=False)
        st.success("Attendance recorded successfully!")

# -------------------- Fees --------------------
elif menu == "Fees":
    st.title("Manage Fees")
    
    student_name = st.selectbox("Select Student", students_df['Name'].tolist())
    month = st.selectbox("Month", pd.date_range('2026-01-01', periods=12, freq='M').strftime('%B'))
    amount = st.number_input("Fee Amount", min_value=0)
    
    if st.button("Submit Fee"):
        student_id = students_df[students_df['Name']==student_name]['StudentID'].values[0]
        # Overwrite existing month
        fees_df = fees_df[~((fees_df['StudentID']==student_id) & (fees_df['Month']==month))]
        fees_df = pd.concat([fees_df, pd.DataFrame({'StudentID':[student_id],'Month':[month],'Amount':[amount]})])
        fees_df.to_csv("fees.csv", index=False)
        st.success("Fee recorded successfully!")
    
    # View fees
    st.subheader("Monthly Fees")
    st.dataframe(fees_df.merge(students_df[['StudentID','Name']], on='StudentID')[['Name','Month','Amount']])

# -------------------- Parent Portal --------------------
elif menu == "Parent Portal":
    st.title("Parent Portal")
    
    parent_ids = students_df['ParentID'].unique()
    selected_parent = st.selectbox("Select Parent", parent_ids)
    
    # Children switch
    children = students_df[students_df['ParentID']==selected_parent]
    child_name = st.selectbox("Select Child", children['Name'])
    
    st.subheader(f"Attendance for {child_name}")
    student_id = children[children['Name']==child_name]['StudentID'].values[0]
    student_attendance = attendance_df[attendance_df['StudentID']==student_id]
    
    if not student_attendance.empty:
        student_attendance['Date'] = pd.to_datetime(student_attendance['Date'])
        present_count = len(student_attendance[student_attendance['Status']=="Present"])
        total_count = len(student_attendance)
        percentage = (present_count/total_count*100) if total_count>0 else 0
        st.write(f"**Attendance Percentage:** {percentage:.2f}%")
        st.dataframe(student_attendance[['Date','Status']])
    else:
        st.write("No attendance data available.")
    
    st.subheader(f"Fees for {child_name}")
    child_fees = fees_df[fees_df['StudentID']==student_id]
    st.dataframe(child_fees[['Month','Amount']])

# -------------------- Announcements --------------------
elif menu == "Announcements":
    st.title("Announcements")
    
    if "Admin" in st.session_state.get("role", ["Admin"]):  # Replace with actual admin check
        st.subheader("Add Announcement")
        new_announcement = st.text_area("Announcement Text")
        if st.button("Add Announcement"):
            announcements_df = pd.concat([announcements_df, pd.DataFrame({'Date':[str(datetime.today().date())],'Announcement':[new_announcement]})])
            announcements_df.to_csv("announcements.csv", index=False)
            st.success("Announcement added!")
    
    st.subheader("All Announcements")
    if not announcements_df.empty:
        st.dataframe(announcements_df.sort_values('Date', ascending=False))
    else:
        st.write("No announcements yet.")
