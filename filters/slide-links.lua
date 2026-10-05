-- The manifest is JSON (a YAML subset), so this filter needs no external parser.
local function chapters()
  local file = io.open(quarto.project.directory .. '/slides/manifest.yml', 'r')
  if not file then return {} end
  local manifest = pandoc.json.decode(file:read('*a'))
  file:close()
  local result = {}
  for _, chapter in ipairs(manifest.chapters or {}) do
    if chapter.status == 'approved' or
       (chapter.status == 'pilot' and os.getenv('AA_SLIDES_INCLUDE_PILOT') == '1') then
      table.insert(result, chapter)
    end
  end
  return result
end

local function links(chapter)
  local prefix = '/slides/' .. chapter.id .. '/'
  if FORMAT ~= 'html' and FORMAT ~= 'html5' then
    prefix = 'https://aa.accountinganalyticshub.com' .. prefix
  end
  return pandoc.Para({pandoc.Link('View slides', prefix .. 'index.html'), pandoc.Str(' · '),
                      pandoc.Link('Download PowerPoint', prefix .. chapter.id .. '.pptx')})
end

function Div(div)
  if div.classes:includes('chapter-slides') then
    for _, chapter in ipairs(chapters()) do
      if chapter.id == div.attributes['data-chapter'] then return links(chapter) end
    end
    return {}
  elseif div.classes:includes('chapter-slides-list') then
    local blocks = {}
    for _, chapter in ipairs(chapters()) do
      table.insert(blocks, pandoc.Para({pandoc.Str(string.format('Chapter %d: %s', chapter.number, chapter.title))}))
      table.insert(blocks, links(chapter))
    end
    if #blocks == 0 then return {} end
    local heading = pandoc.Header(2, 'Chapter slides')
    heading.identifier = 'chapter-slides'
    table.insert(blocks, 1, heading)
    return blocks
  end
end
