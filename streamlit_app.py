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

            if page == "📁 Reports":
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
