const BASE = import.meta.env?.VITE_API_BASE || "";

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new ApiError("network", "The server cannot be reached. Check that the backend is running and try again.", 0);
  }
  let body = null;
  try {
    body = await res.json();
  } catch {
    throw new ApiError("bad_response", "The server sent a response the app could not read.", res.status);
  }
  if (!res.ok || body?.status !== "success") {
    const e = body?.error;
    throw new ApiError(e?.code || "error", e?.message || "The request failed.", res.status);
  }
  return body;
}

export const getJson = (path) => request(path);

export const postJson = (path, payload) =>
  request(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });

export function postForm(path, fields, files = []) {
  const fd = new FormData();
  Object.entries(fields).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") fd.append(k, v);
  });
  files.forEach((f) => fd.append("images", f));
  return request(path, { method: "POST", body: fd });
}

export const del = (path) => request(path, { method: "DELETE" });
