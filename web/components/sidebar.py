"""Sidebar: stock input, config display, and history list."""

from __future__ import annotations

import codecs
import re
import urllib.request
from datetime import date

import streamlit as st

from web.history import get_history

# ---------------------------------------------------------------------------
# Chinese stock name → 6-digit code resolver
# ---------------------------------------------------------------------------

# Simple local fallback for common stocks (avoids network round-trip)
_COMMON_STOCKS = {
    "贵州茅台": "600519", "中国平安": "601318", "招商银行": "600036",
    "宁德时代": "300750", "比亚迪": "002594", "立讯精密": "002475",
    "宏昌电子": "603002", "五粮液": "000858", "隆基绿能": "601012",
    "美的集团": "000333", "格力电器": "000651", "中国中免": "601888",
    "海天味业": "603288", "药明康德": "603259", "紫金矿业": "601899",
    "长江电力": "600900", "中国神华": "601088", "比亚迪": "002594",
    "迈瑞医疗": "300760", "海康威视": "002415", "万华化学": "600309",
    "恒瑞医药": "600276", "伊利股份": "600887", "泸州老窖": "000568",
    "山西汾酒": "600809", "片仔癀": "600436", "云南白药": "000538",
    "中芯国际": "688981", "科大讯飞": "002230", "三一重工": "600031",
}

# Regex: at least one CJK character means "Chinese name" input
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _resolve_ticker(raw: str) -> tuple[str, str | None]:
    """Return (ticker_code, warning_msg).

    - Pure 6-digit or alphanumeric → pass through.
    - Contains CJK characters → try local map, then Tencent API.
    - Unresolvable → return raw with error message.
    """
    s = raw.strip()
    if not s:
        return s, None

    # Already a valid ticker (6-digit code, or code with exchange suffix)
    if re.fullmatch(r"[A-Za-z0-9._\-\^]+", s):
        return s, None

    # Contains Chinese → resolve
    if _CJK_RE.search(s):
        # 1) Local lookup
        if s in _COMMON_STOCKS:
            code = _COMMON_STOCKS[s]
            return code, f"✅ 「{s}」→ {code}"

        # 2) Tencent Finance API search
        try:
            code = _search_tencent(s)
            if code:
                return code, f"✅ 「{s}」→ {code}"
        except Exception:
            pass

        return s, f"❌ 未找到「{s}」对应的股票代码，请直接输入6位代码（如 002475）"

    # Other weird characters
    return s, f"❌ 输入格式有误，请输入6位A股代码（如 300750）或股票中文名（如 立讯精密）"


def _decode_tencent_name(raw_name: str) -> str:
    """Decode a Tencent API name field that may contain Unicode escapes.

    The API returns names like ``\\u7acb\\u8baf\\u7cbe\\u5bc6`` (literal
    backslash-u sequences).  ``codecs.decode(..., 'unicode_escape')`` converts
    these into real CJK characters.
    """
    if not raw_name:
        return ""
    # Fast path: already real CJK characters (no backslash-u escapes)
    if _CJK_RE.search(raw_name):
        return raw_name
    try:
        return codecs.decode(raw_name, "unicode_escape")
    except (UnicodeDecodeError, UnicodeEncodeError, ValueError):
        return raw_name


def _search_tencent(name: str) -> str | None:
    """Search stock code by Chinese name via Tencent Finance API."""
    url = f"https://smartbox.gtimg.cn/s3/?q={urllib.request.quote(name)}&t=all"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    resp = urllib.request.urlopen(req, timeout=5)
    raw = resp.read().decode("gbk")
    # Response format: v_hint="sz~002475~\u7acb\u8baf\u7cbe\u5bc6~lxjm~GP-A"
    # The ~ delimiter splits fields: exchange~code~name~pinyin~type
    for line in raw.strip().split(";"):
        if "~" not in line:
            continue
        # Extract content between first pair of double quotes
        start = line.find('"')
        end = line.rfind('"')
        if start == -1 or end <= start:
            continue
        content = line[start + 1 : end]
        parts = content.split("~")
        if len(parts) < 2:
            continue
        code = parts[1] if len(parts) > 1 else ""
        # Decode Unicode-escaped name field for comparison
        decoded_name = _decode_tencent_name(parts[2]) if len(parts) > 2 else ""
        if decoded_name == name or (len(parts) > 2 and parts[2] == name):
            return code
    # Fallback: return first 6-digit code if only one result
    for line in raw.strip().split(";"):
        if "~" not in line:
            continue
        start = line.find('"')
        end = line.rfind('"')
        if start == -1 or end <= start:
            continue
        content = line[start + 1 : end]
        parts = content.split("~")
        if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 6:
            return parts[1]
    return None


def render_sidebar() -> None:
    """Render the sidebar with input controls and history."""

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:1.5rem;">
            <span style="font-size:2rem; font-weight:800; color:#ff5a1f;">Trading</span><span style="font-size:2rem; font-weight:800; color:#f5f1eb;">Agents</span><span style="font-size:2rem; font-weight:800; color:#f5f1eb;">-</span><span style="font-size:2rem; font-weight:800; color:#ff5a1f;">Astock</span>
            <div style="font-size:0.85rem; color:#888; margin-top:0.2rem;">
                A股多Agent投研系统
            </div>
            <div style="font-size:0.7rem; color:#555; margin-top:0.3rem;">
                by <a href="https://github.com/simonlin1212" style="color:#ff5a1f; text-decoration:none;">simonlin1212</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 新建分析")

    ticker_raw = st.text_input(
        "股票代码或名称",
        placeholder="例: 300750 或 立讯精密",
        key="input_ticker",
        help="输入6位A股代码（如 002475）或股票中文名（如 立讯精密）",
    )

    trade_date = st.date_input(
        "分析日期",
        value=date.today(),
        key="input_date",
    )

    # Resolve ticker (Chinese name → code)
    ticker, ticker_msg = _resolve_ticker(ticker_raw or "")
    if ticker_msg:
        if ticker_msg.startswith("✅"):
            st.success(ticker_msg)
        else:
            st.error(ticker_msg)

    tracker = st.session_state.get("tracker")
    is_busy = tracker is not None and tracker.is_running

    # Disable button if ticker is invalid (contains CJK and unresolved)
    ticker_invalid = bool(_CJK_RE.search(ticker)) if ticker else False

    if st.button(
        "开始分析" if not is_busy else "分析进行中...",
        use_container_width=True,
        disabled=is_busy or not ticker or ticker_invalid,
        type="primary",
    ):
        st.session_state["start_analysis"] = {
            "ticker": ticker,
            "trade_date": trade_date.strftime("%Y-%m-%d"),
        }
        st.session_state["viewing_history"] = None

    st.markdown("---")
    st.markdown("#### 历史记录")

    history = get_history()
    if not history:
        st.caption("暂无历史记录")
        return

    for entry in history[:20]:
        t, d = entry["ticker"], entry["date"]
        label = f"{t}  ·  {d}"
        if st.button(label, key=f"hist_{t}_{d}", use_container_width=True):
            st.session_state["viewing_history"] = entry["path"]
            st.session_state["start_analysis"] = None

    st.markdown("---")
    st.caption("⚠️ 仅供学习研究，不构成投资建议")
