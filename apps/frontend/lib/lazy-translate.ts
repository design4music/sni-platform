/**
 * Lazy DE translation: when a DE user views content with NULL _de fields,
 * translate inline via DeepSeek and cache in DB for future requests.
 *
 * Only used in server components on detail pages (single entity per page).
 * List pages rely on backfill scripts for bulk translation.
 */

import { query } from './db';

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_API_URL = process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1';

async function translateText(text: string, style: 'headline' | 'prose' = 'prose'): Promise<string | null> {
  if (!DEEPSEEK_API_KEY || !text?.trim()) return null;

  const systemMsg = style === 'headline'
    ? 'Translate the following news headline to German. Return only the translation, nothing else.'
    : 'Translate the following text to German. Preserve paragraph structure. Return only the translation.';

  try {
    const response = await fetch(`${DEEPSEEK_API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemMsg },
          { role: 'user', content: text },
        ],
        temperature: 0.2,
        max_tokens: Math.min(text.length * 2, 4000),
      }),
    });

    if (!response.ok) return null;
    const data = await response.json();
    return data.choices?.[0]?.message?.content?.trim() || null;
  } catch {
    return null;
  }
}

interface FieldSpec {
  src: string;       // English column name, e.g. 'title'
  dest: string;      // DE column name, e.g. 'title_de'
  text: string;      // current English text to translate
  style?: 'headline' | 'prose';
}

/**
 * Check if DE translations exist for the given fields. If any are NULL,
 * translate via DeepSeek, cache in DB, and return the translated values.
 * Returns a map of src field name -> translated text.
 */
export async function ensureDE(
  table: string,
  pk: string,
  pkValue: string,
  fields: FieldSpec[]
): Promise<Record<string, string>> {
  const result: Record<string, string> = {};
  if (fields.length === 0) return result;

  // Check which _de fields are already populated
  const destCols = fields.map(f => f.dest).join(', ');
  const rows = await query<Record<string, string | null>>(
    `SELECT ${destCols} FROM ${table} WHERE ${pk} = $1`,
    [pkValue]
  );

  if (!rows[0]) return result;

  const missing: FieldSpec[] = [];
  for (const field of fields) {
    if (rows[0][field.dest]) {
      result[field.src] = rows[0][field.dest]!;
    } else if (field.text?.trim()) {
      missing.push(field);
    }
  }

  // Translate missing fields (sequential to avoid rate limits)
  for (const field of missing) {
    const translated = await translateText(field.text, field.style || 'prose');
    if (translated) {
      result[field.src] = translated;
      // Cache in DB
      await query(
        `UPDATE ${table} SET ${field.dest} = $1 WHERE ${pk} = $2`,
        [translated, pkValue]
      ).catch(() => {});
    }
  }

  return result;
}
