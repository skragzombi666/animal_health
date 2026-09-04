import { languageKey } from "./i18n.js";

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;
const DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$/;

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function escapeAttribute(value) {
  return escapeHtml(value);
}

function dateParts(value) {
  const match = DATE_ONLY.exec(String(value ?? "").trim());
  if (!match) return null;
  const [, year, month, day] = match;
  return { year, month, day };
}

export function formatDateOnly(value, locale = "en-GB") {
  if (value === null || value === undefined || value === "") return "–";
  const parts = dateParts(value);
  if (!parts) return String(value);
  return languageKey(locale) === "de"
    ? `${parts.day}.${parts.month}.${parts.year}`
    : `${parts.day}/${parts.month}/${parts.year}`;
}

export function formatDateTime(value, locale = "en-GB", timeZone = null) {
  if (value === null || value === undefined || value === "") return "–";
  const source = String(value).trim();
  if (timeZone) {
    const parsed = new Date(source);
    if (!Number.isNaN(parsed.getTime())) {
      try {
        return new Intl.DateTimeFormat(locale, {
          dateStyle: "medium",
          timeStyle: "short",
          timeZone,
        }).format(parsed);
      } catch (_error) {
      }
    }
  }
  const match = DATE_TIME.exec(source);
  if (match) {
    const [, year, month, day, hour, minute] = match;
    return `${formatDateOnly(`${year}-${month}-${day}`, locale)} · ${hour}:${minute}`;
  }
  const parsed = new Date(source);
  if (Number.isNaN(parsed.getTime())) return source;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export function formatNumber(value, locale = "en-GB", digits = 2) {
  if (value === null || value === undefined || value === "") return "–";
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  const maximumFractionDigits = Number.isInteger(digits) && digits >= 0
    ? digits
    : 2;
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits,
  }).format(number);
}

export function formatEnum(value, translate) {
  if (value === null || value === undefined || value === "") return "–";
  const key = String(value);
  const translated = typeof translate === "function" ? translate(key) : key;
  return translated === key ? key.replaceAll("_", " ") : translated;
}

function speciesRecord(state, speciesId) {
  const items = state?.animals?.catalog?.species;
  if (!Array.isArray(items)) return null;
  return items.find((item) => String(item?.id ?? "") === String(speciesId ?? "")) || null;
}

export function speciesLabel(
  animal,
  state,
  translate,
  language = "en",
) {
  const id = String(animal?.species ?? "").trim();
  if (!id) return "–";
  const item = speciesRecord(state, id);
  if (item) {
    const german = item.nameDe ?? item.name_de;
    const english = item.nameEn ?? item.name_en;
    const selected = languageKey(language) === "de"
      ? german || english
      : english || german;
    if (selected) return String(selected);
  }
  return formatEnum(id, translate);
}

export function formatWeight(weight, locale = "en-GB") {
  if (!weight) return "–";
  const value = weight.originalValue ?? weight.valueKg;
  const unit = weight.originalUnit ?? (weight.valueKg != null ? "kg" : null);
  if (value === null || value === undefined || value === "") return "–";
  return `${formatNumber(value, locale, unit === "kg" ? 2 : 0)}${unit ? ` ${unit}` : ""}`;
}
