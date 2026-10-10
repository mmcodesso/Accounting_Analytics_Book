-- A chapter has slides when its deck source exists: slides/chapter-NN/index.qmd, or slides/case-part-N/index.qmd for
-- a comprehensive case. There is no approval step.
-- The files the site links but does not serve (the book's PDF, EPUB and DOCX, the PowerPoint decks, the companion
-- and solution files) are assets of the revision's release, book.download in _variables.yml (scripts/release.py
-- publishes them; the book's own files are named from book.edition and book.revision). The text links them by
-- root path, and this filter points those links at the release in every format; scripts/release.py names the
-- assets the same way.
local found = {}
local book = nil

local function has_deck(id)
  if id == nil or not (id:match('^chapter%-%d%d$') or id:match('^case%-part%-%d$')) then return false end
  if found[id] == nil then
    local file = io.open(quarto.project.directory .. '/slides/' .. id .. '/index.qmd', 'r')
    found[id] = file ~= nil
    if file then file:close() end
  end
  return found[id]
end

-- The book block of _variables.yml (a top-level book: block of indented key: value lines), read once.
local function book_block()
  if book == nil then
    local file = io.open(quarto.project.directory .. '/_variables.yml', 'r')
    if file == nil then error('slide-links.lua: _variables.yml not found') end
    book = {}
    local in_book = false
    for line in file:lines() do
      line = line:gsub('\r$', '')
      if line:match('^%S') then
        in_book = line:match('^book:%s*$') ~= nil
      elseif in_book then
        local key, rest = line:match('^%s+([%w_-]+):%s*(.*)$')
        if key and book[key] == nil then
          book[key] = rest:match('^"([^"]*)"') or rest:match("^'([^']*)'") or rest:match('^([^%s#]+)')
        end
      end
    end
    file:close()
    for _, key in ipairs({'edition', 'revision', 'download'}) do
      if not book[key] then error('slide-links.lua: _variables.yml has no book.' .. key) end
    end
    book.download = (book.download:gsub('/+$', ''))
  end
  return book
end

local function release_url(name)
  return book_block().download .. '/' .. name
end

-- The PDF, EPUB and DOCX are named from the edition and the revision, as scripts/release.py names them:
-- Accounting_Analytics_First_Edition_Rev_2027_1.pdf for the first edition, revision 2027.1.
local function book_file(ext)
  local values = book_block()
  local words = {}
  for word in values.edition:gmatch('[^%s_%-]+') do
    words[#words + 1] = word:sub(1, 1):upper() .. word:sub(2)
  end
  local revision = (values.revision:gsub('[^%w]+', '_'))
  return 'Accounting_Analytics_' .. table.concat(words, '_') .. '_Edition_Rev_' .. revision .. '.' .. ext
end

-- The release name of a file linked by root path, or nil for any other link.
local function asset(target)
  local ext = target:match('^/downloads/book%-latest%.(%a+)$')
  if ext == 'pdf' or ext == 'epub' or ext == 'docx' then return book_file(ext) end
  if target:match('^/supplementary/') then return target:match('([^/]+)$') end
  return nil
end

-- The deck in the browser is on the site; outside HTML that link needs the site's address.
local function link_targets(id)
  local prefix = '/slides/' .. id .. '/'
  if FORMAT ~= 'html' and FORMAT ~= 'html5' then
    prefix = 'https://aa.accountinganalyticshub.com' .. prefix
  end
  return prefix .. 'index.html', release_url(id .. '.pptx')
end

-- An icon of the Bootstrap Icons font that Quarto's HTML pages load; decorative, so screen readers skip it.
local function icon(name)
  return pandoc.RawInline('html', '<i class="bi bi-' .. name .. '" aria-hidden="true"></i>')
end

local function words(text)
  local inlines = {}
  for word in text:gmatch('%S+') do
    if #inlines > 0 then inlines[#inlines + 1] = pandoc.Space() end
    inlines[#inlines + 1] = pandoc.Str(word)
  end
  return inlines
end

local function labeled(name, text)
  local inlines = {icon(name), pandoc.Space()}
  for _, inline in ipairs(words(text)) do inlines[#inlines + 1] = inline end
  return inlines
end

-- A chapter page's slide links. The deck opens in a new tab, so the chapter stays open where the reader was.
-- In HTML they form a bar of two pill buttons (styles/book.scss, .chapter-slides-bar); in the PDF a styled line;
-- in EPUB and DOCX a plain line.
function Div(div)
  if div.classes:includes('chapter-slides') then
    local id = div.attributes['data-chapter']
    if not has_deck(id) then return {} end
    local view, download_link = link_targets(id)
    local label = id:match('^case') and 'Case slides' or 'Chapter slides'
    if FORMAT == 'html' or FORMAT == 'html5' then
      local pill = function(kind, attributes)
        return pandoc.Attr('', {'slides-pill', 'slides-pill--' .. kind}, attributes or {})
      end
      return pandoc.Div({pandoc.Plain({
        pandoc.Span(labeled('easel2', label), pandoc.Attr('', {'chapter-slides-bar__label'})),
        pandoc.Link(labeled('play-circle', 'View slides'), view, '',
                    pill('view', {target = '_blank', rel = 'noopener'})),
        pandoc.Link(labeled('download', 'Download PowerPoint'), download_link, '', pill('download')),
      })}, pandoc.Attr('', {'chapter-slides-bar'}))
    end
    if FORMAT:match('latex') then
      -- The PDF's line, in the small blue sans-serif of its headings (colors from styles/book-pdf.tex).
      local latex = function(text) return pandoc.RawInline('latex', text) end
      return pandoc.Para({
        latex('{\\sffamily\\small\\textcolor{PrimaryBlue}{\\textbf{' .. label .. '}}\\quad '),
        pandoc.Link('View slides', view), latex('\\enspace{\\color{Ink!45}\\textbar}\\enspace '),
        pandoc.Link('Download PowerPoint', download_link), latex('}')})
    end
    return pandoc.Para({pandoc.Link('View slides', view), pandoc.Str(' | '),
                        pandoc.Link('Download PowerPoint', download_link)})
  end
end

-- The PDF's text font (Palatino in T1 encoding, styles/book-pdf.tex) has no middle dot, so LuaLaTeX would print
-- "ů" for every "·" (the separators of the Downloads page's table); set it as a centered dot instead.
function Str(str)
  if not FORMAT:match('latex') or not str.text:find('·', 1, true) then return nil end
  local inlines, rest = {}, str.text
  while true do
    local first, last = rest:find('·', 1, true)
    if not first then break end
    if first > 1 then inlines[#inlines + 1] = pandoc.Str(rest:sub(1, first - 1)) end
    inlines[#inlines + 1] = pandoc.RawInline('latex', '\\textperiodcentered{}')
    rest = rest:sub(last + 1)
  end
  if #rest > 0 then inlines[#inlines + 1] = pandoc.Str(rest) end
  return inlines
end

-- The book downloads and the supplementary files.
function Link(link)
  local name = asset(link.target)
  if name then
    link.target = release_url(name)
    return link
  end
end

-- A deck's download link in the Downloads page's table: [PowerPoint]{.slides data-chapter="chapter-04"}.
function Span(span)
  if span.classes:includes('slides') then
    local id = span.attributes['data-chapter']
    if not has_deck(id) then return pandoc.Str('—') end
    local _, download_link = link_targets(id)
    return pandoc.Link(span.content, download_link)
  end
end
