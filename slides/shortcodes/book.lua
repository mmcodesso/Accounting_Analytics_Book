-- Shortcodes that put the book's own content on a slide, cited by ID, so a deck always shows the
-- book's current figure, caption, alt text, table, objectives, key terms and tutorial steps.
-- They read _shared/book.json, which scripts/slides/prepare.py writes from the book at each build.
--
--   {{< book-figure fig-01-02 >}}                 the figure, with "Figure 1.2 · <caption>" under it
--   {{< book-table tbl-01-02 columns="Tool,Main Workflow Stages" rows="SQL,Microsoft Excel" >}}
--   {{< book-objectives >}}  {{< book-terms >}}  {{< book-exercises >}}
--   {{< book-steps 1.1 >}}  {{< book-checkpoint 1.1 answers="hide" >}}
--   {{< book-next >}}  {{< book-title >}}  {{< book-link >}}   (inline)

local index

local function book()
  if index == nil then
    local path = quarto.project.directory .. '/_shared/book.json'
    local file = io.open(path, 'r')
    if not file then error('Missing ' .. path .. '; build the slides with scripts/build_all.py') end
    index = pandoc.json.decode(file:read('a'), false)
    file:close()
  end
  return index
end

local function chapter(meta)
  local id = meta['book-chapter'] and pandoc.utils.stringify(meta['book-chapter'])
  local found = id and book().chapters[id]
  if not found then error('The deck has no book-chapter; build the slides with scripts/build_all.py') end
  return found
end

local function value(list, key)
  local item = list[key]
  if item == nil then return nil end
  local text = pandoc.utils.stringify(item)
  if text == '' then return nil end
  return text
end

local function names(text)
  local out = {}
  for item in text:gmatch('[^,]+') do
    table.insert(out, (item:gsub('^%s+', ''):gsub('%s+$', '')))
  end
  return out
end

local function plain(text)
  return (text:gsub('[*_`]', '')):lower()
end

local function blocks(markdown)
  return quarto.utils.string_to_blocks(markdown)
end

local function bullets(items, marker)
  local out = {}
  for i, item in ipairs(items) do
    table.insert(out, (marker == 'number' and (i .. '. ') or '- ') .. item)
  end
  return table.concat(out, '\n')
end

local function tutorial(meta, id)
  for _, found in ipairs(chapter(meta).tutorials) do
    if found.id == id then return found end
  end
  error('No Guided Tutorial ' .. tostring(id) .. ' in this chapter')
end

local function book_figure(args, kwargs)
  local id = pandoc.utils.stringify(args[1] or '')
  local figure = book().figures[id]
  if not figure then error('No figure ' .. id .. ' in the book') end
  local name = figure.src:match('([^/]+)$')
  -- PowerPoint cannot draw the SVG's HTML labels, so it gets the PNG exported from the same source.
  if quarto.doc.is_format('pptx') then name = name:gsub('%.svg$', '.png') end
  local attributes = 'fig-alt="' .. figure.alt .. '"'
  local width = value(kwargs, 'width')
  if width then attributes = attributes .. ' width="' .. width .. '"' end
  return blocks('![Figure ' .. figure.number .. ' · ' .. figure.caption .. '](/_shared/visuals/' .. name ..
                '){' .. attributes .. '}')
end

