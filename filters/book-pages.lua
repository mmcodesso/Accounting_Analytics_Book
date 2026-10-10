-- The title page and the copyright page that open the PDF, EPUB and DOCX. Their text is front-matter/_book-pages.qmd,
-- included at the top of index.qmd: the title page is one [line]{.class} paragraph per line, and the copyright page
-- names each version's ISBN as [key]{.isbn}, filled in here from the isbn block of _quarto.yml ("ISBN to be
-- assigned" while it is blank). This filter lays the two pages out for each format; the website has neither.
--   PDF: the pages go between the cover (\maketitle) and the table of contents, in the aatitlepage and
--        aacopyrightpage layouts of styles/book-pdf.tex.
--   EPUB: they fill the EPUB's title page (the book-pages variable of styles/book-epub.template) as XHTML, styled
--         inline (an EPUB css file would replace Pandoc's default stylesheet for the whole book). Kept out of the
--         body, where Pandoc would set the book's title as a heading above them.
--   DOCX: Pandoc's title block (Title, Subtitle and Author, from the metadata) starts the title page, each page is
--         a section, and the table of contents is written here after the copyright page (toc is off for docx in
--         _quarto.yml), already listing the headings.

local isbns = nil          -- key -> ISBN text ('' while unassigned), from the isbn block of _quarto.yml
local title_lines = nil    -- the title page's lines: {class, content}
local copyright = nil      -- the copyright page's blocks
local toc_title = nil      -- the table of contents' title, for the DOCX

local LINE_CLASSES = {'book-title', 'book-subtitle', 'book-author', 'book-edition', 'book-revision', 'book-publisher'}

local function is_format(name)
  if name == 'latex' then return FORMAT:match('latex') ~= nil end
  if name == 'epub' then return FORMAT:match('^epub') ~= nil end
  return FORMAT == name
end

local function trim(text)
  return (text:gsub('^%s+', ''):gsub('%s+$', ''))
end

-- An ISBN-13 (hyphens and spaces allowed): 978 or 979, twelve more digits, the last a check digit.
local function valid_isbn(text)
  local digits = text:gsub('[%s%-]', '')
  if not digits:match('^97[89]' .. string.rep('%d', 10) .. '$') then return false end
  local sum = 0
  for i = 1, 12 do
    sum = sum + tonumber(digits:sub(i, i)) * (i % 2 == 1 and 1 or 3)
  end
  return (10 - sum % 10) % 10 == tonumber(digits:sub(13, 13))
end

local function read_meta(meta)
  toc_title = meta['toc-title'] and pandoc.utils.stringify(meta['toc-title']) or 'Table of contents'
  isbns = {}
  if meta.isbn == nil then return end
  for key, value in pairs(meta.isbn) do
    local text = trim(pandoc.utils.stringify(value))
    if text ~= '' and not valid_isbn(text) then
      error('book-pages.lua: isbn.' .. key .. ' in _quarto.yml is not a valid ISBN-13: ' .. text)
    end
    isbns[key] = text
  end
end

local function isbn_span(span)
  local key = pandoc.utils.stringify(span.content)
  local value = isbns[key]
  if value == nil then
    error('book-pages.lua: [' .. key .. ']{.isbn} names no key of the isbn block in _quarto.yml')
  end
  if value == '' then value = 'to be assigned' end
  return pandoc.Inlines('ISBN ' .. value)
end

local function line_class(span)
  for _, class in ipairs(LINE_CLASSES) do
    if span.classes:includes(class) then return class end
  end
  return nil
end

-- "first edition" reads "First Edition" on the title page.
local function title_case(inlines)
  return pandoc.Span(inlines):walk({
    Str = function(str) return pandoc.Str((str.text:gsub('^%l', string.upper))) end,
  }).content
end

local function read_title_page(div)
  title_lines = {}
  for _, block in ipairs(div.content) do
    local span = (block.t == 'Para' or block.t == 'Plain') and #block.content == 1 and block.content[1]
    local class = span and span.t == 'Span' and line_class(span)
    if not class then
      error('book-pages.lua: each line of #book-title-page must be one [text]{.class} paragraph, the class one of '
            .. table.concat(LINE_CLASSES, ', '))
    end
    local content = class == 'book-edition' and title_case(span.content) or span.content
    title_lines[#title_lines + 1] = {class = class, content = content}
  end
end

-- PDF ----------------------------------------------------------------------------------------------------------------

-- The PDF's text font (Palatino in T1 encoding) has no copyright sign at its Unicode position.
local function latex_symbols(doc)
  return doc:walk({
    Str = function(str)
      if not str.text:find('©', 1, true) then return nil end
      local inlines, rest = {}, str.text
      while true do
        local first, last = rest:find('©', 1, true)
        if not first then break end
        if first > 1 then inlines[#inlines + 1] = pandoc.Str(rest:sub(1, first - 1)) end
        inlines[#inlines + 1] = pandoc.RawInline('latex', '\\textcopyright{}')
        rest = rest:sub(last + 1)
      end
      if #rest > 0 then inlines[#inlines + 1] = pandoc.Str(rest) end
      return inlines
    end,
  })
end

local function latex(blocks)
  return trim(pandoc.write(latex_symbols(pandoc.Pandoc(blocks)), 'latex'))
end

local function latex_pages()
  local parts = {}
  if title_lines then
    parts[#parts + 1] = '\\begin{aatitlepage}'
    for _, line in ipairs(title_lines) do
      parts[#parts + 1] = '\\aa' .. line.class:gsub('%-', '') .. '{' .. latex({pandoc.Plain(line.content)}) .. '}'
    end
    parts[#parts + 1] = '\\end{aatitlepage}'
  end
  if copyright then
    parts[#parts + 1] = '\\begin{aacopyrightpage}\n' .. latex(copyright) .. '\n\\end{aacopyrightpage}'
  end
  return table.concat(parts, '\n')
end

-- EPUB ---------------------------------------------------------------------------------------------------------------

local EPUB_LINE_STYLE = {
  ['book-title'] = 'font-size: 2em; font-weight: bold; color: #1A5276; margin: 3em 0 0.4em 0;',
  ['book-subtitle'] = 'font-size: 1.4em; margin: 0 0 2.5em 0;',
  ['book-author'] = 'font-size: 1.2em; margin: 0 0 5em 0;',
  ['book-edition'] = 'margin: 0;',
  ['book-revision'] = 'margin: 0 0 2em 0;',
  ['book-publisher'] = 'font-weight: bold; margin: 0;',
}

local function html(blocks)
  return trim(pandoc.write(pandoc.Pandoc(blocks), 'html5'))
end

local function epub_title_page()
  local lines = {}
  for _, line in ipairs(title_lines) do
    lines[#lines + 1] = '<p style="' .. EPUB_LINE_STYLE[line.class] .. '">' .. html({pandoc.Plain(line.content)})
                        .. '</p>'
  end
  return pandoc.RawBlock('html', '<section epub:type="titlepage" style="text-align: center; font-family: sans-serif;'
                         .. ' color: #2C3E50;">\n' .. table.concat(lines, '\n') .. '\n</section>')
end

local function epub_copyright_page(div)
  return pandoc.RawBlock('html', '<section epub:type="copyright-page" style="font-size: 0.85em; margin-top: 2em;'
                         .. ' page-break-before: always; break-before: page;">\n' .. html(div.content)
                         .. '\n</section>')
end

-- DOCX ---------------------------------------------------------------------------------------------------------------
-- Pandoc's title block is the top of the title page: the filter gives it the page's title, subtitle and author
-- lines (so the file's properties carry them too), styled Title, Subtitle and Author in styles/reference.docx. The
-- rest of the page follows in that file's Book Rule, Book Edition and Book Publisher styles. Each page is a section
-- of its own: the title page's ends the page, and the copyright page's sets its text at the foot of the page, as
-- in the PDF. Then the table of contents, which Word fills in with page numbers when it updates the field; until
-- then (a file opened in Protected View, or in another program) it lists the headings, each a link.

local function xml_text(text)
  return (text:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'):gsub('"', '&quot;'))
end

local function docx_paragraph(style, text)
  local run = text and ('<w:r><w:t xml:space="preserve">' .. xml_text(text) .. '</w:t></w:r>') or ''
  return '<w:p><w:pPr><w:pStyle w:val="' .. style .. '" /></w:pPr>' .. run .. '</w:p>'
end

-- An empty paragraph that ends a section (and so its page); vAlign bottom sets the section's text at the foot.
local function docx_section_end(valign)
  local align = valign and ('<w:vAlign w:val="' .. valign .. '" />') or ''
  return pandoc.RawBlock('openxml', '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact" />'
    .. '<w:rPr><w:sz w:val="2" /><w:szCs w:val="2" /></w:rPr><w:sectPr><w:footnotePr><w:numRestart w:val="eachSect" />'
    .. '</w:footnotePr>' .. align .. '</w:sectPr></w:pPr></w:p>')
end

local DOCX_LINE_STYLE = {['book-edition'] = 'BookEdition', ['book-revision'] = 'BookEdition',
                         ['book-publisher'] = 'BookPublisher'}

local function docx_title_page()
  local xml = {docx_paragraph('BookRule')}
  for _, line in ipairs(title_lines) do
    local style = DOCX_LINE_STYLE[line.class]
    if style then xml[#xml + 1] = docx_paragraph(style, pandoc.utils.stringify(line.content)) end
  end
  return {pandoc.RawBlock('openxml', table.concat(xml)), docx_section_end(nil)}
end

local function docx_copyright_page(div)
  return {pandoc.Div(div.content, pandoc.Attr('', {}, {['custom-style'] = 'Copyright Text'})),
          docx_section_end('bottom')}
end

local function title_line(class)
  for _, line in ipairs(title_lines or {}) do
    if line.class == class then return line.content end
  end
  return nil
end

-- The bookmark Pandoc writes for a heading's identifier (toBookmarkName in Pandoc's DOCX writer): the identifier
-- itself when it starts with a letter and has at most 40 characters, otherwise X and the SHA-1 digest less its
-- first digit.
local function bookmark(id)
  if id:match('^%a') and utf8.len(id) <= 40 then return id end
  return 'X' .. pandoc.utils.sha1(id):sub(2)
end

-- Word's own field (TOC \o "1-3" \h \z \u, as Pandoc writes it for --toc), its result the headings of levels 1 to
-- 3 in the toc 1 to toc 3 styles, without page numbers.
local function docx_toc(doc)
  local entries = {}
  -- A Part's title page is a quarto-book-part div, which Quarto drops from every format but LaTeX after this filter.
  doc.blocks:walk({
    Div = function(div) if div.classes:includes('quarto-book-part') then return {} end end,
  }):walk({
    Header = function(header)
      if header.level <= 3 then entries[#entries + 1] = {header.level, header.identifier,
                                                        pandoc.utils.stringify(header.content)} end
    end,
  })
  local begin = '<w:r><w:fldChar w:fldCharType="begin" w:dirty="true" /></w:r><w:r><w:instrText xml:space="preserve">'
    .. 'TOC \\o &quot;1-3&quot; \\h \\z \\u</w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate" /></w:r>'
  local field_end = '<w:r><w:fldChar w:fldCharType="end" /></w:r>'
  local xml = {'<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents" /><w:docPartUnique />'
    .. '</w:docPartObj></w:sdtPr><w:sdtContent>', docx_paragraph('TOCHeading', toc_title)}
  if #entries == 0 then
    xml[#xml + 1] = '<w:p>' .. begin .. field_end .. '</w:p>'
  end
  for i, entry in ipairs(entries) do
    local level, id, text = entry[1], entry[2], entry[3]
    local run = '<w:r><w:t xml:space="preserve">' .. xml_text(text) .. '</w:t></w:r>'
    if id ~= '' then run = '<w:hyperlink w:anchor="' .. xml_text(bookmark(id)) .. '" w:history="1">' .. run .. '</w:hyperlink>' end
    xml[#xml + 1] = '<w:p><w:pPr><w:pStyle w:val="TOC' .. level .. '" /></w:pPr>' .. (i == 1 and begin or '') .. run
                    .. (i == #entries and field_end or '') .. '</w:p>'
  end
  xml[#xml + 1] = '</w:sdtContent></w:sdt>'
  return pandoc.RawBlock('openxml', table.concat(xml))
end

-- The filters --------------------------------------------------------------------------------------------------------

-- Both pages are taken out of the body: Quarto sets index.qmd's heading before anything that precedes it in the
-- file, so finish puts the DOCX's pages back at the very start of the document, the PDF's between the cover and
-- the table of contents, and the EPUB's on its title page.
local front = {}

local function pages(div)
  if div.identifier == 'book-title-page' then
    read_title_page(div)
    if is_format('epub') then front.epub_title = epub_title_page() end
    if is_format('docx') then front.title = docx_title_page() end
    return {}
  end
  if div.identifier == 'book-copyright-page' then
    copyright = div.content
    if is_format('epub') then front.epub_copyright = epub_copyright_page(div) end
    if is_format('docx') then front.copyright = docx_copyright_page(div) end
    return {}
  end
end

local function finish(doc)
  if is_format('latex') and (title_lines or copyright) then
    quarto.doc.include_text('before-body', latex_pages())
  end
  if is_format('docx') then
    local blocks = pandoc.Blocks({})
    for _, part in ipairs({front.title or {}, front.copyright or {}}) do blocks:extend(part) end
    blocks:insert(docx_toc(doc))
    blocks:extend(doc.blocks)
    doc.blocks = blocks
    for meta, class in pairs({title = 'book-title', subtitle = 'book-subtitle', author = 'book-author'}) do
      local line = title_line(class)
      if line then doc.meta[meta] = meta == 'author' and pandoc.MetaList({pandoc.MetaInlines(line)})
                                    or pandoc.MetaInlines(line) end
    end
  end
  local epub_pages = pandoc.Blocks({})
  if front.epub_title then epub_pages:insert(front.epub_title) end
  if front.epub_copyright then epub_pages:insert(front.epub_copyright) end
  if #epub_pages > 0 then doc.meta['book-pages'] = pandoc.MetaBlocks(epub_pages) end
  if is_format('epub') and isbns.epub and isbns.epub ~= '' then
    doc.meta.identifier = pandoc.MetaList({pandoc.MetaMap({
      scheme = pandoc.MetaString('ISBN-13'), text = pandoc.MetaString(isbns.epub)})})
  end
  return doc
end

return {
  {Meta = function(meta) read_meta(meta) end},
  {Span = function(span) if span.classes:includes('isbn') then return isbn_span(span) end end},
  {Div = pages},
  {Pandoc = finish},
}
