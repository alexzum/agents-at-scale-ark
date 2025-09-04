"use client";

import { useEffect, useMemo, useState } from "react";
import JsonDisplay from "@/components/JsonDisplay";
import { ResponseForView, responseIsJson, ViewMode, pickDefaultView } from "@/lib/utils/jsons";

type Props = { response: ResponseForView; initialMode?: ViewMode };

function ViewToggle({
  mode, setMode, showJson,
}:{ mode: ViewMode; setMode:(m: ViewMode)=>void; showJson:boolean }) {
  return (
    <div className="inline-flex gap-2 mb-2">
      <button className={`px-2 py-1 rounded ${mode === "text" ? "bg-gray-800 text-white" : "bg-gray-200"}`} onClick={() => setMode("text")}>Text</button>
      <button className={`px-2 py-1 rounded ${mode === "markdown" ? "bg-gray-800 text-white" : "bg-gray-200"}`} onClick={() => setMode("markdown")}>Markdown</button>
      {showJson && (
        <button className={`px-2 py-1 rounded ${mode === "json" ? "bg-gray-800 text-white" : "bg-gray-200"}`} onClick={() => setMode("json")}>JSON</button>
      )}
    </div>
  );
}

export default function ResponseViewer({ response, initialMode }: Props) {
  const showJson = responseIsJson(response);
  const [mode, setMode] = useState<ViewMode>(initialMode ?? pickDefaultView(response, "text"));

  useEffect(() => {
    setMode(initialMode ?? pickDefaultView(response, "text"));
  }, [response, initialMode]);

  const textBody = useMemo(() => {
    if (typeof response.body === "string") return response.body;
    try { return JSON.stringify(response.body, null, 2); } catch { return String(response.body); }
  }, [response.body]);

  const jsonValue = response.rawJson ?? response.body;

  return (
    <div className="flex flex-col">
      <ViewToggle mode={mode} setMode={setMode} showJson={showJson} />
      {mode === "json" && showJson && <JsonDisplay value={jsonValue} />}
      {mode === "markdown" && <pre className="whitespace-pre-wrap break-words">{textBody}</pre>}
      {mode === "text" && <pre className="whitespace-pre-wrap break-words">{textBody}</pre>}
    </div>
  );
}
