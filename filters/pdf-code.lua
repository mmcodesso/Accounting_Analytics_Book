-- In the PDF, inline code (an Excel formula, a SQL fragment, a name to type) sits on the same gray as the
-- code blocks, as it does in HTML (styles/book.scss). \aacode, defined in styles/book-pdf.tex, highlights
-- it without boxing it, so a long formula can still break at the end of a line. Other formats are left alone.
if not FORMAT:match('latex') then
  return {}
end

return {
  {
    Code = function(code)
      return {pandoc.RawInline('latex', '\\aacode{'), code, pandoc.RawInline('latex', '}')}
    end,
  },
}
