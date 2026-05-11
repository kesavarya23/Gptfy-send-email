"""
Fetch Account + related Opportunities from a live Salesforce org (OAuth session).
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_ACCOUNT_SOQL_FIELDS = (
    "Id, Name, Industry, Type, BillingCity, BillingState, BillingCountry, "
    "AnnualRevenue, Phone, Website, Owner.Name, Description"
)

_OPP_SOQL_FIELDS = (
    "Name, StageName, Amount, CloseDate, NextStep, Probability, "
    "IsClosed, LastModifiedDate"
)


def _escape_soql_string(s: str) -> str:
    """SOQL string literal: escape single quotes by doubling them."""
    return (s or "").replace("'", "''")


def looks_like_salesforce_id(s: str) -> bool:
    t = (s or "").strip()
    if len(t) not in (15, 18):
        return False
    return bool(re.match(r"^[a-zA-Z0-9]+$", t))


def find_accounts_by_name(sf, name: str, limit: int = 25) -> List[Dict[str, Any]]:
    esc = _escape_soql_string(name.strip())
    q = (
        f"SELECT Id, Name, BillingCity, BillingState FROM Account "
        f"WHERE Name = '{esc}' ORDER BY LastModifiedDate DESC LIMIT {limit}"
    )
    res = sf.query(q)
    return res.get("records") or []


def fetch_account_record(sf, account_id: str) -> Optional[Dict[str, Any]]:
    q = f"SELECT {_ACCOUNT_SOQL_FIELDS} FROM Account WHERE Id = '{_escape_soql_string(account_id)}' LIMIT 1"
    res = sf.query(q)
    recs = res.get("records") or []
    return recs[0] if recs else None


def fetch_opportunities_for_account(sf, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch ONLY open opportunities (IsClosed = false) for the account.

    Closed-Won / Closed-Lost opportunities are intentionally excluded —
    we only want to send outreach about deals that are still in pipeline.
    Ordered by most recent CloseDate, then largest Amount.
    """
    aid = _escape_soql_string(account_id)
    q_open = (
        f"SELECT {_OPP_SOQL_FIELDS} FROM Opportunity "
        f"WHERE AccountId = '{aid}' AND IsClosed = false "
        f"ORDER BY CloseDate ASC NULLS LAST, Amount DESC NULLS LAST "
        f"LIMIT {limit}"
    )
    res = sf.query(q_open)
    return list(res.get("records") or [])


def _fmt_money(v: Any) -> str:
    if v is None:
        return ""
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def structure_opportunity(o: Dict[str, Any], account_name: str = "") -> Dict[str, Any]:
    """
    Project a raw SOQL Opportunity record into the slim shape used downstream
    (email composer + AI writer). Always includes a ``brief_text`` field that
    describes this single opportunity on its own — that's what we feed into
    the AI as ``opportunity_text`` when sending one-email-per-opportunity, so
    each email focuses on exactly one real deal instead of the whole list.
    """
    name = (o.get("Name") or "Opportunity").strip()
    stage = (o.get("StageName") or "").strip()
    amount_raw = o.get("Amount")
    amount_str = _fmt_money(amount_raw)
    close_date = o.get("CloseDate") or ""
    next_step = (o.get("NextStep") or "").strip()
    probability = o.get("Probability")

    parts = [name]
    if stage:
        parts.append(f"Stage: {stage}")
    if amount_str:
        parts.append(f"Amount: ${amount_str}")
    if close_date:
        parts.append(f"Close date: {close_date}")
    if probability is not None:
        try:
            parts.append(f"Probability: {int(float(probability))}%")
        except (TypeError, ValueError):
            pass
    brief_lines = [" — ".join(parts)]
    if account_name:
        brief_lines.append(f"Account: {account_name}")
    if next_step:
        brief_lines.append(f"Next step: {next_step[:500]}")
    brief_text = "\n".join(brief_lines).strip()

    return {
        "name": name,
        "account_name": account_name,
        "stage": stage,
        "amount": amount_raw,
        "amount_str": amount_str,
        "close_date": close_date,
        "probability": probability,
        "next_step": next_step,
        "brief_text": brief_text,
    }


