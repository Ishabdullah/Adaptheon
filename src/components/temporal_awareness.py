"""
Temporal Awareness Module for Adaptheon
Handles knowledge cutoff, temporal detection, and time-sensitive query routing
"""

import re
import os
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List

# Load knowledge cutoff from environment or use default
def get_knowledge_cutoff() -> date:
    """Get the LLM's knowledge cutoff date from config"""
    cutoff_str = os.getenv('KNOWLEDGE_CUTOFF_DATE', '2023-06-30')
    try:
        year, month, day = cutoff_str.split('-')
        return date(int(year), int(month), int(day))
    except:
        # Default fallback
        return date(2023, 6, 30)

KNOWLEDGE_CUTOFF = get_knowledge_cutoff()

# Temporal keywords that indicate time-sensitive queries
TEMPORAL_KEYWORDS = [
    'today', 'now', 'current', 'currently', 'present', 'right now',
    'this year', 'this month', 'this week', 'this morning', 'this evening',
    'tonight', 'yesterday', 'tomorrow', 'last night', 'last week',
    'recent', 'recently', 'latest', 'newest', 'up to date', 'updated',
    'as of', 'in 2024', 'in 2025', 'for 2024', 'for 2025',
]

# Always-temporal domains (inherently time-sensitive)
# NOTE: These should be combined with context - not standalone
ALWAYS_TEMPORAL_DOMAINS = [
    # Finance & Markets
    'price', 'stock', 'crypto', 'cryptocurrency',
    'market', 'trading', 'shares', 'nasdaq', 'dow',
    'bitcoin', 'ethereum', 'coin',

    # Weather
    'weather', 'temperature', 'forecast', 'climate',

    # Sports
    'score', 'game', 'match', 'playing', 'won', 'lost',
    'quarterback', 'pitcher', 'coach',

    # News & Current Events
    'news', 'breaking', 'headline', 'latest news',
    'breaking news', 'top news',

    # Books & Bestsellers
    'bestseller', 'best seller', 'nyt #', 'top book',
]

# Context-dependent temporal terms (only temporal with keywords like "current", "now")
# These become temporal when combined with "who is", "what is current", etc.
CONTEXT_TEMPORAL_TERMS = [
    # Political positions (temporal when asking "who is the current...")
    'election', 'president', 'governor', 'prime minister',
    'senator', 'mayor', 'ceo', 'chairman',

    # Sports positions (temporal when asking "who is the...")
    'quarterback', 'qb', 'pitcher', 'coach', 'manager',
    'captain', 'mvp',

    # Crypto/Finance (temporal when not asking historical questions)
    'bitcoin price', 'ethereum price', 'stock price',
]

def is_after_cutoff(target_date: date) -> bool:
    """Check if a date is after the knowledge cutoff"""
    return target_date > KNOWLEDGE_CUTOFF

def get_current_date() -> date:
    """Get current date from system clock"""
    return datetime.now().date()

def extract_years_from_text(text: str) -> List[int]:
    """Extract 4-digit years from text"""
    years = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
    return [int(year) for year in years]

def extract_dates_from_text(text: str) -> List[date]:
    """
    Extract explicit dates from text (YYYY-MM-DD format)
    Returns list of date objects
    """
    dates = []
    # Pattern: YYYY-MM-DD
    date_pattern = r'\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b'
    matches = re.findall(date_pattern, text)

    for match in matches:
        try:
            year, month, day = int(match[0]), int(match[1]), int(match[2])
            dates.append(date(year, month, day))
        except:
            continue

    return dates

def resolve_relative_time(text: str) -> Optional[date]:
    """
    Resolve relative temporal phrases to concrete dates
    Returns the most relevant date or None
    """
    text_lower = text.lower()
    today = get_current_date()

    if any(word in text_lower for word in ['today', 'now', 'currently', 'right now']):
        return today

    if 'yesterday' in text_lower or 'last night' in text_lower:
        return today - timedelta(days=1)

    if 'tomorrow' in text_lower:
        return today + timedelta(days=1)

    if 'this year' in text_lower:
        return today

    if 'this month' in text_lower:
        return today

    if 'this week' in text_lower:
        return today

    if 'last week' in text_lower:
        return today - timedelta(days=7)

    return None

