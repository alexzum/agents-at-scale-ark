import { useMemo, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

type JsonDisplayProps = {
  value: unknown | string;
  maxPreviewBytes?: number;
  className?: string;
  filename?: string;
};

function tryParse(text: string) {
  try { return JSON.parse(text); } catch { return undefined; }
}

function safePretty(value: unknown, space = 2) {
  try {
    if (typeof value === "string") {
      const parsed = tryParse(value);
      return parsed ? JSON.stringify(parsed, null, space) : value;
    }
    return JSON.stringify(value, null, space);
  } catch {
    return String(value);
  }
}

export default function JsonDisplay({
  value,
  maxPreviewBytes = 300_000,
  className,
  filename = "response.json",
}: JsonDisplayProps) {
  const [expanded, setExpanded] = useState(false);
  const pretty = useMemo(() => safePretty(value, 2), [value]);

  const tooBig = pretty.length > maxPreviewBytes;
  const shown = expanded || !tooBig ? pretty : pretty.slice(0, maxPreviewBytes) + "\n… (truncated)";

  const copy = async () => navigator.clipboard.writeText(pretty);
  const download = () => {
    const blob = new Blob([pretty], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const parsed = typeof value === "string" ? tryParse(value) : value;

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-2">
        <button className="px-2 py-1 rounded bg-gray-200" onClick={copy}>Copy</button>
        <button className="px-2 py-1 rounded bg-gray-200" onClick={download}>Download</button>
        {tooBig && (
          <button className="px-2 py-1 rounded bg-gray-200" onClick={() => setExpanded(v => !v)}>
            {expanded ? "Show less" : "Load full"}
          </button>
        )}
      </div>
      <div className="border rounded overflow-auto max-h-[480px]">
        <SyntaxHighlighter language="json">{shown}</SyntaxHighlighter>
      </div>
      {!parsed && (
        <div className="mt-2 text-amber-700 text-sm">Couldn’t parse JSON. Showing raw text.</div>
      )}
    </div>
  );
}
