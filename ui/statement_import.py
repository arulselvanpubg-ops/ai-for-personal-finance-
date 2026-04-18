"""Bank statement import — saves to the shared Transaction store (used app-wide)."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import streamlit as st

from ai.categorizer import categorize_transactions_for_import
from core.db import Transaction
from core.parser import import_transactions
from utils.monitoring import log_event, log_exception

STATEMENT_FILE_TYPES = ["pdf", "csv", "xlsx"]
STATEMENT_UPLOAD_HELP = (
    "PDF / CSV / Excel. PDF must have selectable text (not a scan). "
    "Data is stored once and reused everywhere in the app. "
    "Imports use efficient bulk categorization (deduped; set IMPORT_CATEGORIZE_MODE in .env if needed)."
)


@dataclass
class StatementImportOutcome:
    success: bool
    count: int = 0
    message: str = ""


def process_uploaded_statement(uploaded_file) -> StatementImportOutcome:
    """
    Parse uploaded bank file, categorize rows, and persist as Transaction records.
    """
    temp_path: Optional[str] = None
    try:
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in (".csv", ".xlsx", ".pdf"):
            return StatementImportOutcome(
                success=False,
                message="Please upload a .pdf, .csv, or .xlsx file.",
            )

        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_path = temp_file.name

        transactions = import_transactions(temp_path)
        if not transactions:
            return StatementImportOutcome(
                success=False,
                message=(
                    "No transactions could be read. For PDFs, use a text-based e-statement "
                    "(not a photo scan). For CSV/Excel, include date and amount columns."
                ),
            )

        # Apply deduplication
        from core.deduplication import deduplicate_import_transactions
        
        # Allow user to choose deduplication strategy
        merge_strategy = getattr(uploaded_file, 'merge_strategy', 'keep_newest')
        
        deduplicated_transactions, dedup_stats = deduplicate_import_transactions(
            transactions, merge_strategy
        )
        
        descriptions = [tx.get("description") or "" for tx in deduplicated_transactions]
        categories = categorize_transactions_for_import(descriptions)
        for tx, cat in zip(deduplicated_transactions, categories):
            tx["category"] = cat

        for tx in deduplicated_transactions:
            amt = tx["amount"]
            # If the UI passed a flag to invert, we invert all positive amounts
            if getattr(uploaded_file, "invert_amounts", False) and amt > 0:
                amt = -amt
                
            Transaction.create(
                date=tx["date"],
                amount=amt,
                description=tx["description"],
                category=tx["category"],
            )

        log_event(
            "info",
            "transactions_imported",
            count=len(transactions),
            filename=uploaded_file.name,
        )
        n = len(deduplicated_transactions)
        original_count = len(transactions)
        duplicates_removed = original_count - n
        
        # Update dashboard date to match the newly imported data
        if deduplicated_transactions:
            latest_tx = max(deduplicated_transactions, key=lambda x: x["date"])
            import streamlit as st
            st.session_state["selected_year"] = latest_tx["date"].year
            st.session_state["selected_month"] = latest_tx["date"].month
        
        # Build message with deduplication info
        message_parts = []
        if merge_strategy == 'replace_all':
            message_parts.append(f"Imported {n} transaction(s) (replaced all existing data)")
        else:
            if duplicates_removed > 0:
                message_parts.append(f"Imported {n} new transaction(s)")
                message_parts.append(f"Removed {duplicates_removed} duplicate(s)")
                message_parts.append(f"Processed {original_count} total transaction(s)")
            else:
                message_parts.append(f"Imported {n} transaction(s)")
        
        message_parts.append("Dashboard, Expenses, Budget, Reports, and Chat now use this updated data.")
        
        return StatementImportOutcome(
            success=True,
            count=n,
            message=" ".join(message_parts),
        )
    except Exception as exc:
        log_exception("transaction_import_failed", exc, filename=uploaded_file.name)
        error_msg = str(exc)
        
        # Friendly hints for common errors
        if "column" in error_msg.lower():
            msg = "Could not find recognized Date or Amount columns. Ensure your file has clear headers."
        elif "password" in error_msg.lower() or "encrypted" in error_msg.lower():
            msg = "The file appears to be password protected. Please remove the password before uploading."
        elif "utf-8" in error_msg.lower() or "decode" in error_msg.lower():
            msg = "File encoding error. Try saving the CSV as 'UTF-8' and upload again."
        elif len(error_msg) < 200:
            msg = f"Import failed: {error_msg}"
        else:
            msg = (
                "Import failed (damaged file or unsupported layout). "
                "Try another export format from your bank (CSV is usually most reliable)."
            )
        return StatementImportOutcome(success=False, message=msg)
    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


def render_statement_import_ui(
    *,
    key_prefix: str,
    heading: Optional[str] = "Import bank statement",
    show_sync_hint: bool = True,
) -> None:
    """Streamlit: file uploader + import button; shows outcome messages."""
    if heading:
        st.subheader(heading)

    uploaded = st.file_uploader(
        "Statement file (PDF, CSV, or Excel)",
        type=STATEMENT_FILE_TYPES,
        help=STATEMENT_UPLOAD_HELP,
        key=f"{key_prefix}_statement_uploader",
    )
    
    invert_amounts = st.checkbox(
        "Treat all amounts as expenses (invert signs)",
        value=True,
        help="Check this if your bank exports expenses as positive numbers."
    )
    
    # Default deduplication strategy (keep newest) - automatically applied

    if show_sync_hint:
        st.caption(
            "Imports are saved to your account. **Dashboard**, **Expenses**, **Budget** "
            "(actual spend vs budgets), **Reports**, **Investments**, **Goals**, and **Chat** "
            "all read from the same transaction list."
        )

    if uploaded and st.button(
        "Import & sync everywhere",
        type="primary",
        key=f"{key_prefix}_statement_import_btn",
    ):
        uploaded.invert_amounts = invert_amounts
        uploaded.merge_strategy = "keep_newest"  # Default strategy
        with st.spinner("Analyzing and categorizing your statement... This may take a minute."):
            outcome = process_uploaded_statement(uploaded)
            
        if outcome.success:
            st.success(outcome.message)
        elif outcome.message.startswith("No transactions"):
            st.warning(outcome.message)
        else:
            st.error(outcome.message)
