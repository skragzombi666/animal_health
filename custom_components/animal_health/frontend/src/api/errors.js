export const ERROR_CODES = Object.freeze({
  VALIDATION: "validation",
  NOT_FOUND: "not_found",
  CONFLICT: "conflict",
  PERMISSION: "permission",
  TRANSPORT: "transport",
  UNAVAILABLE: "unavailable",
  INTERNAL: "internal",
});

const STABLE_CODES = new Set(Object.values(ERROR_CODES));

function record(value) {
  return value !== null && typeof value === "object" ? value : {};
}

function errorMessage(value) {
  if (value instanceof Error && value.message) return value.message;
  const source = record(value);
  if (typeof source.message === "string" && source.message.trim()) {
    return source.message.trim();
  }
  if (typeof value === "string" && value.trim()) return value.trim();
  return "Animal Health operation failed";
}

function explicitCode(value) {
  const source = record(value);
  for (const candidate of [source.code, source.error_code, source.errorCode]) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim().toLowerCase();
    }
  }
  return "";
}

function numericStatus(value) {
  const source = record(value);
  for (const candidate of [source.status, source.statusCode, source.httpStatus]) {
    const parsed = Number(candidate);
    if (Number.isInteger(parsed) && parsed >= 100 && parsed <= 599) {
      return parsed;
    }
  }
  return null;
}

export function classifyErrorCode(value) {
  const code = explicitCode(value);
  if (STABLE_CODES.has(code)) return code;

  const status = numericStatus(value);
  if (status === 400 || status === 422) return ERROR_CODES.VALIDATION;
  if (status === 401 || status === 403) return ERROR_CODES.PERMISSION;
  if (status === 404) return ERROR_CODES.NOT_FOUND;
  if (status === 409) return ERROR_CODES.CONFLICT;
  if (status === 502 || status === 503 || status === 504) {
    return ERROR_CODES.UNAVAILABLE;
  }

  const haystack = `${code} ${errorMessage(value)}`.toLowerCase();
  if (
    /not[_ -]?found|no longer exists|does not exist|unknown (?:animal|task|record|resource)|missing (?:animal|task|record|resource)/.test(
      haystack,
    )
  ) {
    return ERROR_CODES.NOT_FOUND;
  }
  if (/already exists|duplicate|conflict|integrity/.test(haystack)) {
    return ERROR_CODES.CONFLICT;
  }
  if (/unauthori[sz]ed|forbidden|permission|access denied/.test(haystack)) {
    return ERROR_CODES.PERMISSION;
  }
  if (/validation|invalid|required|must not be empty|unsupported/.test(haystack)) {
    return ERROR_CODES.VALIDATION;
  }
  if (/not loaded|unavailable|not available|not supported/.test(haystack)) {
    return ERROR_CODES.UNAVAILABLE;
  }
  if (
    /connection|network|offline|timeout|timed out|failed to fetch|socket|transport/.test(
      haystack,
    )
  ) {
    return ERROR_CODES.TRANSPORT;
  }
  return ERROR_CODES.INTERNAL;
}

export class AnimalHealthError extends Error {
  constructor(
    message,
    {
      code = ERROR_CODES.INTERNAL,
      operation = null,
      details = {},
      cause = null,
    } = {},
  ) {
    super(String(message || "Animal Health operation failed"));
    this.name = "AnimalHealthError";
    this.code = STABLE_CODES.has(code) ? code : ERROR_CODES.INTERNAL;
    this.operation = operation === null ? null : String(operation);
    this.details =
      details !== null && typeof details === "object" && !Array.isArray(details)
        ? { ...details }
        : {};
    this.cause = cause;
  }
}

export function normalizeError(value, { operation = null, details = {} } = {}) {
  if (value instanceof AnimalHealthError) return value;
  const source = record(value);
  const sourceDetails =
    source.details !== null &&
    typeof source.details === "object" &&
    !Array.isArray(source.details)
      ? source.details
      : {};
  return new AnimalHealthError(errorMessage(value), {
    code: classifyErrorCode(value),
    operation,
    details: { ...sourceDetails, ...details },
    cause: value,
  });
}

export function validationError(message, path = null, details = {}) {
  return new AnimalHealthError(message, {
    code: ERROR_CODES.VALIDATION,
    operation: "validation",
    details: {
      ...(path ? { path: String(path) } : {}),
      ...details,
    },
  });
}
