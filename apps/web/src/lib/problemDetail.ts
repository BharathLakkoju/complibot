export function problemDetail(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null) {
    return fallback;
  }
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return "";
      })
      .filter(Boolean);
    if (parts.length) return parts.join("; ");
  }
  const title = (body as { title?: unknown }).title;
  if (typeof title === "string" && title.trim()) {
    return title;
  }
  return fallback;
}
