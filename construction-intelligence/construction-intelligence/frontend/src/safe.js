// Defensive accessors. AI payloads are validated server side, but the UI never trusts shape blindly.
export const arr = (x) => (Array.isArray(x) ? x : []);
export const str = (x, fallback = "") => (typeof x === "string" ? x : x == null ? fallback : String(x));
export const num = (x, fallback = 0) => (typeof x === "number" && Number.isFinite(x) ? x : fallback);

export function money(value, currency = "INR") {
  const v = num(value);
  try {
    return new Intl.NumberFormat(currency === "INR" ? "en-IN" : "en-US", {
      style: "currency", currency: /^[A-Z]{3}$/.test(currency) ? currency : "INR", maximumFractionDigits: 0,
    }).format(v);
  } catch {
    return `${currency} ${Math.round(v).toLocaleString()}`;
  }
}

export const percent = (x) => `${Math.round(num(x) * 100)}%`;
