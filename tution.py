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
            students_df["name"] == student
        ].iloc[0]

        student_id = str(data["id"])

        st.info(
            f"Standard: {data['standard']} | Batch: {data['batch']}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            month = st.text_input(
                "Fee Month",
                datetime.now().strftime("%b %Y")
            )

        with col2:
            amount = st.number_input(
                "Amount",
                min_value=0
            )

        with col3:
            method = st.selectbox(
                "Payment Method",
                ["Cash","UPI","Cheque"]
            )

        if st.button("Record / Update Payment"):

            date_now = datetime.now().strftime("%Y-%m-%d")

            # Remove previous entry for same student & month
            fees_df = fees_df[
                ~(
                    (fees_df["student_id"].astype(str) == student_id) &
                    (fees_df["month"] == month)
                )
            ]

            # Add updated entry
            new_fee = pd.DataFrame(
                [[date_now, student_id, amount, month, method]],
                columns=["date","student_id","amount","month","method"]
            )

            fees_df = pd.concat(
                [fees_df, new_fee],
                ignore_index=True
            )

            fees_df.to_csv(FILES["fees"], index=False)

            st.success(f"Fee for {student} ({month}) recorded/updated!")

        # -------- SHOW CURRENT FEES --------

        st.subheader("Fee Records")

        if fees_df.empty:

            st.info("No fee records yet.")

        else:

            fees_display = fees_df.copy()

            # Map student names
            fees_display = fees_display.merge(
                students_df[["id","name"]],
                left_on="student_id",
                right_on="id",
                how="left"
            )

            fees_display = fees_display.rename(columns={
                "name":"Student Name",
                "date":"Payment Date",
                "month":"Fee Month",
                "amount":"Amount",
                "method":"Payment Method"
            })

            fees_display = fees_display[
                ["Student Name","Fee Month","Payment Date","Amount","Payment Method"]
            ]

            st.dataframe(
                fees_display,
                use_container_width=True
            )
