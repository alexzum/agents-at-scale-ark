export type ResponseForView = {
  body: unknown | string;                        // extracted text you show today
  headers?: Record<string, string | undefined>; // optional
  rawJson?: unknown | string;                   // original JSON envelope
};

export type ViewMode = "text" | "markdown" | "json";

export function isJsonContentType(headers?: Record<string, string | undefined>) {
  if (!headers) return false;
  const ct = (headers["content-type"] || headers["Content-Type"] || "").toLowerCase();
  return ct.includes("application/json") || ct.includes("application/ld+json");
}

export function isParsableJson(s: string) {
  try { JSON.parse(s); return true; } catch { return false; }
}

export function responseIsJson(res: ResponseForView) {
  if (res.rawJson !== undefined) return true;
  const headerJson = isJsonContentType(res.headers);
  const bodyIsObject = typeof res.body === "object" && res.body !== null;
  const bodyIsJsonString = typeof res.body === "string" && isParsableJson(res.body);
  return headerJson || bodyIsObject || bodyIsJsonString;
}

/** Default to JSON when JSON is detected (your ask). */
export function pickDefaultView(res: ResponseForView, fallback: ViewMode = "text"): ViewMode {
  return responseIsJson(res) ? "json" : fallback;
}