def format_account_and_opportunities(
    account: Dict[str, Any],
    opps: List[Dict[str, Any]],
) -> Tuple[str, str]:
    """
    Returns (account_name, opportunity_brief_text) for email context fields.
    """
    name = (account.get("Name") or "").strip() or "Account"
    lines: List[str] = []

    ind = account.get("Industry")
    if ind:
        lines.append(f"Industry: {ind}")
    atype = account.get("Type")
    if atype:
        lines.append(f"Type: {atype}")
    city = account.get("BillingCity")
    state = account.get("BillingState")
    country = account.get("BillingCountry")
    loc = ", ".join([x for x in [city, state, country] if x])
    if loc:
        lines.append(f"Location: {loc}")
    rev = account.get("AnnualRevenue")
    if rev is not None:
        lines.append(f"Annual revenue: {_fmt_money(rev)}")
    phone = account.get("Phone")
    if phone:
        lines.append(f"Phone: {phone}")
    site = account.get("Website")
    if site:
        lines.append(f"Website: {site}")
    owner = account.get("Owner")
    if isinstance(owner, dict) and owner.get("Name"):
        lines.append(f"Account owner: {owner['Name']}")
    desc = (account.get("Description") or "").strip()
    if desc:
        lines.append("")
        lines.append("Account notes:")
        lines.append(desc[:8000])

    open_opps = [o for o in opps if not o.get("IsClosed")]
    if open_opps:
        lines.append("")
        lines.append(f"Open opportunities (from org) — {len(open_opps)}:")
        for o in open_opps:
            amt = _fmt_money(o.get("Amount"))
            parts = [
                o.get("Name") or "Opportunity",
                o.get("StageName") or "",
                f"${amt}" if amt else "",
                f"close {o.get('CloseDate')}" if o.get("CloseDate") else "",
            ]
            head = " — ".join(p for p in parts if p)
            lines.append(f"- {head}")
            ns = (o.get("NextStep") or "").strip()
            if ns:
                lines.append(f"  Next step: {ns[:500]}")
    else:
        lines.append("")
        lines.append("(No open opportunities for this account in Salesforce.)")

    return name, "\n".join(lines).strip()


def _structured_open_opportunities(
    opps: List[Dict[str, Any]], account_name: str
) -> List[Dict[str, Any]]:
    """Return only OPEN opps as slim dicts the email pipeline can iterate over."""
    return [
        structure_opportunity(o, account_name=account_name)
        for o in opps
        if not o.get("IsClosed")
    ]


def resolve_account_bundle(sf, lookup: str) -> Dict[str, Any]:
    """
    lookup: 15/18-char Account Id, or exact Account Name (single match).
    Returns dict with keys: ok, account_name, opportunity_text, opportunities,
    matches?, error?

    ``opportunities`` is a list of slim per-opp dicts (only open opps), so the
    email sender can iterate one-email-per-opportunity instead of cramming the
    whole list into a single text blob.
    """
    raw = (lookup or "").strip()
    if not raw:
        return {"ok": False, "error": "Enter an Account name or Account Id."}

    if looks_like_salesforce_id(raw):
        acc = fetch_account_record(sf, raw)
        if not acc:
            return {"ok": False, "error": "No Account found for that Id."}
        opps = fetch_opportunities_for_account(sf, acc["Id"])
        aname, obrief = format_account_and_opportunities(acc, opps)
        return {
            "ok": True,
            "account_id": acc.get("Id"),
            "account_name": aname,
            "opportunity_text": obrief,
            "opportunities": _structured_open_opportunities(opps, aname),
        }

    matches = find_accounts_by_name(sf, raw)
    if not matches:
        return {
            "ok": False,
            "error": f"No Account named “{raw}” found. Try the 15- or 18-character Account Id from the URL.",
        }
    if len(matches) > 1:
        slim = [
            {
                "id": m.get("Id"),
                "name": m.get("Name"),
                "billing_city": m.get("BillingCity"),
                "billing_state": m.get("BillingState"),
            }
            for m in matches
        ]
        return {
            "ok": False,
            "needs_pick": True,
            "matches": slim,
            "error": "Multiple accounts with that name. Pick one by Id or refine the name.",
        }

    acc_full = fetch_account_record(sf, matches[0]["Id"])
    if not acc_full:
        return {"ok": False, "error": "Could not load Account details."}
    opps = fetch_opportunities_for_account(sf, acc_full["Id"])
    aname, obrief = format_account_and_opportunities(acc_full, opps)
    return {
        "ok": True,
        "account_id": acc_full.get("Id"),
        "account_name": aname,
        "opportunity_text": obrief,
        "opportunities": _structured_open_opportunities(opps, aname),
    }
