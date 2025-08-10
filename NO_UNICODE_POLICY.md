# No Unicode Policy for SNI Project

## Policy Statement
To prevent encoding issues and ensure compatibility across all Windows environments, the Strategic Narrative Intelligence (SNI) project strictly prohibits the use of Unicode characters in source code, except where functionally necessary.

## Prohibited Characters
- **Icons and decorative Unicode characters**: ✓ ✗ ✔ ✘ ★ ☆ ♦ ♣ ♠ ♥ ☑ ☐ ⚠ ⚡ 🔥 📊 📈 📉 🎯 ⭐ 💡 🚀 ⚙ 🔧 🛠 📝 📋 📍 🌟 ⚡
- **Fancy arrows**: → ← ↑ ↓ ⇒ ⇐ ⇑ ⇓ ↔ ↕ ⟵ ⟶ ⟷ ➜ ➡ ⬅ ⬆ ⬇
- **Mathematical symbols**: ≥ ≤ ≠ ± ÷ × ∞ ∅ ∆ ∑ ∏ ∈ ∉ ⊂ ⊃ ∪ ∩ ∧ ∨
- **Special punctuation**: " " ' ' – — … • ‚ „ ‹ › « » ¿ ¡ § ¶ † ‡
- **Currency symbols (except $)**: € £ ¥ ₹ ₽ ¢ ₩ ₪ ₫ ₨ ₦ ₡
- **Accented characters in code/comments**: á é í ó ú ñ ü ö ä ß à è ì ò ù ç ş ğ ı
- **Emojis and pictographs**: All emoji characters (🚫 STRICTLY PROHIBITED)

## Allowed Replacements
Instead of Unicode, use ASCII alternatives:

| Prohibited | Use Instead |
|------------|-------------|
| ✓ | [OK] |
| ✗ | [ERROR] or [FAIL] |
| → | -> |
| ← | <- |
| ≥ | >= |
| ≤ | <= |
| ≠ | != |
| • | - or * |
| " " | " |
| ' ' | ' |
| – — | - |
| … | ... |

## Exceptions
Unicode characters are permitted ONLY when functionally necessary:
1. Multi-language text processing patterns for NLP models (any language including European, Asian, African, etc. - e.g., Russian, German, French, Chinese, Japanese, Korean, Arabic, Polish, Finnish, Thai, Hindi, etc.)
2. External data containing Unicode (news articles, user input)
3. Database content (articles may contain Unicode from external sources)

## Implementation Rules
1. All Python source code files must use only ASCII characters (0x00-0x7F)
2. All comments and docstrings must use ASCII only
3. Print statements and logging must use ASCII alternatives
4. Configuration files should use ASCII when possible
5. Documentation files (.md) should prefer ASCII but may use Unicode for readability

## Validation
Run this command to check for Unicode violations:
```bash
python -c "
import glob, re
for file in glob.glob('**/*.py', recursive=True):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        non_ascii = re.findall(r'[^\x00-\x7F]', content)
        if non_ascii and 'content_processor.py' not in file:
            print(f'{file}: {set(non_ascii)}')
"
```

## Rationale
1. **Windows Compatibility**: Prevents 'charmap' codec errors on Windows systems
2. **Terminal Compatibility**: Ensures output works in all terminal environments
3. **Consistency**: Maintains uniform character encoding across the codebase
4. **Debugging**: Eliminates encoding-related debugging overhead
5. **Portability**: Ensures code works across different environments and locales

## Status
- ✅ All Python files cleaned (2025-08-02)
- ✅ Policy established
- ✅ Validation script created

This policy is effective immediately and applies to all future development.