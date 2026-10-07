-- The structure every deck shares. Module dividers (# headings) that name a section of the chapter get
-- its number ("1.4 The Accounting Analytics Workflow"); a ::: {.roadmap} div becomes the roadmap of the
-- book's Parts and the deck's modules; dividers, callout slides and check slides get a background
-- image, which Reveal.js and PowerPoint both honor, so the two formats look alike.

local BACKGROUNDS = {'in-practice', 'watch-out', 'connecting-dots', 'check', 'answer'}

local function load_index()
  local path = quarto.project.directory .. '/_shared/book.json'
  local file = io.open(path, 'r')
  if not file then error('Missing ' .. path .. '; build the slides with scripts/build_all.py') end
  local index = pandoc.json.decode(file:read('a'), false)
  file:close()
  return index
end

local function background(name)
  return '../_shared/theme/bg-' .. name .. '.png'
end

local ROMAN = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}

local function roadmap(index, chapter, modules)
  -- Where the chapter sits in the book ("Part I of V ... Chapter 1 of 3"), then the deck's modules.
  local parts = {}
  for _, other in pairs(index.chapters) do
    if other.part then parts[other.part] = true end
  end
  local count = 0
  for _ in pairs(parts) do count = count + 1 end
  local position = 0
  for i, number in ipairs(chapter.part_chapters) do
    if math.tointeger(number) == math.tointeger(chapter.number) then position = i end
  end
  local numeral, name = (chapter.part or ''):match('^Part (%u+): (.+)$')
  local lead = numeral and ('**Part ' .. numeral .. ' of ' .. (ROMAN[count] or count) .. ': ' .. name ..
    '** · Chapter ' .. position .. ' of ' .. #chapter.part_chapters) or ''
  local lines = {lead, ''}
  for _, module in ipairs(modules) do table.insert(lines, '- ' .. module) end
  return quarto.utils.string_to_blocks(table.concat(lines, '\n'))
end

function Pandoc(doc)
  local deck = doc.meta['book-chapter'] and pandoc.utils.stringify(doc.meta['book-chapter'])
  if not deck then return doc end
  local index = load_index()
  local chapter = index.chapters[deck]
  if not chapter then error('No chapter ' .. deck .. ' in the book') end
  local numbers = {}
  for _, section in ipairs(chapter.sections) do numbers[section.title:lower()] = section.number end
  local modules = {}
  for _, block in ipairs(doc.blocks) do
    if block.t == 'Header' and block.level == 1 then
      local title = pandoc.utils.stringify(block.content)
      local number = not title:match('^Guided Tutorial') and numbers[title:lower()]
      if number then
        block.content:insert(1, pandoc.Space())
        block.content:insert(1, pandoc.Span(pandoc.Str(number), pandoc.Attr('', {'section-number'})))
      end
      table.insert(modules, number and (number .. ' ' .. title) or title)
      block.classes:insert('divider')
      block.attributes['background-image'] = background('divider')
      block.attributes['data-state'] = 'divider-state'
    elseif block.t == 'Header' and block.level == 2 then
      for _, name in ipairs(BACKGROUNDS) do
        if block.classes:includes(name) then block.attributes['background-image'] = background(name) end
      end
    end
  end
  doc.blocks = doc.blocks:walk({
    Div = function(div)
      if div.classes:includes('roadmap') then return roadmap(index, chapter, modules) end
    end,
  })
  return doc
end
