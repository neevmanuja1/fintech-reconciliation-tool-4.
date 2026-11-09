
import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib

st.set_page_config(
    page_title="Fintech Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# PROFESSIONAL DASHBOARD STYLING
# --------------------------------------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    [data-testid="stMetric"] {
        background: #f5f8fc;
        border: 1px solid #e1e8f0;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }

    .dashboard-header {
        padding: 20px 0 15px 0;
    }

    .dashboard-subtitle {
        color: #64748b;
        font-size: 16px;
    }

    .section-description {
        color: #64748b;
        font-size: 14px;
    }

    .status-banner {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 12px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        border-color: #2563eb;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------

st.markdown("""
<div class="dashboard-header">
    <h1>💳 Fintech Reconciliation</h1>
    <p class="dashboard-subtitle">
        Transaction monitoring, discrepancy detection,
        and financial reconciliation intelligence.
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("💳 Reconciliation")
    st.caption("Financial Operations Platform")

    st.divider()

    st.subheader("Workspace")
    st.write("📊 Overview")
    st.write("🔎 Transaction Review")
    st.write("📁 Reports")

    st.divider()

    st.subheader("System Information")
    st.write("Engine: Rule-based reconciliation")
    st.write("Risk classification: Enabled")
    st.write("Discrepancy explanations: Enabled")

    st.divider()

    st.info(
        "Prototype environment. "
        "Upload synthetic or fictional data only."
    )


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

st.subheader("Data Sources")

st.caption(
    "Upload payment processor records and bank statements "
    "to begin reconciliation."
)

col1, col2 = st.columns(2)

with col1:
    payment_file = st.file_uploader(
        "Payment Records",
        type=["csv"],
        key="payments"
    )

with col2:
    bank_file = st.file_uploader(
        "Bank Records",
        type=["csv"],
        key="bank"
    )


# --------------------------------------------------
# RECONCILIATION ENGINE
# --------------------------------------------------

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
                st.error(
                    f"{name}: Missing transaction IDs."
                )
                st.stop()

            if data["Transaction_ID"].duplicated().any():
                st.error(
                    f"{name}: Duplicate transaction IDs."
                )
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
            type="primary",
            use_container_width=True
        ):
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

            # ------------------------------------------
            # TRANSACTION STATUS
            # ------------------------------------------

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

            # ------------------------------------------
            # RISK PRIORITY
            # ------------------------------------------

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

            # ------------------------------------------
            # RECOMMENDED ACTIONS
            # ------------------------------------------

            action_map = {
                "Matched":
                    "No action required",

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

            # ------------------------------------------
            # EXPLANATION ENGINE
            # ------------------------------------------

            def explain_discrepancy(row):

                transaction_status = row["Status"]

                if transaction_status == "Matched":
                    return (
                        "Transaction reconciled successfully. "
                        "Payment and bank records agree."
                    )

                if transaction_status == "Missing from Bank":
                    return (
                        "This payment exists in the payment "
                        "system but has no corresponding bank "
                        "record. Possible causes include delayed "
                        "settlement, failed transfers, or missing "
                        "bank entries. Verify settlement status."
                    )

                if transaction_status == "Missing from Payments":
                    return (
                        "This transaction appears in the bank "
                        "records but is absent from the payment "
                        "system. Possible causes include manual "
                        "transfers, unrecorded payments, or "
                        "synchronization issues. Investigate "
                        "the transaction source."
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
                        "Possible causes include processing "
                        "fees, partial settlements, or "
                        "incorrect transaction entries. "
                        "Review the original payment and "
                        "bank settlement records."
                    )

                return "Further investigation required."

            results["AI_Explanation"] = results.apply(
                explain_discrepancy,
                axis=1
            )

            exceptions = results[
                results["Status"] != "Matched"
            ].copy()

            # ------------------------------------------
            # DASHBOARD OVERVIEW
            # ------------------------------------------

            st.divider()

            st.markdown("""
            <div class="status-banner">
                ✓ Reconciliation completed successfully.
                Results are ready for review.
            </div>
            """, unsafe_allow_html=True)

            st.subheader("Reconciliation Overview")

            total = len(results)

            matched_count = int(
                (results["Status"] == "Matched").sum()
            )

            discrepancy_count = len(exceptions)

            match_rate = (
                (matched_count / total) * 100
                if total > 0 else 0
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Total Transactions",
                f"{total:,}"
            )

            c2.metric(
                "Matched",
                f"{matched_count:,}"
            )

            c3.metric(
                "Discrepancies",
                f"{discrepancy_count:,}"
            )

            c4.metric(
                "Match Rate",
                f"{match_rate:.1f}%"
            )

            # ------------------------------------------
            # ANALYTICS
            # ------------------------------------------

            st.divider()

            st.subheader("Transaction Analytics")

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:

                st.markdown("**Transaction Status Breakdown**")

                status_counts = (
                    results["Status"].value_counts()
                )

                st.bar_chart(status_counts)

            with chart_col2:

                st.markdown("**Risk Priority Breakdown**")

                priority_counts = (
                    exceptions["Priority"]
                    .value_counts()
                    .reindex(
                        ["High", "Medium", "Low"],
                        fill_value=0
                    )
                )

                st.bar_chart(priority_counts)

            # ------------------------------------------
            # TRANSACTION REVIEW
            # ------------------------------------------

            st.divider()

            st.subheader("Transaction Review")

            st.caption(
                "Search, filter, and investigate "
                "transactions requiring attention."
            )

            priority_order = {
                "High": 0,
                "Medium": 1,
                "Low": 2
            }

            with st.form("priority_filter_form"):

                filter_col1, filter_col2 = st.columns(2)

                with filter_col1:
                    selected_priority = st.selectbox(
                        "Risk Priority",
                        ["All", "High", "Medium", "Low"]
                    )

                with filter_col2:
                    search_id = st.text_input(
                        "Search Transaction ID",
                        placeholder="e.g. TX003"
                    )

                st.form_submit_button(
                    "Apply Filters",
                    use_container_width=True
                )

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

            st.caption(
                f"Showing {len(sorted_exceptions)} "
                f"of {len(exceptions)} discrepancies"
            )

            display_columns = [
                "Transaction_ID",
                "Amount_Payment",
                "Amount_Bank",
                "Status",
                "Priority",
                "Recommended_Action"
            ]

            st.dataframe(
                sorted_exceptions[display_columns],
                use_container_width=True,
                hide_index=True
            )

            if sorted_exceptions.empty:
                st.info(
                    "No transactions match your filters."
                )

            # ------------------------------------------
            # INVESTIGATION PANELS
            # ------------------------------------------

            st.divider()

            st.subheader("Investigation Center")

            st.caption(
                "Detailed rule-based explanations "
                "and recommended corrective actions."
            )

            for _, row in sorted_exceptions.iterrows():

                transaction_id = row["Transaction_ID"]

                with st.expander(
                    f"🔎 {transaction_id} | "
                    f"{row['Status']} | "
                    f"{row['Priority']} Priority"
                ):

                    detail1, detail2, detail3 = st.columns(3)

                    detail1.write(
                        f"**Transaction:** {transaction_id}"
                    )

                    detail2.write(
                        f"**Status:** {row['Status']}"
                    )

                    detail3.write(
                        f"**Priority:** {row['Priority']}"
                    )

                    st.markdown("#### Discrepancy Analysis")

                    st.write(row["AI_Explanation"])

                    st.markdown("#### Recommended Action")

                    st.info(row["Recommended_Action"])

            st.caption(
                "Explanations identify possible causes, "
                "not confirmed diagnoses."
            )

            # ------------------------------------------
            # EXCEL REPORT
            # ------------------------------------------

            st.divider()

            st.subheader("Export Reports")

            st.caption(
                "Download reconciliation results, "
                "discrepancies, and summary metrics."
            )

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
                        "Discrepancies",
                        "Match Rate (%)"
                    ],
                    "Value": [
                        total,
                        matched_count,
                        discrepancy_count,
                        round(match_rate, 2)
                    ]
                })

                summary.to_excel(
                    writer,
                    sheet_name="Summary",
                    index=False
                )

            st.download_button(
                "⬇ Download Reconciliation Report",
                data=output.getvalue(),
                file_name="Fintech_Reconciliation_Report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True
            )

    except Exception as e:
        st.error(
            f"Unable to process files: {e}"
        )

else:
    st.session_state["show_results"] = False

    st.info(
        "Upload both payment and bank CSV files "
        "to begin reconciliation."
    )
