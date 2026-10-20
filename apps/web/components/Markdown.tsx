import ReactMarkdown from "react-markdown";

// react-markdown builds React elements and does not render raw HTML by default, so model output
// cannot inject markup. Do not add rehype-raw or dangerouslySetInnerHTML here.
export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      components={{ a: ({ href, children }) => <a href={href} rel="noreferrer noopener" target="_blank">{children}</a> }}
      urlTransform={(url) => (/^https?:\/\//i.test(url) ? url : "")}
    >
      {children}
    </ReactMarkdown>
  );
}
