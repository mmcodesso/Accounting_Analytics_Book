-- A chapter has slides when its deck source exists: slides/chapter-NN/index.qmd. There is no approval step.
local found = {}

local function has_deck(id)
  if id == nil or not id:match('^chapter%-%d%d$') then return false end
  if found[id] == nil then
    local file = io.open(quarto.project.directory .. '/slides/' .. id .. '/index.qmd', 'r')
    found[id] = file ~= nil
    if file then file:close() end
  end
  return found[id]
end

local function link_targets(id)
  local prefix = '/slides/' .. id .. '/'
  if FORMAT ~= 'html' and FORMAT ~= 'html5' then
    prefix = 'https://aa.accountinganalyticshub.com' .. prefix
  end
  return prefix .. 'index.html', prefix .. id .. '.pptx'
end

-- A chapter page's slide links.
function Div(div)
  if div.classes:includes('chapter-slides') then
    local id = div.attributes['data-chapter']
    if not has_deck(id) then return {} end
    local view, download = link_targets(id)
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
    local id = span.attributes['data-chapter']
    if not has_deck(id) then return pandoc.Str('—') end
    local _, download = link_targets(id)
    return pandoc.Link(span.content, download)
  end
end
