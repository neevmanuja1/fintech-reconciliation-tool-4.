
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="Fintech Reconciliation",
    page_icon="💳",
    layout="wide"
)

st.title("💳 Fintech Reconciliation Platform")
st.write(
    "Upload payment and bank records to identify "
    "transaction discrepancies automatically."
)

st.info("Prototype: Use fictional or synthetic data only.")

col1, col2 = st.columns(2)

with col1:
    payment_file = st.file_uploader(
        "Upload Payment Records (CSV)",
        type=["csv"],
        key="payments"
    )

with col2:
    bank_file = st.file_uploader(
        "Upload Bank Records (CSV)",
        type=["csv"],
        key="bank"
    )

if payment_file and bank_file:
    try:
        payments = pd.read_csv(
            payment_file, dtype={"Transaction_ID": str}
        )
        bank = pd.read_csv(
            bank_file, dtype={"Transaction_ID": str}
        )

        required = {"Transaction_ID", "Amount"}

        for name, data in [
            ("Payments", payments),
            ("Bank", bank)
        ]:
            if not required.issubset(data.columns):
                st.error(
                    f"{name}: CSV must contain "
                    "Transaction_ID and Amount columns."
                )
                st.stop()

            if data["Transaction_ID"].isna().any():
                st.error(f"{name}: Missing transaction IDs.")
                st.stop()

            if data["Transaction_ID"].duplicated().any():
                st.error(f"{name}: Duplicate transaction IDs.")
                st.stop()

            data["Amount"] = pd.to_numeric(
                data["Amount"], errors="coerce"
            )

            if data["Amount"].isna().any():
                st.error(f"{name}: Invalid or missing amounts.")
                st.stop()


        if st.button("Run Reconciliation", type="primary"):
            st.session_state["show_results"] = True

        if st.session_state.get("show_results", False):
            results = payments.merge(
                bank,
                on="Transaction_ID",
                how="outer",
                suffixes=("_Payment", "_Bank"),
                indicator=True,
                validate="one_to_one"
            )

            def status(row):
                if row["_merge"] == "left_only":
                    return "Missing from Bank"
                if row["_merge"] == "right_only":
                    return "Missing from Payments"
                if row["Amount_Payment"] != row["Amount_Bank"]:
                    return "Amount Mismatch"
                return "Matched"

            results["Status"] = results.apply(status, axis=1)
            
            # Assign priority to discrepancies
            results["Priority"] = "None"

            results.loc[
                results["Status"].isin([
                    "Missing from Bank",
                    "Missing from Payments"
                ]),
                "Priority"
            ] = "High"

            mismatch = results["Status"] == "Amount Mismatch"

            difference = (
                results["Amount_Payment"] -
                results["Amount_Bank"]
            ).abs()

            results.loc[
                mismatch & (difference >= 100),
                "Priority"
            ] = "High"

            results.loc[
                mismatch & (difference >= 25) & (difference < 100),
                "Priority"
            ] = "Medium"

            results.loc[
                mismatch & (difference < 25),
                "Priority"
            ] = "Low"
            
            # Recommend actions for each transaction
            action_map = {
                "Matched": "No action required",
                "Missing from Bank": "Verify bank settlement and check for processing delays",
                "Missing from Payments": "Investigate unrecorded payment in payment system",
                "Amount Mismatch": "Compare payment and bank amounts and investigate difference"
            }

            results["Recommended_Action"] = (
                results["Status"].map(action_map)
            )





            exceptions = results[
                results["Status"] != "Matched"
            ]

            st.success("Reconciliation completed!")

            c1, c2, c3 = st.columns(3)

            c1.metric("Total Transactions", len(results))
            c2.metric(
                "Matched",
                (results["Status"] == "Matched").sum()
            )
            c3.metric("Discrepancies", len(exceptions))

            st.subheader("Transaction Analysis")
            st.bar_chart(results["Status"].value_counts())

          
            st.subheader("Transactions Requiring Review")

            priority_order = {
                "High": 0,
                "Medium": 1,
                "Low": 2
            }
            
            # Filter transactions by priority
           
            with st.form("priority_filter_form"):
                selected_priority = st.selectbox(
                    "Filter transactions by priority",
                    ["All", "High", "Medium", "Low"]
                )

                st.form_submit_button("Apply Filter")




            sorted_exceptions = exceptions.copy()

            if selected_priority != "All":
                sorted_exceptions = sorted_exceptions[
                    sorted_exceptions["Priority"] == selected_priority
                ]

            sorted_exceptions["Priority_Order"] = (
                sorted_exceptions["Priority"].map(priority_order)
            )

            sorted_exceptions = sorted_exceptions.sort_values(
                "Priority_Order"
            )

            st.dataframe(
                sorted_exceptions.drop(
                    columns=["_merge", "Priority_Order"]
                ),
                use_container_width=True,
                hide_index=True
            )


            output = BytesIO()

            with pd.ExcelWriter(
                output, engine="openpyxl"
            ) as writer:
                results.drop(columns=["_merge"]).to_excel(
                    writer,
                    sheet_name="All Transactions",
                    index=False
                )

                exceptions.drop(columns=["_merge"]).to_excel(
                    writer,
                    sheet_name="Discrepancies",
                    index=False
                )

                summary = pd.DataFrame({
                    "Metric": [
                        "Total Transactions",
                        "Matched",
                        "Discrepancies"
                    ],
                    "Value": [
                        len(results),
                        (results["Status"] == "Matched").sum(),
                        len(exceptions)
                    ]
                })

                summary.to_excel(
                    writer,
                    sheet_name="Summary",
                    index=False
                )

            st.download_button(
                "Download Excel Report",
                data=output.getvalue(),
                file_name="Fintech_Reconciliation_Report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            )

    except Exception as e:
        st.error(f"Unable to process files: {e}")

else:
    st.write("Upload both CSV files to begin.")
