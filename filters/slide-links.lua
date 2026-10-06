-- The manifest is JSON (a YAML subset), so this filter needs no external parser.
local approved

local function chapters()
  if approved then return approved end
  approved = {}
  local file = io.open(quarto.project.directory .. '/slides/manifest.yml', 'r')
  if not file then return approved end
  local manifest = pandoc.json.decode(file:read('*a'))
  file:close()
  for _, chapter in ipairs(manifest.chapters or {}) do
    if chapter.status == 'approved' or
       (chapter.status == 'pilot' and os.getenv('AA_SLIDES_INCLUDE_PILOT') == '1') then
      table.insert(approved, chapter)
    end
  end
  return approved
end

local function find(id)
  for _, chapter in ipairs(chapters()) do
    if chapter.id == id then return chapter end
  end
end

local function link_targets(chapter)
  local prefix = '/slides/' .. chapter.id .. '/'
  if FORMAT ~= 'html' and FORMAT ~= 'html5' then
    prefix = 'https://aa.accountinganalyticshub.com' .. prefix
  end
  return prefix .. 'index.html', prefix .. chapter.id .. '.pptx'
end

-- A chapter page's slide links.
function Div(div)
  if div.classes:includes('chapter-slides') then
    local chapter = find(div.attributes['data-chapter'])
    if not chapter then return {} end
    local view, download = link_targets(chapter)
    return pandoc.Para({pandoc.Link('View slides', view), pandoc.Str(' · '),
                        pandoc.Link('Download PowerPoint', download)})
  end
end

-- Files the site serves (the supplementary files, the book downloads) are linked by root path, like the decks;
-- outside HTML the link needs the site's address.
function Link(link)
  if FORMAT ~= 'html' and FORMAT ~= 'html5' and
     (link.target:sub(1, 15) == '/supplementary/' or link.target:sub(1, 11) == '/downloads/') then
    link.target = 'https://aa.accountinganalyticshub.com' .. link.target
    return link
  end
end

-- A deck's download link in the Downloads page's table: [PowerPoint]{.slides data-chapter="chapter-04"}.
function Span(span)
  if span.classes:includes('slides') then
    local chapter = find(span.attributes['data-chapter'])
    if not chapter then return pandoc.Str('—') end
    local _, download = link_targets(chapter)
    return pandoc.Link(span.content, download)
  end
end
