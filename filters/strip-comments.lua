-- Drop HTML comments from the rendered book.
--
-- Authors keep notes in HTML comments, such as screenshot capture specs and the
-- instructor answers in the comprehensive cases. Pandoc copies raw HTML comments
-- into the website's page source, so this filter removes them. They stay
-- readable in the .qmd sources only.

-- Quarto passes its own bookkeeping through the document as comments
-- (<!-- quarto-file-metadata: ... -->, which drives book numbering), so those stay.
local function is_comment(text)
  return text:match("^%s*<!%-%-") ~= nil and text:match("%-%->%s*$") ~= nil
    and text:match("^%s*<!%-%-%s*quarto") == nil
end

function RawBlock(el)
  if el.format:match("html") and is_comment(el.text) then
    return {}
  end
end

function RawInline(el)
  if el.format:match("html") and is_comment(el.text) then
    return {}
  end
end
