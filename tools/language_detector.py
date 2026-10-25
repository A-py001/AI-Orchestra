"""
Language Detector and Localization Utilities for AI Orchestra
Provides robust auto-detection of query language and specialized localized prompts
to ensure both local and cloud LLMs strictly adhere to the requested output language.
"""
import re
from typing import Tuple, Dict, Any, List

# Unicode ranges
PERSIAN_ARABIC_RE = re.compile(r'[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFE]')
PERSIAN_SPECIFIC_RE = re.compile(r'[\u067E\u0686\u0698\u06AF\u06CC\u06A9]') # پ, چ, ژ, گ, ی, ک
CYRILLIC_RE = re.compile(r'[\u0400-\u04FF]')
CHINESE_RE = re.compile(r'[\u4E00-\u9FFF]')

LANGUAGE_NAMES = {
    "fa": "Persian (فارسی)",
    "en": "English",
    "ar": "Arabic (العربية)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "zh": "Chinese (中文)",
    "tr": "Turkish (Türkçe)",
}

LANGUAGE_ALIASES = {
    "farsi": "fa",
    "persian": "fa",
    "فارسی": "fa",
    "fa": "fa",
    "english": "en",
    "en": "en",
    "arabic": "ar",
    "عربی": "ar",
    "ar": "ar",
    "spanish": "es",
    "es": "es",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "portuguese": "pt",
    "pt": "pt",
    "russian": "ru",
    "ru": "ru",
    "chinese": "zh",
    "zh": "zh",
    "turkish": "tr",
    "tr": "tr",
}


def detect_language(text: str) -> str:
    """
    Auto-detects language code from text using script heuristics.
    Returns ISO 639-1 code (e.g., 'fa', 'en', 'ru', 'zh').
    """
    if not text or not text.strip():
        return "en"

    cleaned = text.strip()
    total_letters = sum(1 for c in cleaned if c.isalpha())
    if total_letters == 0:
        return "en"

    persian_arabic_count = len(PERSIAN_ARABIC_RE.findall(cleaned))
    if persian_arabic_count / total_letters > 0.2:
        return "fa"

    cyrillic_count = len(CYRILLIC_RE.findall(cleaned))
    if cyrillic_count / total_letters > 0.2:
        return "ru"

    chinese_count = len(CHINESE_RE.findall(cleaned))
    if chinese_count / max(len(cleaned), 1) > 0.15:
        return "zh"

    return "en"


def normalize_language(lang_input: str) -> Tuple[str, str]:
    """
    Normalizes a language input (code or name) to (lang_code, display_name).
    Example: 'Persian' -> ('fa', 'Persian (فارسی)')
    """
    if not lang_input:
        return "en", "English"

    clean = lang_input.strip().lower()
    code = LANGUAGE_ALIASES.get(clean, clean)
    display = LANGUAGE_NAMES.get(code, code.capitalize())
    return code, display


def get_localized_profile(lang_code: str) -> Dict[str, Any]:
    """
    Returns localized section titles, strict directives, and expected output
    to prevent local models from defaulting back to English.
    """
    if lang_code == "fa":
        return {
            "lang_code": "fa",
            "lang_name": "Persian (فارسی)",
            "writer_role": "Chief Editorial Writer & Communications Maestro (Fluent in Persian / فارسی)",
            "writer_goal": (
                "Synthesize the analytical solution and verified sources into an eloquent, publication-ready, "
                "and beautifully structured executive report written ENTIRELY in fluent Persian (فارسی)."
            ),
            "writer_backstory": (
                "You are the Grand Finale and the Master Scribe of the AI Orchestra. Your core mastery is writing "
                "compelling, articulate, and natural prose in Persian (فارسی). You translate complex technical breakthroughs "
                "and deep research into flawless Persian. You NEVER write your final report in English when Persian is requested."
            ),
            "section_headers": [
                "📌 عنوان اجرایی و جامع گزارش",
                "💡 ۱. چکیده اجرایی (خلاصه مهم‌ترین نکات و پاسخ کلیدی)",
                "🔍 ۲. یافته‌های پژوهش و تحلیل شواهد (داده‌ها، آمار و مستندات)",
                "🧠 ۳. راه‌حل گام‌به‌گام و تحلیل عمیق (پاسخ تشریحی و استدلال)",
                "📋 ۴. توصیه‌ها و جمع‌بندی کاربردی (اقدامات و راهکارهای اجرایی)",
                "📚 ۵. فهرست منابع و مآخذ معتبر (شامل عنوان، نوع منبع و لینک مستقیم)",
            ],
            "mandate": (
                "دستورالعمل قطعی و غیرقابل تغییر زبان:\n"
                "- کل این گزارش باید ۱۰۰٪ به زبان فارسی روان، شیوا و استاندارد نوشته شود.\n"
                "- استفاده از تیترها یا جملات انگلیسی اکیداً ممنوع است؛ تمام تیترها باید دقیقاً به فارسی باشند.\n"
                "- تمام مفاهیم، نتیجه‌گیری‌ها و توضیحات را به فارسی ترجمه و بازنویسی کنید.\n"
                "- فقط اسامی خاص نرم‌افزاری یا کتابخانه‌ها و آدرس‌های URL دست‌نخورده باقی بمانند."
            ),
            "expected_output": (
                "یک گزارش تحلیلی کامل، رسمی و زیبا به فرمت مارک‌داون (Markdown) که منحصراً و ۱۰۰٪ به زبان فارسی نوشته شده است، "
                "همراه با تیترهای فارسی و فهرست منابع و مآخذ معتبر."
            )
        }

    # Default / English
    return {
        "lang_code": "en",
        "lang_name": "English",
        "writer_role": "Chief Editorial Writer & Communications Maestro",
        "writer_goal": (
            "Synthesize the analytical solution and verified sources into an eloquent, publication-ready, "
            "and beautifully structured executive report with clear headings, actionable insights, and complete source references."
        ),
        "writer_backstory": (
            "You are the Grand Finale and the Master Scribe of the AI Orchestra. You translate intricate technical breakthroughs "
            "and deep analytical proofs into engaging, lucid, and flawless prose. Your final report provides an Executive Summary, "
            "in-depth solution breakdown, practical takeaways, and a structured table of verified sources and links."
        ),
        "section_headers": [
            "📌 Executive Title",
            "💡 1. Executive Summary",
            "🔍 2. Key Findings & Evidence Analysis",
            "🧠 3. In-Depth Solution & Step-by-Step Breakdown",
            "📋 4. Practical Takeaways & Recommendations",
            "📚 5. Verified Sources & Bibliography (Title, Type, and URL)",
        ],
        "mandate": (
            "CRITICAL MANDATE: The ENTIRE report MUST be written strictly in English. "
            "Compose a polished, authoritative executive dossier with clear structure."
        ),
        "expected_output": (
            "A complete, beautifully formatted Markdown report ready for publication, with full source citations and actionable conclusions."
        )
    }
