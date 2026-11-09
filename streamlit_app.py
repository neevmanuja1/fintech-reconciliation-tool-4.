
import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib

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

# Reset previous results when uploaded files change
if payment_file and bank_file:
    file_signature = (
        hashlib.sha256(payment_file.getvalue()).hexdigest(),
        hashlib.sha256(bank_file.getvalue()).hexdigest()
    )

    if st.session_state.get("file_signature") != file_signature:
        st.session_state["file_signature"] = file_signature
        st.session_state["show_results"] = False

    try:
        payments = pd.read_csv(
            payment_file,
            dtype={"Transaction_ID": str}
        )

        bank = pd.read_csv(
            bank_file,
            dtype={"Transaction_ID": str}
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
                data["Amount"],
                errors="coerce"
            )

            if data["Amount"].isna().any():
                st.error(
                    f"{name}: Invalid or missing amounts."
                )
                st.stop()

        if st.button(
            "Run Reconciliation",
            type="primary"
        ):
            st.session_state["show_results"] = True

        if st.session_state.get("show_results", False):

            # Merge payment and bank records
            results = payments.merge(
                bank,
                on="Transaction_ID",
                how="outer",
                suffixes=("_Payment", "_Bank"),
                indicator=True,
                validate="one_to_one"
            )

            # Identify transaction discrepancies
            def status(row):
                if row["_merge"] == "left_only":
                    return "Missing from Bank"

                if row["_merge"] == "right_only":
                    return "Missing from Payments"

                if (
                    row["Amount_Payment"]
                    != row["Amount_Bank"]
                ):
                    return "Amount Mismatch"

                return "Matched"

            results["Status"] = results.apply(
                status,
                axis=1
            )

            # Assign priority to discrepancies
            results["Priority"] = "None"

            results.loc[
                results["Status"].isin([
                    "Missing from Bank",
                    "Missing from Payments"
                ]),
                "Priority"
            ] = "High"

            mismatch = (
                results["Status"] == "Amount Mismatch"
            )

            difference = (
                results["Amount_Payment"]
                - results["Amount_Bank"]
            ).abs()

            results.loc[
                mismatch & (difference >= 100),
                "Priority"
            ] = "High"

            results.loc[
                mismatch
                & (difference >= 25)
                & (difference < 100),
                "Priority"
            ] = "Medium"

            results.loc[
                mismatch & (difference < 25),
                "Priority"
            ] = "Low"

            # Recommend corrective actions
            action_map = {
                "Matched": "No action required",
                "Missing from Bank":
                    "Verify bank settlement and check for processing delays",
                "Missing from Payments":
                    "Investigate unrecorded payment in payment system",
                "Amount Mismatch":
                    "Compare payment and bank amounts and investigate difference"
            }

            results["Recommended_Action"] = (
                results["Status"].map(action_map)
            )

            # AI-style discrepancy explanation engine
            # Rule-based explanations, no external AI API required
            def explain_discrepancy(row):
                transaction_status = row["Status"]

                if transaction_status == "Matched":
                    return (
                        "Transaction reconciled successfully. "
                        "The payment and bank records agree. "
                        "No further investigation is required."
                    )

                if transaction_status == "Missing from Bank":
                    return (
                        "This transaction exists in the payment "
                        "system but has no corresponding bank "
                        "record. Possible explanations include "
                        "delayed bank settlement, a failed "
                        "transfer, or an omitted bank entry. "
                        "Verify the settlement status and "
                        "review the bank statement."
                    )

                if transaction_status == "Missing from Payments":
                    return (
                        "This transaction appears in the bank "
                        "records but is absent from the payment "
                        "system. Possible explanations include "
                        "an unrecorded payment, a manual bank "
                        "transfer, or a data synchronization "
                        "issue. Investigate the transaction "
                        "source and payment system logs."
                    )

                if transaction_status == "Amount Mismatch":
                    payment_amount = row["Amount_Payment"]
                    bank_amount = row["Amount_Bank"]

                    amount_difference = abs(
                        payment_amount - bank_amount
                    )

                    if amount_difference >= 100:
                        severity = "significant"
                    elif amount_difference >= 25:
                        severity = "moderate"
                    else:
                        severity = "minor"

                    return (
                        f"The payment system records "
                        f"{payment_amount:.2f}, while the "
                        f"bank records {bank_amount:.2f}. "
                        f"This creates a {severity} "
                        f"discrepancy of "
                        f"{amount_difference:.2f}. "
                        "Possible explanations include "
                        "processing fees, partial settlements, "
                        "or incorrect transaction entries. "
                        "Compare the original payment record "
                        "with the bank settlement report."
                    )

                return "Further investigation is required."

            results["AI_Explanation"] = results.apply(
                explain_discrepancy,
                axis=1
            )

            # Identify transactions requiring review
            exceptions = results[
                results["Status"] != "Matched"
            ].copy()

            st.success("Reconciliation completed!")

            # Dashboard metrics
            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Transactions",
                len(results)
            )

            c2.metric(
                "Matched",
                int(
                    (results["Status"] == "Matched").sum()
                )
            )

            c3.metric(
                "Discrepancies",
                len(exceptions)
            )

            # Transaction analysis chart
            st.subheader("Transaction Analysis")

            st.bar_chart(
                results["Status"].value_counts()
            )

            # Review section
            st.subheader(
                "Transactions Requiring Review"
            )

            priority_order = {
                "High": 0,
                "Medium": 1,
                "Low": 2
            }

            # Priority filter and transaction search
            with st.form("priority_filter_form"):

                selected_priority = st.selectbox(
                    "Filter transactions by priority",
                    ["All", "High", "Medium", "Low"]
                )

                search_id = st.text_input(
                    "Search by Transaction ID",
                    placeholder="e.g. TX003"
                )

                st.form_submit_button("Apply Filter")

            # Apply filters
            sorted_exceptions = exceptions.copy()

            if search_id.strip():
                sorted_exceptions = sorted_exceptions[
                    sorted_exceptions[
                        "Transaction_ID"
                    ].str.contains(
                        search_id.strip(),
                        case=False,
                        regex=False,
                        na=False
                    )
                ]

            if selected_priority != "All":
                sorted_exceptions = sorted_exceptions[
                    sorted_exceptions["Priority"]
                    == selected_priority
                ]

            # Sort transactions by priority
            sorted_exceptions["Priority_Order"] = (
                sorted_exceptions["Priority"].map(
                    priority_order
                )
            )

            sorted_exceptions = (
                sorted_exceptions.sort_values(
                    "Priority_Order"
                )
            )

            # Display filtered transactions
            st.dataframe(
                sorted_exceptions.drop(
                    columns=[
                        "_merge",
                        "Priority_Order"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )

            if sorted_exceptions.empty:
                st.info(
                    "No transactions match your filters."
                )

            # Detailed discrepancy explanations
            st.subheader("Discrepancy Explanations")

            st.caption(
                "Automatically generated rule-based "
                "explanations. Possible causes are "
                "hypotheses, not confirmed findings."
            )

            if not sorted_exceptions.empty:

                for _, row in sorted_exceptions.iterrows():

                    transaction_id = row["Transaction_ID"]
                    transaction_priority = row["Priority"]

                    with st.expander(
                        f"{transaction_id} | "
                        f"{row['Status']} | "
                        f"Priority: {transaction_priority}"
                    ):

                        st.write("**Transaction ID:**", transaction_id)

                        st.write(
                            "**Status:**",
                            row["Status"]
                        )

                        st.write(
                            "**Priority:**",
                            transaction_priority
                        )

                        st.write("**Explanation:**")
                        st.write(row["AI_Explanation"])

                        st.write("**Recommended Action:**")
                        st.write(row["Recommended_Action"])

            # Generate Excel report
            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                results.drop(
                    columns=["_merge"]
                ).to_excel(
                    writer,
                    sheet_name="All Transactions",
                    index=False
                )

                exceptions.drop(
                    columns=["_merge"]
                ).to_excel(
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
                        int(
                            (
                                results["Status"]
                                == "Matched"
                            ).sum()
                        ),
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
        st.error(
            f"Unable to process files: {e}"
        )

else:
    st.session_state["show_results"] = False
    st.write("Upload both CSV files to begin.")
