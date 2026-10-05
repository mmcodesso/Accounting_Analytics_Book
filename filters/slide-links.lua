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

local function link_targets(chapter)
  local prefix = '/slides/' .. chapter.id .. '/'
  if FORMAT ~= 'html' and FORMAT ~= 'html5' then
    prefix = 'https://aa.accountinganalyticshub.com' .. prefix
  end
  return prefix .. 'index.html', prefix .. chapter.id .. '.pptx'
end

local function links(chapter)
  local view, download = link_targets(chapter)
  return pandoc.Para({pandoc.Link('View slides', view), pandoc.Str(' · '),
                      pandoc.Link('Download PowerPoint', download)})
end

function Div(div)
  if div.classes:includes('chapter-slides') then
    for _, chapter in ipairs(chapters()) do
      if chapter.id == div.attributes['data-chapter'] then return links(chapter) end
    end
    return {}
  elseif div.classes:includes('chapter-slides-list') then
    local rows = {}
    for _, chapter in ipairs(chapters()) do
      local view, download = link_targets(chapter)
      table.insert(rows, {
        {pandoc.Plain(string.format('Chapter %d: %s', chapter.number, chapter.title))},
        {pandoc.Plain({pandoc.Link('View slides', view)})},
        {pandoc.Plain({pandoc.Link('PowerPoint', download)})}
      })
    end
    if #rows == 0 then return {} end
    local heading = pandoc.Header(2, 'Chapter slides')
    heading.identifier = 'chapter-slides'
    local slide_table = pandoc.utils.from_simple_table(pandoc.SimpleTable(
      {},
      {pandoc.AlignLeft, pandoc.AlignLeft, pandoc.AlignLeft},
      {0.60, 0.20, 0.20},
      {{pandoc.Plain('Chapter name')}, {pandoc.Plain('View slides')}, {pandoc.Plain('Download')}},
      rows
    ))
    return {heading, slide_table}
  end
end