local function book_table(args, kwargs)
  local id = pandoc.utils.stringify(args[1] or '')
  local found = book().tables[id]
  if not found then error('No table ' .. id .. ' in the book') end
  local keep = {}
  local wanted = value(kwargs, 'columns')
  if wanted then
    for _, name in ipairs(names(wanted)) do
      local position
      for i, heading in ipairs(found.header) do
        if plain(heading) == name:lower() then position = i end
      end
      if not position then error(id .. ' has no column "' .. name .. '"') end
      table.insert(keep, position)
    end
  else
    for i = 1, #found.header do keep[i] = i end
  end
  local rows = found.rows
  local wanted_rows = value(kwargs, 'rows')
  if wanted_rows then
    rows = {}
    for _, name in ipairs(names(wanted_rows)) do
      local row
      for _, candidate in ipairs(found.rows) do
        if plain(candidate[1]) == name:lower() then row = candidate end
      end
      if not row then error(id .. ' has no row "' .. name .. '"') end
      table.insert(rows, row)
    end
  end
  local function line(cells)
    local out = {}
    for _, i in ipairs(keep) do table.insert(out, cells[i] or '') end
    return '| ' .. table.concat(out, ' | ') .. ' |'
  end
  -- Column widths follow the longest cell of each column. Pandoc reads them from the dashes of the
  -- separator, which only count when a line is longer than 72 characters; this one always is.
  local longest, total = {}, 0
  for position, i in ipairs(keep) do
    local width = #plain(found.header[i] or '')
    for _, row in ipairs(rows) do width = math.max(width, #plain(row[i] or '')) end
    longest[position] = math.max(width, 8)
    total = total + longest[position]
  end
  local dashes = {}
  for position in ipairs(keep) do
    table.insert(dashes, string.rep('-', math.max(3, math.floor(100 * longest[position] / total + 0.5))))
  end
  -- The source line goes above the table, as the book places table captions; in PowerPoint, text
  -- after a table would start a new slide, and a table caption is drawn at a fixed place over long rows.
  local lines = {'[Table ' .. found.number .. ' · ' .. found.caption .. ']{.source}', '',
                 line(found.header), '|' .. table.concat(dashes, '|') .. '|'}
  for _, row in ipairs(rows) do table.insert(lines, line(row)) end
  return blocks(table.concat(lines, '\n'))
end

local function book_objectives(_, _, meta)
  return blocks(bullets(chapter(meta).objectives, 'number'))
end

local function book_terms(_, _, meta)
  -- One paragraph, so a chapter's twenty-odd terms fit one slide in both formats.
  return blocks(table.concat(chapter(meta).key_terms, ' · '))
end

local function book_steps(args, _, meta)
  local steps = {}
  for _, step in ipairs(tutorial(meta, pandoc.utils.stringify(args[1] or '')).steps) do
    table.insert(steps, step.title)
  end
  return blocks(bullets(steps, 'number'))
end

local function book_checkpoint(args, kwargs, meta)
  local found = tutorial(meta, pandoc.utils.stringify(args[1] or '')).checkpoint
  local items = {}
  for _, item in ipairs(found.items) do
    -- answers="hide" drops a question's trailing parenthetical answer, which the notes can give instead.
    if value(kwargs, 'answers') == 'hide' and item:match('%?') then item = item:gsub('%s*%b()%s*$', '') end
    table.insert(items, item)
  end
  local markdown = bullets(items)
  if value(kwargs, 'lead') == 'true' then markdown = found.lead .. '\n\n' .. markdown end
  return blocks(markdown)
end

local function book_exercises(_, _, meta)
  local lines, current = {}, nil
  for _, exercise in ipairs(chapter(meta).exercises) do
    local perspective = exercise.perspective:gsub(' Exercises$', '')
    if perspective ~= current then
      table.insert(lines, '- ' .. perspective)
      current = perspective
    end
    table.insert(lines, '    - Exercise ' .. exercise.id .. ': ' .. exercise.title)
  end
  return blocks(table.concat(lines, '\n'))
end

local function inline(text)
  return quarto.utils.string_to_inlines(text)
end

local function book_next(_, _, meta)
  return inline(chapter(meta).next)
end

local function book_title()
  return inline(book().book_title)
end

local function book_link(_, _, meta)
  local url = book().book_url .. chapter(meta).path:gsub('%.qmd$', '.html')
  return pandoc.Link(url, url)
end

return {
  ['book-figure'] = book_figure,
  ['book-table'] = book_table,
  ['book-objectives'] = book_objectives,
  ['book-terms'] = book_terms,
  ['book-steps'] = book_steps,
  ['book-checkpoint'] = book_checkpoint,
  ['book-exercises'] = book_exercises,
  ['book-next'] = book_next,
  ['book-title'] = book_title,
  ['book-link'] = book_link,
}
