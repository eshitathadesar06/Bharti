# ---------------- PARENT VIEW ----------------

elif page == "Parent View":

    st.title("👨‍👩‍👧 Parent Portal")

    phone = st.session_state.parent_phone

    children = students_df[
        students_df["phone"].astype(str) == str(phone)
    ]

    if children.empty:
        st.warning("No students found for this phone number")

    else:

        child_options = children["name"].tolist()

        selected_child = st.selectbox("Select Student", child_options)

        child = children[children["name"] == selected_child].iloc[0]

        st.subheader(child["name"])
        st.write("Standard:", child["standard"])
        st.write("Batch:", child["batch"])

        # -------- FEE HISTORY --------

        st.subheader("Fee History")

        student_fees = fees_df[
            fees_df["student_id"].astype(str) == str(child["id"])
        ]

        if student_fees.empty:
            st.info("No fees recorded")

        else:

            fees_display = student_fees.copy()

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

            st.dataframe(fees_display, use_container_width=True, hide_index=True)

        # -------- ATTENDANCE --------

        st.subheader("Attendance Records")

        attendance_df["student_id"] = attendance_df["student_id"].astype(str)

        student_attendance = attendance_df[
            attendance_df["student_id"] == str(child["id"])
        ]

        if student_attendance.empty:

            st.info("No attendance records found for this student.")

        else:

            student_attendance = student_attendance.copy()

            student_attendance["date"] = pd.to_datetime(
                student_attendance["date"],
                errors="coerce"
            )

            student_attendance["Month"] = student_attendance["date"].dt.strftime("%b %Y")

            months = student_attendance["Month"].dropna().unique().tolist()

            selected_month = st.selectbox(
                "Select Month",
                ["All Months"] + months
            )

            if selected_month != "All Months":

                student_attendance = student_attendance[
                    student_attendance["Month"] == selected_month
                ]

            attendance_display = student_attendance.copy()

            attendance_display["Date"] = attendance_display["date"].dt.strftime("%d %B %Y")

            attendance_display["Status"] = attendance_display["status"]

            attendance_display = attendance_display[["Date","Status"]]

            total_days = len(attendance_display)

            present_days = len(
                attendance_display[
                    attendance_display["Status"] == "Present"
                ]
            )

            if total_days > 0:
                percentage = round((present_days / total_days) * 100, 2)
            else:
                percentage = 0

            st.metric("Attendance Percentage", f"{percentage}%")

            st.dataframe(
                attendance_display,
                use_container_width=True,
                hide_index=True
            )
