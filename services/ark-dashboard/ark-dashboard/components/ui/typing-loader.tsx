interface TypingLoaderProps {
  className?: string;
  transparent?: boolean;
}

export function TypingLoader({
  className = "",
  transparent = false
}: TypingLoaderProps) {
  return (
    <div className={`flex justify-start flex-col items-start ${className}`}>
      <div className={`rounded-full p-2 ${transparent ? "" : "bg-gray-200"}`}>
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: "0.1s" }}
          ></div>
          <div
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          ></div>
        </div>
      </div>
    </div>
  );
}
