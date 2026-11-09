
import streamlit as st
import pandas as pd
from io import BytesIO
from decimal import Decimal, InvalidOperation
import hashlib
import re

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Fintech Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# DASHBOARD STYLING
# ==================================================

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

# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:
    st.title("💳 Reconciliation")
    st.caption("Financial Operations Platform")
    st.divider()

    st.subheader("Workspace")

    page = st.radio(
        "Navigation",
        [
            "📊 Overview",
            "🔎 Transaction Review",
            "📁 Reports"
        ],
        label_visibility="collapsed",
        key="navigation"
    )

    st.divider()
    st.subheader("System Information")

    st.write("Engine: Rule-based reconciliation")
    st.write("Financial precision: Exact decimal")
    st.write("Risk classification: Enabled")
    st.write("Discrepancy explanations: Enabled")
    st.write("Resolution tracking: Enabled")

    st.divider()

    st.info(
        "Prototype environment. "
        "Upload synthetic or fictional data only."
    )

    st.warning(
        "Investigation progress is saved only "
        "during the current Streamlit session."
    )

# ==================================================
# APPLICATION HEADER
# ==================================================

st.markdown("""
<div class="dashboard-header">
    <h1>💳 Fintech Reconciliation</h1>
    <p class="dashboard-subtitle">
        Transaction monitoring, discrepancy detection,
        investigation tracking, and financial reporting.
    </p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# FILE UPLOAD
# ==================================================

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

# ==================================================
# SESSION STATE
# ==================================================

if "investigations" not in st.session_state:
    st.session_state["investigations"] = {}

if "show_results" not in st.session_state:
    st.session_state["show_results"] = False

RESOLUTION_STATUSES = [
    "Open",
    "Under Investigation",
    "Resolved"
]

def get_investigation(transaction_id):
    return st.session_state["investigations"].get(
        str(transaction_id),
        {
            "Resolution_Status": "Open",
            "Investigation_Notes": ""
        }
    )


def save_investigation(
    transaction_id,
    resolution_status,
    investigation_notes
):
    st.session_state["investigations"][
        str(transaction_id)
    ] = {
        "Resolution_Status": resolution_status,
        "Investigation_Notes": investigation_notes
    }


def add_investigation_columns(data):
    updated = data.copy()

    updated["Resolution_Status"] = (
        updated["Transaction_ID"].apply(
            lambda transaction_id: get_investigation(
                transaction_id
            )["Resolution_Status"]
        )
    )

    updated["Investigation_Notes"] = (
        updated["Transaction_ID"].apply(
            lambda transaction_id: get_investigation(
                transaction_id
            )["Investigation_Notes"]
        )
    )

    updated.loc[
        updated["Status"] == "Matched",
        "Resolution_Status"
    ] = "Not Required"

    return updated


# ==================================================
# STEP 41.1: EXACT FINANCIAL PRECISION
# ==================================================

# Store all monetary amounts internally as integer cents.
# Decimal is used to parse the original CSV strings exactly.
# This avoids binary floating-point comparison errors.

AMOUNT_PATTERN = re.compile(
    r"^[+-]?\d+(?:\.\d{1,2})?$"
)

def parse_amount_to_cents(value):
    if pd.isna(value):
        raise ValueError("Amount cannot be empty.")

    text = str(value).strip()

    if not AMOUNT_PATTERN.fullmatch(text):
        raise ValueError(
            f"Invalid amount '{text}'. "
            "Use a numeric amount with at most "
            "two decimal places."
        )

    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError(
            f"Invalid financial amount: {text}"
        )

    if not amount.is_finite():
        raise ValueError(
            "Amounts must be finite numbers."
        )

    cents = amount * Decimal("100")

    if cents != cents.to_integral_value():
        raise ValueError(
            "Amounts cannot have more than "
            "two decimal places."
        )

    return int(cents)


def format_cents(cents):
    if pd.isna(cents):
        return "N/A"

    return f"{Decimal(int(cents)) / Decimal('100'):.2f}"


def prepare_financial_data(data, name):
    required = {
        "Transaction_ID",
        "Amount"
    }

    if not required.issubset(data.columns):
        raise ValueError(
            f"{name}: CSV must contain "
            "Transaction_ID and Amount columns."
        )

    data = data.copy()

    if data["Transaction_ID"].isna().any():
        raise ValueError(
            f"{name}: Missing transaction IDs."
        )

    data["Transaction_ID"] = (
        data["Transaction_ID"].str.strip()
    )

    if data["Transaction_ID"].eq("").any():
        raise ValueError(
            f"{name}: Blank transaction IDs."
        )

    if data["Transaction_ID"].duplicated().any():
        raise ValueError(
            f"{name}: Duplicate transaction IDs."
        )

    try:
        data["Amount_Cents"] = (
            data["Amount"].apply(
                parse_amount_to_cents
            )
        )
    except ValueError as error:
        raise ValueError(
            f"{name}: {error}"
        )

    # Keep an exact Decimal representation.
    data["Amount"] = (
        data["Amount_Cents"].apply(
            lambda cents: Decimal(cents) / Decimal("100")
        )
    )

    return data


# ==================================================
# RESET RESULTS WHEN UPLOADED FILES CHANGE
# ==================================================

if payment_file is not None and bank_file is not None:

    file_signature = (
        hashlib.sha256(
            payment_file.getvalue()
        ).hexdigest(),
        hashlib.sha256(
            bank_file.getvalue()
        ).hexdigest()
    )

    if (
        st.session_state.get("file_signature")
        != file_signature
    ):
        st.session_state["file_signature"] = file_signature
        st.session_state["show_results"] = False
        st.session_state["investigations"] = {}

    try:
        # ==============================================
        # READ AND VALIDATE CSV FILES
        # ==============================================

        payments = pd.read_csv(
            payment_file,
            dtype=str,
            keep_default_na=False
        )

        bank = pd.read_csv(
            bank_file,
            dtype=str,
            keep_default_na=False
        )

        payments = prepare_financial_data(
            payments,
            "Payments"
        )

        bank = prepare_financial_data(
            bank,
            "Bank"
        )

        # ==============================================
        # RUN RECONCILIATION
        # ==============================================

        if st.button(
            "Run Reconciliation",
            type="primary",
            use_container_width=True
        ):
            st.session_state["show_results"] = True

        if st.session_state.get(
            "show_results",
            False
        ):

            # ==========================================
            # MERGE TRANSACTION RECORDS
            # ==========================================

            results = payments.merge(
                bank,
                on="Transaction_ID",
                how="outer",
                suffixes=(
                    "_Payment",
                    "_Bank"
                ),
                indicator=True,
                validate="one_to_one"
            )

            # ==========================================
            # TRANSACTION STATUS
            # ==========================================

            def status(row):

                if row["_merge"] == "left_only":
                    return "Missing from Bank"

                if row["_merge"] == "right_only":
                    return "Missing from Payments"

                if (
                    row["Amount_Cents_Payment"]
                    != row["Amount_Cents_Bank"]
                ):
                    return "Amount Mismatch"

                return "Matched"

            results["Status"] = results.apply(
                status,
                axis=1
            )

            # ==========================================
            # EXACT DISCREPANCY DIFFERENCES
            # ==========================================

            results["Difference_Cents"] = (
                results["Amount_Cents_Payment"]
                - results["Amount_Cents_Bank"]
            ).abs()

            # ==========================================
            # RISK PRIORITY
            # ==========================================

            results["Priority"] = "None"

            missing = results["Status"].isin([
                "Missing from Bank",
                "Missing from Payments"
            ])

            results.loc[
                missing,
                "Priority"
            ] = "High"

            mismatch = (
                results["Status"] == "Amount Mismatch"
            )

            difference = results["Difference_Cents"]

            # 100 euros = 10,000 cents
            results.loc[
                mismatch & (difference >= 10000),
                "Priority"
            ] = "High"

            # 25 euros = 2,500 cents
            results.loc[
                mismatch
                & (difference >= 2500)
                & (difference < 10000),
                "Priority"
            ] = "Medium"

            results.loc[
                mismatch & (difference < 2500),
                "Priority"
            ] = "Low"

            # ==========================================
            # RECOMMENDED ACTIONS
            # ==========================================

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
                results["Status"].map(
                    action_map
                )
            )

            # ==========================================
            # RULE-BASED DISCREPANCY EXPLANATIONS
            # ==========================================

            def explain_discrepancy(row):

                transaction_status = row["Status"]

                if transaction_status == "Matched":
                    return (
                        "Transaction reconciled successfully. "
                        "Payment and bank records agree. "
                        "No further investigation is required."
                    )

                if transaction_status == "Missing from Bank":
                    return (
                        "This payment exists in the payment "
                        "system but has no corresponding bank "
                        "record. Possible causes include "
                        "delayed settlement, failed transfers, "
                        "or missing bank entries. "
                        "Verify settlement status and review "
                        "the bank statement."
                    )

                if transaction_status == "Missing from Payments":
                    return (
                        "This transaction appears in the bank "
                        "records but is absent from the payment "
                        "system. Possible causes include "
                        "manual transfers, unrecorded payments, "
                        "or synchronization issues. "
                        "Investigate the transaction source "
                        "and payment system logs."
                    )

                if transaction_status == "Amount Mismatch":

                    payment_amount = format_cents(
                        row["Amount_Cents_Payment"]
                    )

                    bank_amount = format_cents(
                        row["Amount_Cents_Bank"]
                    )

                    amount_difference = int(
                        row["Difference_Cents"]
                    )

                    if amount_difference >= 10000:
                        severity = "significant"
                    elif amount_difference >= 2500:
                        severity = "moderate"
                    else:
                        severity = "minor"

                    return (
                        f"The payment system records "
                        f"{payment_amount}, while the "
                        f"bank records {bank_amount}. "
                        f"This creates a {severity} "
                        f"discrepancy of "
                        f"{format_cents(amount_difference)}. "
                        "Possible causes include processing "
                        "fees, partial settlements, or "
                        "incorrect transaction entries. "
                        "Compare the original payment "
                        "record with the bank settlement report."
                    )

                return "Further investigation is required."

            results["AI_Explanation"] = results.apply(
                explain_discrepancy,
                axis=1
            )

            # ==========================================
            # IDENTIFY DISCREPANCIES
            # ==========================================

            exceptions = results[
                results["Status"] != "Matched"
            ].copy()

            # ==========================================
            # INVESTIGATION TRACKING
            # ==========================================

            results = add_investigation_columns(
                results
            )

            exceptions = add_investigation_columns(
                exceptions
            )

            # ==========================================
            # CALCULATE METRICS
            # ==========================================

            total = len(results)

            matched_count = int(
                (
                    results["Status"] == "Matched"
                ).sum()
            )

            discrepancy_count = len(exceptions)

            match_rate = (
                matched_count / total * 100
                if total > 0
                else 0
            )

            high_priority_count = int(
                (
                    exceptions["Priority"] == "High"
                ).sum()
            )

            medium_priority_count = int(
                (
                    exceptions["Priority"] == "Medium"
                ).sum()
            )

            low_priority_count = int(
                (
                    exceptions["Priority"] == "Low"
                ).sum()
            )

            open_count = int(
                (
                    exceptions["Resolution_Status"] == "Open"
                ).sum()
            )

            investigating_count = int(
                (
                    exceptions["Resolution_Status"]
                    == "Under Investigation"
                ).sum()
            )

            resolved_count = int(
                (
                    exceptions["Resolution_Status"] == "Resolved"
                ).sum()
            )

            unresolved_count = (
                open_count + investigating_count
            )

            resolution_rate = (
                resolved_count / discrepancy_count * 100
                if discrepancy_count > 0
                else 100.0
            )

            # ==========================================
            # DISPLAY-FRIENDLY AMOUNTS
            # ==========================================

            # Keep exact integer cents for calculations.
            # Convert to display strings only for tables.

            def display_amounts(data):
                updated = data.copy()

                for source in ["Payment", "Bank"]:
                    cents_column = (
                        f"Amount_Cents_{source}"
                    )

                    amount_column = (
                        f"Amount_{source}"
                    )

                    updated[amount_column] = (
                        updated[cents_column].apply(
                            format_cents
                        )
                    )

                return updated

            # ==========================================
            # SUCCESS BANNER
            # ==========================================

            st.divider()

            st.markdown("""
            <div class="status-banner">
                ✓ Reconciliation completed successfully.
                Results are ready for review.
            </div>
            """, unsafe_allow_html=True)

            # ==========================================
            # PAGE 1: OVERVIEW
            # ==========================================

            if page == "📊 Overview":

                st.subheader(
                    "Reconciliation Overview"
                )

                st.caption(
                    "Monitor transaction matching "
                    "performance and reconciliation risk."
                )

                # --------------------------------------
                # DASHBOARD METRICS
                # --------------------------------------

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

                st.divider()

                # --------------------------------------
                # TRANSACTION ANALYTICS
                # --------------------------------------

                st.subheader(
                    "Transaction Analytics"
                )

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:

                    st.markdown(
                        "**Transaction Status Breakdown**"
                    )

                    status_counts = (
                        results["Status"].value_counts()
                    )

                    st.bar_chart(
                        status_counts
                    )

                with chart_col2:

                    st.markdown(
                        "**Risk Priority Breakdown**"
                    )

                    priority_counts = (
                        exceptions["Priority"]
                        .value_counts()
                        .reindex(
                            [
                                "High",
                                "Medium",
                                "Low"
                            ],
                            fill_value=0
                        )
                    )

                    st.bar_chart(
                        priority_counts
                    )

                # --------------------------------------
                # RISK SUMMARY
                # --------------------------------------

                st.divider()

                st.subheader(
                    "Risk Summary"
                )

                risk1, risk2, risk3 = st.columns(3)

                risk1.metric(
                    "High Priority",
                    high_priority_count
                )

                risk2.metric(
                    "Medium Priority",
                    medium_priority_count
                )

                risk3.metric(
                    "Low Priority",
                    low_priority_count
                )

                st.caption(
                    "Priority is assigned using exact "
                    "financial differences and predefined "
                    "risk thresholds."
                )

                # --------------------------------------
                # INVESTIGATION PROGRESS
                # --------------------------------------

                st.divider()

                st.subheader(
                    "Investigation Progress"
                )

                st.caption(
                    "Track the progress of detected "
                    "transaction discrepancies."
                )

                r1, r2, r3, r4 = st.columns(4)

                r1.metric(
                    "Open",
                    open_count
                )

                r2.metric(
                    "Under Investigation",
                    investigating_count
                )

                r3.metric(
                    "Resolved",
                    resolved_count
                )

                r4.metric(
                    "Resolution Rate",
                    f"{resolution_rate:.1f}%"
                )

                st.progress(
                    min(
                        max(resolution_rate / 100, 0.0),
                        1.0
                    )
                )

                if unresolved_count > 0:

                    st.warning(
                        f"{unresolved_count} discrepancies "
                        "remain unresolved."
                    )

                else:

                    st.success(
                        "No unresolved discrepancies remain."
                    )

                st.caption(
                    "Resolution status reflects analyst "
                    "updates, not automatic confirmation "
                    "that underlying records have been corrected."
                )

                # --------------------------------------
                # RECONCILIATION SUMMARY
                # --------------------------------------

                st.divider()

                st.subheader(
                    "Reconciliation Summary"
                )

                if discrepancy_count == 0:

                    st.success(
                        "All transactions matched successfully. "
                        "No discrepancies require investigation."
                    )

                else:

                    st.write(
                        f"**{discrepancy_count}** discrepancies "
                        "were detected."
                    )

                    st.write(
                        f"**{high_priority_count}** are "
                        "classified as high priority."
                    )

                    st.write(
                        f"**{resolved_count}** have been "
                        "marked as resolved."
                    )

                    st.write(
                        "Open **Transaction Review** in the "
                        "sidebar to update investigation progress."
                    )

            # ==========================================
            # PAGE 2: TRANSACTION REVIEW
            # ==========================================

            elif page == "🔎 Transaction Review":

                st.subheader(
                    "Transaction Review"
                )

                st.caption(
                    "Search, filter, investigate, and resolve "
                    "transactions requiring attention."
                )

                # --------------------------------------
                # RESOLUTION METRICS
                # --------------------------------------

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "Open",
                    open_count
                )

                m2.metric(
                    "Under Investigation",
                    investigating_count
                )

                m3.metric(
                    "Resolved",
                    resolved_count
                )

                st.divider()

                # --------------------------------------
                # FILTERS
                # --------------------------------------

                priority_order = {
                    "High": 0,
                    "Medium": 1,
                    "Low": 2
                }

                with st.form(
                    "priority_filter_form"
                ):

                    filter_col1, filter_col2 = (
                        st.columns(2)
                    )

                    with filter_col1:

                        selected_priority = st.selectbox(
                            "Risk Priority",
                            [
                                "All",
                                "High",
                                "Medium",
                                "Low"
                            ]
                        )

                    with filter_col2:

                        selected_resolution = st.selectbox(
                            "Resolution Status",
                            [
                                "All",
                                "Open",
                                "Under Investigation",
                                "Resolved"
                            ]
                        )

                    search_id = st.text_input(
                        "Search Transaction ID",
                        placeholder="e.g. TX003"
                    )

                    st.form_submit_button(
                        "Apply Filters",
                        use_container_width=True
                    )

                # --------------------------------------
                # APPLY FILTERS
                # --------------------------------------

                sorted_exceptions = exceptions.copy()

                if search_id.strip():

                    sorted_exceptions = (
                        sorted_exceptions[
                            sorted_exceptions[
                                "Transaction_ID"
                            ].str.contains(
                                search_id.strip(),
                                case=False,
                                regex=False,
                                na=False
                            )
                        ]
                    )

                if selected_priority != "All":

                    sorted_exceptions = (
                        sorted_exceptions[
                            sorted_exceptions["Priority"]
                            == selected_priority
                        ]
                    )

                if selected_resolution != "All":

                    sorted_exceptions = (
                        sorted_exceptions[
                            sorted_exceptions[
                                "Resolution_Status"
                            ] == selected_resolution
                        ]
                    )

                # --------------------------------------
                # SORT BY PRIORITY
                # --------------------------------------

                sorted_exceptions["Priority_Order"] = (
                    sorted_exceptions["Priority"].map(
                        priority_order
                    )
                )

                sorted_exceptions = (
                    sorted_exceptions.sort_values(
                        "Priority_Order",
                        kind="stable"
                    )
                )

                st.caption(
                    f"Showing {len(sorted_exceptions)} "
                    f"of {len(exceptions)} discrepancies"
                )

                # --------------------------------------
                # DISPLAY TRANSACTION TABLE
                # --------------------------------------

                display_columns = [
                    "Transaction_ID",
                    "Amount_Payment",
                    "Amount_Bank",
                    "Status",
                    "Priority",
                    "Resolution_Status",
                    "Recommended_Action"
                ]

                display_data = display_amounts(
                    sorted_exceptions
                )

                st.dataframe(
                    display_data[display_columns],
                    use_container_width=True,
                    hide_index=True
                )

                if sorted_exceptions.empty:

                    st.info(
                        "No transactions match your filters."
                    )

                # --------------------------------------
                # INVESTIGATION CENTER
                # --------------------------------------

                st.divider()

                st.subheader(
                    "Investigation Center"
                )

                st.caption(
                    "Review discrepancy explanations, "
                    "update resolution status, and save "
                    "investigation notes."
                )

                for _, row in sorted_exceptions.iterrows():

                    transaction_id = str(
                        row["Transaction_ID"]
                    )

                    current_investigation = (
                        get_investigation(
                            transaction_id
                        )
                    )

                    current_status = (
                        current_investigation[
                            "Resolution_Status"
                        ]
                    )

                    if current_status not in RESOLUTION_STATUSES:
                        current_status = "Open"

                    current_notes = (
                        current_investigation[
                            "Investigation_Notes"
                        ]
                    )

                    with st.expander(
                        f"🔎 {transaction_id} | "
                        f"{row['Status']} | "
                        f"{row['Priority']} Priority | "
                        f"{current_status}"
                    ):

                        detail1, detail2, detail3 = (
                            st.columns(3)
                        )

                        detail1.write(
                            f"**Transaction:** "
                            f"{transaction_id}"
                        )

                        detail2.write(
                            f"**Status:** "
                            f"{row['Status']}"
                        )

                        detail3.write(
                            f"**Priority:** "
                            f"{row['Priority']}"
                        )

                        st.markdown(
                            "#### Financial Details"
                        )

                        amount1, amount2, amount3 = (
                            st.columns(3)
                        )

                        amount1.write(
                            "**Payment Amount:** "
                            + format_cents(
                                row["Amount_Cents_Payment"]
                            )
                        )

                        amount2.write(
                            "**Bank Amount:** "
                            + format_cents(
                                row["Amount_Cents_Bank"]
                            )
                        )

                        amount3.write(
                            "**Difference:** "
                            + format_cents(
                                row["Difference_Cents"]
                            )
                        )

                        st.markdown(
                            "#### Discrepancy Analysis"
                        )

                        st.write(
                            row["AI_Explanation"]
                        )

                        st.markdown(
                            "#### Recommended Action"
                        )

                        st.info(
                            row["Recommended_Action"]
                        )

                        # ------------------------------
                        # INVESTIGATION TRACKING
                        # ------------------------------

                        st.markdown(
                            "#### Investigation Tracking"
                        )

                        with st.form(
                            key=f"investigation_form_{transaction_id}"
                        ):

                            new_status = st.selectbox(
                                "Resolution Status",
                                RESOLUTION_STATUSES,
                                index=RESOLUTION_STATUSES.index(
                                    current_status
                                ),
                                key=f"status_{transaction_id}"
                            )

                            new_notes = st.text_area(
                                "Investigation Notes",
                                value=current_notes,
                                placeholder=(
                                    "Describe what you investigated, "
                                    "what you found, and the next steps."
                                ),
                                height=120,
                                key=f"notes_{transaction_id}"
                            )

                            save_clicked = (
                                st.form_submit_button(
                                    "Save Investigation",
                                    use_container_width=True
                                )
                            )

                        if save_clicked:

                            save_investigation(
                                transaction_id,
                                new_status,
                                new_notes
                            )

                            st.rerun()

                st.caption(
                    "Investigation data is stored in "
                    "Streamlit session state. "
                    "It may be lost when the session ends."
                )

                st.caption(
                    "Explanations identify possible causes, "
                    "not confirmed diagnoses."
                )

            # ==========================================
            # PAGE 3: REPORTS
            # ==========================================

            elif page == "📁 Reports":

                st.subheader(
                    "Export Reports"
                )

                st.caption(
                    "Download reconciliation results, "
                    "discrepancies, investigation notes, "
                    "and summary metrics."
                )

                # --------------------------------------
                # REPORT SUMMARY
                # --------------------------------------

                r1, r2, r3, r4 = st.columns(4)

                r1.metric(
                    "Total Transactions",
                    total
                )

                r2.metric(
                    "Matched",
                    matched_count
                )

                r3.metric(
                    "Discrepancies",
                    discrepancy_count
                )

                r4.metric(
                    "Match Rate",
                    f"{match_rate:.1f}%"
                )

                st.divider()

                # --------------------------------------
                # RESOLUTION SUMMARY
                # --------------------------------------

                st.subheader(
                    "Investigation Status Summary"
                )

                s1, s2, s3 = st.columns(3)

                s1.metric(
                    "Open",
                    open_count
                )

                s2.metric(
                    "Under Investigation",
                    investigating_count
                )

                s3.metric(
                    "Resolved",
                    resolved_count
                )

                st.divider()

                st.subheader(
                    "Report Contents"
                )

                st.write(
                    "**All Transactions:** "
                    "Complete reconciliation results, "
                    "including investigation statuses."
                )

                st.write(
                    "**Discrepancies:** "
                    "Transactions requiring investigation, "
                    "with saved resolution statuses and notes."
                )

                st.write(
                    "**Summary:** "
                    "Reconciliation and resolution metrics."
                )

                # --------------------------------------
                # PREPARE EXCEL DATA
                # --------------------------------------

                def prepare_excel_data(data):

                    exported = data.copy()

                    for source in ["Payment", "Bank"]:

                        cents_column = (
                            f"Amount_Cents_{source}"
                        )

                        amount_column = (
                            f"Amount_{source}"
                        )

                        # Excel stores numeric cells using
                        # floating-point numbers. Values
                        # here are derived from exact cents.

                        exported[amount_column] = (
                            exported[cents_column].apply(
                                lambda cents: (
                                    float(
                                        Decimal(int(cents))
                                        / Decimal("100")
                                    )
                                    if pd.notna(cents)
                                    else None
                                )
                            )
                        )

                    exported["Amount_Difference"] = (
                        exported["Difference_Cents"].apply(
                            lambda cents: (
                                float(
                                    Decimal(int(cents))
                                    / Decimal("100")
                                )
                                if pd.notna(cents)
                                else None
                            )
                        )
                    )

                    exported = exported.drop(
                        columns=[
                            "_merge",
                            "Amount_Cents_Payment",
                            "Amount_Cents_Bank",
                            "Difference_Cents"
                        ],
                        errors="ignore"
                    )

                    return exported

                # --------------------------------------
                # GENERATE EXCEL REPORT
                # --------------------------------------

                output = BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine="openpyxl"
                ) as writer:

                    all_transactions_export = (
                        prepare_excel_data(results)
                    )

                    discrepancies_export = (
                        prepare_excel_data(exceptions)
                    )

                    all_transactions_export.to_excel(
                        writer,
                        sheet_name="All Transactions",
                        index=False
                    )

                    discrepancies_export.to_excel(
                        writer,
                        sheet_name="Discrepancies",
                        index=False
                    )

                    summary = pd.DataFrame({
                        "Metric": [
                            "Total Transactions",
                            "Matched",
                            "Discrepancies",
                            "Match Rate (%)",
                            "High Priority",
                            "Medium Priority",
                            "Low Priority",
                            "Open Investigations",
                            "Under Investigation",
                            "Resolved Investigations",
                            "Unresolved Investigations",
                            "Resolution Rate (%)"
                        ],
                        "Value": [
                            total,
                            matched_count,
                            discrepancy_count,
                            round(match_rate, 2),
                            high_priority_count,
                            medium_priority_count,
                            low_priority_count,
                            open_count,
                            investigating_count,
                            resolved_count,
                            unresolved_count,
                            round(resolution_rate, 2)
                        ]
                    })

                    summary.to_excel(
                        writer,
                        sheet_name="Summary",
                        index=False
                    )

                    # Apply two-decimal number formatting
                    # to financial columns in Excel.

                    for sheet_name in [
                        "All Transactions",
                        "Discrepancies"
                    ]:

                        worksheet = writer.sheets[
                            sheet_name
                        ]

                        headers = {
                            cell.value: cell.column
                            for cell in worksheet[1]
                        }

                        money_columns = [
                            "Amount_Payment",
                            "Amount_Bank",
                            "Amount_Difference"
                        ]

                        for column_name in money_columns:

                            if column_name in headers:

                                column_number = headers[
                                    column_name
                                ]

                                for row_number in range(
                                    2,
                                    worksheet.max_row + 1
                                ):

                                    worksheet.cell(
                                        row=row_number,
                                        column=column_number
                                    ).number_format = "#,##0.00"

                # --------------------------------------
                # DOWNLOAD BUTTON
                # --------------------------------------

                st.download_button(
                    "⬇ Download Reconciliation Report",
                    data=output.getvalue(),
                    file_name=(
                        "Fintech_Reconciliation_Report.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True
                )

                st.success(
                    "Your reconciliation report is "
                    "ready to download."
                )

                st.info(
                    "Tip: Download your report before "
                    "ending your session to preserve "
                    "your investigation progress."
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
