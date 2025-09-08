import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState, useEffect } from 'react'
import mermaid from 'mermaid'

// Initialize mermaid
if (typeof window !== 'undefined') {
  mermaid.initialize({ 
    startOnLoad: false, 
    theme: "dark",
    themeVariables: {
      primaryColor: "#3b82f6",
      primaryTextColor: "#ffffff",
      primaryBorderColor: "#1f2937",
      lineColor: "#374151",
      secondaryColor: "#1f2937",
      tertiaryColor: "#111827"
    }
  })
}

export const useMarkdownProcessor = (content: string) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children, ...props }: any) => (
          <a 
            href={href} 
            target="_blank" 
            rel="noreferrer" 
            className="text-blue-600 dark:text-blue-400 hover:underline"
            {...props}
          >
            {children}
          </a>
        ),
        h1: ({ children, ...props }: any) => (
          <h1 className="text-2xl font-bold mt-6 mb-4 first:mt-0" {...props}>
            {children}
          </h1>
        ),
        h2: ({ children, ...props }: any) => (
          <h2 className="text-xl font-bold mt-5 mb-3 first:mt-0" {...props}>
            {children}
          </h2>
        ),
        h3: ({ children, ...props }: any) => (
          <h3 className="text-lg font-bold mt-4 mb-2 first:mt-0" {...props}>
            {children}
          </h3>
        ),
        h4: ({ children, ...props }: any) => (
          <h4 className="text-base font-bold mt-3 mb-2 first:mt-0" {...props}>
            {children}
          </h4>
        ),
        h5: ({ children, ...props }: any) => (
          <h5 className="text-sm font-bold mt-3 mb-2 first:mt-0" {...props}>
            {children}
          </h5>
        ),
        h6: ({ children, ...props }: any) => (
          <h6 className="text-xs font-bold mt-3 mb-2 first:mt-0" {...props}>
            {children}
          </h6>
        ),
        p: ({ children, ...props }: any) => (
          <p className="mb-4 last:mb-0" {...props}>{children}</p>
        ),
        strong: ({ children, ...props }: any) => (
          <strong className="font-bold" {...props}>{children}</strong>
        ),
        em: ({ children, ...props }: any) => (
          <em className="italic" {...props}>{children}</em>
        ),
        code: (props: any) => {
          const { className, children } = props
          const inline = !className?.includes('language-')
          const match = /language-(\w+)/.exec(className || '')
          const isMermaid = match && match[1] === 'mermaid'
          
          if (!inline && isMermaid) {
            return <MermaidCode content={String(children).replace(/\n$/, '')} />
          }
          
          if (!inline) {
            return (
              <div className="my-4 rounded-md overflow-hidden bg-gray-900 dark:bg-gray-800">
                <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            )
          }
          
          return (
            <code 
              className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs font-mono" 
              {...props}
            >
              {children}
            </code>
          )
        },
        ul: ({ children, ...props }: any) => (
          <ul className="list-disc list-inside mb-4 pl-4 space-y-1" {...props}>
            {children}
          </ul>
        ),
        ol: ({ children, ...props }: any) => (
          <ol className="list-decimal list-inside mb-4 pl-4 space-y-1" {...props}>
            {children}
          </ol>
        ),
        li: ({ children, ...props }: any) => (
          <li className="text-sm" {...props}>{children}</li>
        ),
        table: ({ children, ...props }: any) => (
          <div className="my-4 overflow-x-auto border rounded-md">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props}>
              {children}
            </table>
          </div>
        ),
        thead: ({ children, ...props }: any) => (
          <thead className="bg-gray-50 dark:bg-gray-800" {...props}>{children}</thead>
        ),
        th: ({ children, ...props }: any) => (
          <th 
            className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider" 
            {...props}
          >
            {children}
          </th>
        ),
        td: ({ children, ...props }: any) => (
          <td 
            className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100 border-t border-gray-200 dark:border-gray-700" 
            {...props}
          >
            {children}
          </td>
        ),
        blockquote: ({ children, ...props }: any) => (
          <blockquote 
            className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-4 italic text-gray-600 dark:text-gray-400" 
            {...props}
          >
            {children}
          </blockquote>
        ),
        hr: (props: any) => (
          <hr className="my-6 border-gray-200 dark:border-gray-700" {...props} />
        )
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

const MermaidCode = ({ content }: { content: string }) => {
  const [showMermaidPreview, setShowMermaidPreview] = useState(false)

  return (
    <div className="my-4">
      <div className="rounded-md overflow-hidden bg-gray-900 dark:bg-gray-800">
        <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
          <code>{content}</code>
        </pre>
      </div>
      <div className="mt-2">
        <button
          type="button"
          className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          onClick={() => setShowMermaidPreview(true)}
        >
          View Diagram
        </button>
        {showMermaidPreview && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">Mermaid Diagram</h3>
                <button
                  onClick={() => setShowMermaidPreview(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
              <MermaidDiagram content={content} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const MermaidDiagram = ({ content }: { content: string }) => {
  const [diagram, setDiagram] = useState<string | boolean>(true)

  useEffect(() => {
    const render = async () => {
      const id = `mermaid-svg-${Math.round(Math.random() * 10000000)}`
      
      try {
        if (await mermaid.parse(content, { suppressErrors: true })) {
          const { svg } = await mermaid.render(id, content)
          setDiagram(svg)
        } else {
          setDiagram(false)
        }
      } catch {
        setDiagram(false)
      }
    }
    render()
  }, [content])

  if (diagram === true) {
    return <p className="text-center py-4">Rendering diagram...</p>
  } else if (diagram === false) {
    return <p className="text-center py-4 text-red-500">Unable to render diagram.</p>
  } else {
    return <div dangerouslySetInnerHTML={{ __html: diagram ?? "" }} />
  }
}