def contains_temporal_keywords(text: str) -> bool:
    """Check if text contains temporal keywords"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in TEMPORAL_KEYWORDS)

def contains_temporal_domain(text: str) -> bool:
    """Check if text references always-temporal domains"""
    text_lower = text.lower()
    return any(domain in text_lower for domain in ALWAYS_TEMPORAL_DOMAINS)

def contains_identity_question(text: str) -> bool:
    """
    Check if text contains identity/status questions that are inherently temporal.

    Examples:
    - "Who is the current president?"
    - "What is the stock price of Amazon?"
    - "Who is the quarterback for the Giants?"
    """
    text_lower = text.lower()

    # Identity question patterns
    identity_patterns = [
        'who is the', 'who\'s the', 'who are the',
        'what is the current', 'what\'s the current',
        'who is currently', 'who are currently',
    ]

    # Check if query contains identity pattern + context-temporal term
    has_identity_pattern = any(pattern in text_lower for pattern in identity_patterns)
    has_context_term = any(term in text_lower for term in CONTEXT_TEMPORAL_TERMS)

    return has_identity_pattern and has_context_term

def detect_temporal_intent(text: str) -> dict:
    """
    Analyze text for temporal intent and extract time information

    Returns dict with:
    - is_temporal: bool (whether query is time-sensitive)
    - has_keywords: bool (contains temporal keywords)
    - has_domain: bool (references temporal domain)
    - extracted_years: list of years mentioned
    - extracted_dates: list of explicit dates
    - resolved_date: concrete date from relative terms
    - is_after_cutoff: bool (whether query refers to post-cutoff time)
    - reason: str (explanation of temporal detection)
    """

    has_keywords = contains_temporal_keywords(text)
    has_domain = contains_temporal_domain(text)
    has_identity_question = contains_identity_question(text)
    extracted_years = extract_years_from_text(text)
    extracted_dates = extract_dates_from_text(text)
    resolved_date = resolve_relative_time(text)

    # Determine if query is time-sensitive
    is_temporal = False
    is_after_cutoff_flag = False
    reasons = []

    # Check 0: Identity/status questions (always time-sensitive)
    if has_identity_question:
        is_temporal = True
        is_after_cutoff_flag = True  # Identity questions require current data
        reasons.append("identity/status question (who is the...)")

    # Check 1: Temporal keywords
    if has_keywords:
        is_temporal = True
        is_after_cutoff_flag = True  # Keywords like "now", "today" always mean post-cutoff
        reasons.append("contains temporal keywords")

    # Check 2: Always-temporal domains (but only if no historical context)
    # If there are years mentioned AND all are before cutoff, domain doesn't make it temporal
    historical_years_only = False
    if extracted_years:
        # Check if all mentioned years are before cutoff
        historical_years_only = all(year <= KNOWLEDGE_CUTOFF.year for year in extracted_years)

    if has_domain and not historical_years_only:
        is_temporal = True
        is_after_cutoff_flag = True  # Prices, weather, scores are always current
        reasons.append("references temporal domain (price/weather/sports)")
    elif has_domain and historical_years_only:
        # Domain mentioned but with historical years - not temporal
        reasons.append(f"domain mentioned but with historical context ({extracted_years})")

    # Check 3: Explicit years after cutoff
    for year in extracted_years:
        if year > KNOWLEDGE_CUTOFF.year:
            is_temporal = True
            is_after_cutoff_flag = True
            reasons.append(f"mentions year {year} (after cutoff {KNOWLEDGE_CUTOFF.year})")

    # Check 4: Explicit dates after cutoff
    for dt in extracted_dates:
        if is_after_cutoff(dt):
            is_temporal = True
            is_after_cutoff_flag = True
            reasons.append(f"mentions date {dt} (after cutoff {KNOWLEDGE_CUTOFF})")

    # Check 5: Resolved relative date
    if resolved_date and is_after_cutoff(resolved_date):
        is_temporal = True
        is_after_cutoff_flag = True
        reasons.append(f"resolved to {resolved_date} (after cutoff {KNOWLEDGE_CUTOFF})")

    return {
        'is_temporal': is_temporal,
        'has_keywords': has_keywords,
        'has_domain': has_domain,
        'has_identity_question': has_identity_question,
        'extracted_years': extracted_years,
        'extracted_dates': extracted_dates,
        'resolved_date': resolved_date,
        'is_after_cutoff': is_after_cutoff_flag,
        'reason': '; '.join(reasons) if reasons else 'no temporal indicators detected',
        'cutoff_date': KNOWLEDGE_CUTOFF,
        'current_date': get_current_date(),
    }

def should_use_external_sources(text: str) -> bool:
    """
    Determine if query should use external sources instead of base LLM knowledge

    Returns True if:
    - Query contains temporal keywords (now, today, current, etc.)
    - Query references temporal domains (prices, weather, scores)
    - Query mentions dates/years after knowledge cutoff
    """
    temporal_info = detect_temporal_intent(text)
    return temporal_info['is_after_cutoff']

def get_temporal_system_hint() -> str:
    """
    Get system hint to prepend to LLM prompts for time-sensitive queries
    """
    return (
        f"IMPORTANT: Your training data has a knowledge cutoff of {KNOWLEDGE_CUTOFF}. "
        f"For any information about events, data, or facts after {KNOWLEDGE_CUTOFF}, "
        f"you MUST rely ONLY on the provided external sources, tools, or retrieved documents. "
        f"Do NOT make up or guess information about anything after your cutoff date. "
        f"Today's date is {get_current_date()}."
    )
