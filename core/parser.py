import csv
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber

from utils.validators import sanitize_input
from utils.monitoring import log_event

# --- CSV / spreadsheet: column name hints (lowercase substrings) ---
_DATE_HINTS = (
    "date",
    "posted",
    "posting",
    "transaction",
    "trans date",
    "txn",
    "value date",
    "booking",
)
_AMOUNT_SINGLE_HINTS = ("amount", "amt")
_DEBIT_HINTS = ("debit", "withdraw", "paid out", "outflow", "dr ")
_CREDIT_HINTS = ("credit", "deposit", "paid in", "inflow", "cr ")
_DESC_HINTS = (
    "description",
    "details",
    "memo",
    "narration",
    "particulars",
    "payee",
    "merchant",
    "narrative",
)


def _norm_col(name: Any) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    s = str(name).strip().lower()
    s = s.replace("\ufeff", "").replace("\n", " ")
    return " ".join(s.split())


def _find_column(
    columns: List[str], hints: Tuple[str, ...], exclude: Optional[Tuple[str, ...]] = None
) -> Optional[str]:
    exclude = exclude or ()
    for c in columns:
        n = _norm_col(c)
        if not n or any(x in n for x in exclude):
            continue
        for h in hints:
            if h in n:
                return c
    return None


def _parse_money(val: Any) -> Optional[float]:
    """Parse currency strings (US 1,234.56 and EU 1.234,56 / 1234,56)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", "-", "--"):
        return None
    neg = "(" in s and ")" in s
    s = re.sub(r"[$€£₹₽\s]", "", s)
    s = s.replace("(", "").replace(")", "")
    s = s.strip()
    if s.startswith("-"):
        neg = True
        s = s[1:]

    # European: thousands with dot, decimal comma (e.g. 1.234,56)
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*,\d{2}", s):
        s = s.replace(".", "").replace(",", ".")
    # Single comma as decimal (1234,56)
    elif s.count(",") == 1 and s.count(".") == 0:
        left, right = s.split(",")
        if right.isdigit() and len(right) <= 2:
            s = left + "." + right
        else:
            s = s.replace(",", "")
    else:
        # US-style thousands
        s = s.replace(",", "")

    try:
        num = float(s)
        if neg and num > 0:
            num = -num
        return num
    except ValueError:
        return None


def _parse_date_cell(val: Any) -> Optional[datetime]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val
    if hasattr(val, "to_pydatetime"):
        try:
            return val.to_pydatetime()
        except Exception:
            pass
    s = str(val).strip()
    if not s:
        return None
    dt = pd.to_datetime(s, errors="coerce", dayfirst=False)
    if pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        for fmt in (
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%d.%m.%Y",
        ):
            try:
                return datetime.strptime(s.split()[0], fmt)
            except ValueError:
                continue
        return None
    t = pd.Timestamp(dt).to_pydatetime()
    return t


def _dataframe_to_transactions(df: pd.DataFrame) -> List[Dict]:
    """Map a bank-style dataframe to transaction dicts."""
    transactions: List[Dict] = []
    if df is None or df.empty:
        return transactions

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)

    date_col = _find_column(cols, _DATE_HINTS, exclude=("balance", "available"))
    debit_col = _find_column(cols, _DEBIT_HINTS)
    credit_col = _find_column(cols, _CREDIT_HINTS)
    amount_col = _find_column(cols, _AMOUNT_SINGLE_HINTS, exclude=("balance",))

    if not date_col:
        # Fallback: first column that parses as dates for most non-null rows
        best_col, best_score = None, 0
        for c in cols:
            parsed = df[c].map(_parse_date_cell)
            score = parsed.notna().sum()
            if score > best_score:
                best_score = score
                best_col = c
        if best_col and best_score >= max(1, len(df) // 4):
            date_col = best_col

    desc_col = _find_column(cols, _DESC_HINTS)

    if not date_col:
        return transactions

    for _, row in df.iterrows():
        date = _parse_date_cell(row.get(date_col))
        if not date:
            continue

        amount: Optional[float] = None
        if amount_col:
            amount = _parse_money(row.get(amount_col))
        if amount is None and (debit_col or credit_col):
            debit = _parse_money(row.get(debit_col)) if debit_col else None
            credit = _parse_money(row.get(credit_col)) if credit_col else None
            if debit and debit != 0:
                amount = -abs(debit)
            elif credit and credit != 0:
                amount = abs(credit)

        if amount is None or amount == 0:
            continue

        desc = ""
        if desc_col:
            desc = sanitize_input(str(row.get(desc_col) or ""), max_length=200)
        if not desc:
            parts = [
                str(row[c]).strip()
                for c in cols
                if c not in (date_col, amount_col, debit_col, credit_col)
                and str(row.get(c, "")).strip()
                and str(row.get(c, "")).lower() not in ("nan", "none")
            ]
            desc = sanitize_input(" ".join(parts[:5]), max_length=200)

        transactions.append(
            {
                "date": date,
                "amount": amount,
                "description": desc or "Transaction",
                "category": "Uncategorized",
            }
        )

    log_event("info", "dataframe_to_transactions_complete", rows=len(df), transactions=len(transactions))
    return transactions


def _load_csv_to_dataframe(file_path: str) -> pd.DataFrame:
    last_err: Optional[Exception] = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        for sep in (None, ",", ";", "\t"):
            try:
                kwargs: Dict[str, Any] = {
                    "encoding": encoding,
                    "engine": "python",
                    "on_bad_lines": "skip",
                }
                if sep is None:
                    kwargs["sep"] = None
                else:
                    kwargs["sep"] = sep
                return pd.read_csv(file_path, **kwargs)
            except UnicodeDecodeError as e:
                last_err = e
                break
            except Exception as e:
                last_err = e
                continue
    try:
        return pd.read_csv(file_path, encoding="latin-1", sep=None, engine="python")
    except Exception as e:
        if last_err:
            raise e from last_err
        raise


def parse_csv(file_path: str) -> List[Dict]:
    """Parse CSV file and return list of transaction dicts."""
    try:
        df = _load_csv_to_dataframe(file_path)
        log_event("info", "csv_loaded_with_pandas", file=os.path.basename(file_path), columns=list(df.columns))
    except Exception as e:
        log_event("warning", "csv_pandas_failed_using_fallback", file=os.path.basename(file_path), error=str(e))
        # Legacy fallback: DictReader path for minimal one-line CSVs
        transactions: List[Dict] = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                normalized = {(k or "").lower(): (v or "").strip() for k, v in row.items()}
                date_str = normalized.get("date") or normalized.get("transaction date")
                amount_str = (
                    normalized.get("amount")
                    or normalized.get("debit")
                    or normalized.get("credit")
                )
                description = (
                    normalized.get("description")
                    or normalized.get("memo")
                    or normalized.get("details")
                )
                if date_str and amount_str:
                    try:
                        date = None
                        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d %H:%M:%S"):
                            try:
                                date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        if date:
                            amount = float(
                                amount_str.replace("$", "").replace("₹", "").replace(",", "").replace("€", "")
                            )
                            transactions.append(
                                {
                                    "date": date,
                                    "amount": amount,
                                    "description": sanitize_input(description or "", max_length=200),
                                    "category": "Uncategorized",
                                }
                            )
                    except (ValueError, AttributeError):
                        continue
        return transactions

    return _dataframe_to_transactions(df)


def parse_xlsx(file_path: str) -> List[Dict]:
    """Parse Excel export (common bank format)."""
    df = pd.read_excel(file_path, engine="openpyxl")
    return _dataframe_to_transactions(df)


# --- PDF: patterns for lines without strict column layout ---
_RE_DATE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b"
)
# Amount at end of line: US/EU styles, optional DR/CR
_RE_AMOUNT_END = re.compile(
    r"(?P<amt>-?\(?[\d\.,]+\s*(?:DR|CR)?\)?|[\d\.,]+\s*(?:DR|CR))\s*$",
    re.IGNORECASE,
)

_SKIP_PDF_LINE = re.compile(
    r"opening\s+balance|closing\s+balance|brought\s+forward|carried\s+forward|"
    r"page\s+\d|statement\s+(period|date|summary)|account\s+(number|no\.?)|"
    r"^\s*total\b|balance\s+(b\/f|c\/f)|available\s+balance|"
    r"^\s*date\s+description\s+amount",
    re.IGNORECASE,
)


def _parse_date_token(tok: str) -> Optional[datetime]:
    tok = tok.strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(tok, fmt)
        except ValueError:
            continue
    # 18 Jan 2026
    for fmt in ("%d %b %Y", "%d %B %Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(tok, fmt)
        except ValueError:
            continue
    return None


def _parse_amount_token(tok: str) -> Optional[float]:
    t = tok.strip()
    t = re.sub(r"\s*(DR|CR)\s*$", "", t, flags=re.I)
    return _parse_money(t)


def _looks_like_table_header_row(parts: List[str]) -> bool:
    if len(parts) < 2 or len(parts) > 8:
        return False
    first = parts[0].lower().strip(" *#")
    header_starts = (
        "date",
        "trans",
        "posting",
        "value",
        "txn",
        "transaction",
    )
    if not any(first.startswith(h) for h in header_starts):
        return False
    joined = " ".join(p.lower() for p in parts)
    return bool(
        re.search(
            r"\b(amount|debit|credit|withdraw|deposit|particulars|description|details|balance)\b",
            joined,
        )
    )


def _row_cells_to_transaction(cells: List[Any]) -> Optional[Dict]:
    if not cells:
        return None
    parts = [str(c).strip() if c is not None else "" for c in cells]
    parts = [p for p in parts if p]
    if len(parts) < 2:
        return None
    if _looks_like_table_header_row(parts):
        return None

    date_val: Optional[datetime] = None
    date_idx = -1
    for i, p in enumerate(parts):
        d = _parse_date_cell(p)
        if d:
            date_val = d
            date_idx = i
            break
    if not date_val:
        return None

    amount_val: Optional[float] = None
    amount_idx = -1
    for j in range(len(parts) - 1, -1, -1):
        if j == date_idx:
            continue
        amt = _parse_money(parts[j])
        if amt is not None and amt != 0:
            amount_val = amt
            amount_idx = j
            break
    if amount_val is None or amount_val == 0:
        return None

    desc_bits: List[str] = []
    for k, p in enumerate(parts):
        if k in (date_idx, amount_idx):
            continue
        desc_bits.append(p)
    desc = sanitize_input(" ".join(desc_bits), max_length=200)
    return {
        "date": date_val,
        "amount": amount_val,
        "description": desc or "Transaction",
        "category": "Uncategorized",
    }


def _candidate_amount_strings_from_line(line: str) -> List[str]:
    """Find monetary tokens (rightmost often = transaction amount)."""
    candidates: List[str] = []
    for m in re.finditer(
        r"-?\(?\$?[\d][\d\.,]*[.,]?\d{0,2}\)?|\$?[\d]{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?",
        line,
    ):
        t = m.group(0).strip()
        if len(t) >= 1 and _parse_money(t) is not None:
            candidates.append(t)
    return candidates


def _parse_pdf_text_line(line: str) -> Optional[Dict]:
    line = line.strip()
    if len(line) < 5:
        return None
    if _SKIP_PDF_LINE.search(line):
        return None

    m_date = _RE_DATE.search(line)
    if not m_date:
        parts = line.split()
        if len(parts) >= 3:
            date2 = _parse_date_token(parts[0])
            if date2:
                amt2 = _parse_amount_token(parts[-1])
                if amt2 and amt2 != 0:
                    desc2 = " ".join(parts[1:-1])
                    if len(desc2) > 1:
                        return {
                            "date": date2,
                            "amount": amt2,
                            "description": sanitize_input(desc2, max_length=200),
                            "category": "Uncategorized",
                        }
        return None

    m_amt = _RE_AMOUNT_END.search(line)
    amount_str = m_amt.group("amt").strip() if m_amt else None
    if not amount_str:
        cands = _candidate_amount_strings_from_line(line)
        if cands:
            amount_str = cands[-1]

    if not amount_str:
        return None

    date_str = m_date.group(1)
    date = _parse_date_cell(date_str)
    amount = _parse_amount_token(amount_str)
    if not date or amount is None or amount == 0:
        return None

    desc_start = m_date.end()
    if m_amt:
        desc_end = m_amt.start()
    else:
        last_amt_pos = line.rfind(amount_str)
        desc_end = last_amt_pos if last_amt_pos >= 0 else len(line)

    description = line[desc_start:desc_end].strip()
    description = re.sub(r"\s+", " ", description)
    if len(description) < 2:
        parts = line.split()
        if len(parts) >= 3:
            description = " ".join(parts[1:-1])
    return {
        "date": date,
        "amount": amount,
        "description": sanitize_input(description, max_length=200) or "Transaction",
        "category": "Uncategorized",
    }


def _lines_from_word_boxes(page: pdfplumber.page.Page) -> List[str]:
    """Rebuild reading order when extract_text() scrambles columns."""
    try:
        words = page.extract_words(
            use_text_flow=False,
            keep_blank_chars=False,
            x_tolerance=3,
            y_tolerance=3,
        )
    except Exception:
        return []
    if not words:
        return []
    rows: Dict[float, List[dict]] = {}
    for w in words:
        top = round(float(w["top"]) / 2.5) * 2.5
        rows.setdefault(top, []).append(w)
    lines: List[str] = []
    for top in sorted(rows.keys()):
        row_words = sorted(rows[top], key=lambda z: float(z["x0"]))
        line = " ".join(t.get("text", "") for t in row_words)
        if line.strip():
            lines.append(line.strip())
    return lines


def _extract_tables_multi_strategy(page: Any) -> List[List]:
    """Try several table detectors (ruled grids vs borderless)."""
    all_tables: List[List] = []
    strategies: Tuple[Optional[dict], ...] = (
        None,
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
        {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 4,
            "intersection_tolerance": 4,
            "text_x_tolerance": 2,
            "text_y_tolerance": 2,
        },
    )
    for settings in strategies:
        try:
            if settings:
                tables = page.extract_tables(table_settings=settings) or []
            else:
                tables = page.extract_tables() or []
        except Exception:
            continue
        for t in tables:
            if t:
                all_tables.append(t)
    return all_tables


def parse_pdf(file_path: str) -> List[Dict]:
    """Parse bank statement PDFs: tables, raw text, and word-box lines."""
    log_event("info", "pdf_parsing_start", file=os.path.basename(file_path))
    transactions: List[Dict] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            for table in _extract_tables_multi_strategy(page):
                for row in table:
                    if not row:
                        continue
                    tx = _row_cells_to_transaction(list(row))
                    if tx:
                        transactions.append(tx)

            text_lines: List[str] = []
            text = page.extract_text()
            if text:
                text_lines.extend(text.split("\n"))
            text_lines.extend(_lines_from_word_boxes(page))

            for line in text_lines:
                tx = _parse_pdf_text_line(line)
                if tx:
                    transactions.append(tx)

    seen = set()
    unique: List[Dict] = []
    for tx in transactions:
        key = (tx["date"].date(), round(tx["amount"], 2), tx["description"][:80])
        if key in seen:
            continue
        seen.add(key)
        unique.append(tx)
    return unique


def import_transactions(file_path: str) -> List[Dict]:
    """Import transactions from file (CSV, Excel, or PDF)."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return parse_csv(file_path)
    if ext == ".xlsx":
        return parse_xlsx(file_path)
    if ext == ".pdf":
        return parse_pdf(file_path)
    raise ValueError("Unsupported file format. Use CSV, Excel (.xlsx), or PDF.")
