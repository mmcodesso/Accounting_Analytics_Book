-- Keep the EPUB's markup valid XHTML 5.
--
-- Quarto copies a figure's fig-alt onto the <div class="quarto-float"> that wraps the figure, as an alt
-- attribute, in addition to the <img> that already carries the alt text. HTML5 allows alt only on img (and area and
-- input), so EPUBCheck reports RSC-005 "attribute "alt" not allowed here" once per figure (165 errors), and
-- distributors such as Draft2Digital refuse the file. The <img> keeps its alt text; the wrapper loses the attribute.
--
-- Registered at: post-render: Quarto sets the attribute on a figure node (crossref, in `post-quarto`'s time) and only
-- renders that node into a <div> afterwards, so an earlier entry point never sees it. EPUB only: the website's pages
-- are not touched. scripts/ebook_validate.py checks the same rule.

local function is_epub()
  if quarto and quarto.doc and quarto.doc.is_format then
    return quarto.doc.is_format("epub")
  end
  return (FORMAT or ""):match("^epub") ~= nil
end

local function strip_alt(element)
  if not is_epub() or element.attributes["alt"] == nil then
    return nil
  end
  element.attributes["alt"] = nil
  return element
end

return {
  { Div = strip_alt, Span = strip_alt },
}
