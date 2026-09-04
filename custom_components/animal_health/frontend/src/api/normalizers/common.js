import { validationError } from "../errors.js";

export function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function asRecord(value, path = "value") {
  if (!isRecord(value)) {
    throw validationError(`${path} must be an object`, path);
  }
  return value;
}

export function asArray(value, path = "value") {
  if (value == null) return [];
  if (!Array.isArray(value)) {
    throw validationError(`${path} must be an array`, path);
  }
  return value;
}

export function firstDefined(source, keys, fallback = null) {
  if (!isRecord(source)) return fallback;
  for (const key of keys) {
    if (Object.hasOwn(source, key) && source[key] !== undefined) {
      return source[key];
    }
  }
  return fallback;
}

export function requiredText(value, path = "value") {
  if (value == null) {
    throw validationError(`${path} is required`, path);
  }
  const text = String(value).trim();
  if (!text) {
    throw validationError(`${path} is required`, path);
  }
  return text;
}

export function optionalText(value) {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

export function booleanValue(value, fallback = false) {
  if (value === true || value === false) return value;
  if (value === 1 || value === "1" || value === "true") return true;
  if (value === 0 || value === "0" || value === "false") return false;
  return fallback;
}

export function numberValue(value, fallback = null, path = "value") {
  if (value == null || value === "") return fallback;
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    throw validationError(`${path} must be a finite number`, path);
  }
  return parsed;
}

export function integerValue(value, fallback = null, path = "value") {
  const parsed = numberValue(value, fallback, path);
  if (parsed == null) return parsed;
  if (!Number.isInteger(parsed)) {
    throw validationError(`${path} must be an integer`, path);
  }
  return parsed;
}

export function stringList(value, path = "value") {
  const source = value == null ? [] : Array.isArray(value) ? value : [value];
  const result = [];
  const seen = new Set();
  for (const item of source) {
    if (item == null) continue;
    const text = String(item).trim();
    if (!text || seen.has(text)) continue;
    seen.add(text);
    result.push(text);
  }
  if (value != null && !Array.isArray(value) && isRecord(value)) {
    throw validationError(`${path} must contain text values`, path);
  }
  return result;
}

function leapYear(year) {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInMonth(year, month) {
  const days = [31, leapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return days[month - 1] || 0;
}

export function dateOnly(value, path = "value") {
  if (value == null || value === "") return null;
  const text = String(value).trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (!match) {
    throw validationError(`${path} must use YYYY-MM-DD`, path);
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) {
    throw validationError(`${path} is not a valid calendar date`, path);
  }
  return text;
}

export function dateTime(value, path = "value") {
  if (value == null || value === "") return null;
  const text = String(value).trim();
  if (!/[T ]\d{2}:\d{2}/.test(text) || Number.isNaN(Date.parse(text))) {
    throw validationError(`${path} must be an ISO-8601 date-time`, path);
  }
  return text;
}

export function snakeToCamel(value) {
  return String(value).replace(/_([a-z0-9])/g, (_match, character) =>
    character.toUpperCase(),
  );
}

export function camelizeObject(value) {
  if (Array.isArray(value)) return value.map((item) => camelizeObject(item));
  if (!isRecord(value)) return value;
  const result = {};
  for (const [key, item] of Object.entries(value)) {
    result[snakeToCamel(key)] = camelizeObject(item);
  }
  return result;
}

export function collectPrefixedFields(source, prefix) {
  const record = asRecord(source, "source");
  const result = {};
  for (const [key, value] of Object.entries(record)) {
    if (!key.startsWith(prefix) || value === undefined) continue;
    const target = snakeToCamel(key.slice(prefix.length));
    if (target) result[target] = camelizeObject(value);
  }
  return result;
}

export function recordOfText(value, path = "value") {
  if (value == null) return {};
  const source = asRecord(value, path);
  const result = {};
  for (const [key, item] of Object.entries(source)) {
    if (item == null || item === "") continue;
    result[String(key)] = String(item);
  }
  return result;
}

export function recordOfStringLists(value, path = "value") {
  if (value == null) return {};
  const source = asRecord(value, path);
  return Object.fromEntries(
    Object.entries(source).map(([key, item]) => [
      String(key),
      stringList(item, `${path}.${key}`),
    ]),
  );
}
