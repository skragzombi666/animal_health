import { validationError } from "../api/errors.js";

const REQUIRED_METHODS = Object.freeze([
  "request",
  "callService",
  "download",
  "notify",
]);

export function isPlainObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

export function requireName(value, path) {
  if (typeof value !== "string" || !value.trim()) {
    throw validationError(`${path} must be a non-empty string`, path);
  }
  return value.trim();
}

export function requirePayload(value, path = "payload") {
  if (value === undefined) return {};
  if (!isPlainObject(value)) {
    throw validationError(`${path} must be a plain object`, path);
  }
  return { ...value };
}

export function assertTransport(value) {
  if (!isPlainObject(value)) {
    throw validationError("transport must be a plain object", "transport");
  }
  const missing = REQUIRED_METHODS.filter(
    (method) => typeof value[method] !== "function",
  );
  if (missing.length) {
    throw validationError(
      `transport is missing required methods: ${missing.join(", ")}`,
      "transport",
      { missing },
    );
  }
  return value;
}
