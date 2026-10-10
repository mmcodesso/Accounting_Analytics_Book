-- Shortcodes that put the book's own content on a slide, cited by ID, so a deck always shows the
-- book's current figure, caption, alt text, table, objectives, key terms and tutorial steps.
-- They read _shared/book.json, which scripts/slides/prepare.py writes from the book at each build.
--
--   {{< book-figure fig-01-02 >}}                 the figure, with "Figure 1.2 · <caption>" under it
--   {{< book-figure fig-03-07 crop="0,0,1,0.56" >}}   a detail: left, top, width, height as fractions
--   {{< book-table tbl-01-02 columns="Tool,Main Workflow Stages" rows="SQL,Microsoft Excel" >}}
--   {{< book-objectives >}} or {{< book-objectives 1-3 >}}  {{< book-terms >}}  {{< book-exercises >}}
--   {{< book-steps 1.1 >}}  {{< book-checkpoint 1.1 answers="hide" >}}
--   {{< book-next >}}  {{< book-title >}}  {{< book-link >}}   (inline)
--   A case's parts, each list with an optional range:
--   {{< book-requirement 3 >}}  {{< book-requirements 3-5 >}}  {{< book-milestones >}}
--   {{< book-deliverables >}}  {{< book-criteria 1-3 >}}

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

local function crop_key(text)
  -- The staged name of a crop, as scripts/slides/prepare.py writes it: 0,0,1,0.56 -> 0-0-1-0p56.
  local parts = {}
  for item in text:gmatch('[^,]+') do
    local number = tonumber(item)
    if not number then error('crop="' .. text .. '" needs four numbers: left, top, width, height') end
    table.insert(parts, (string.format('%g', number):gsub('%.', 'p')))
  end
  if #parts ~= 4 then error('crop="' .. text .. '" needs four numbers: left, top, width, height') end
  return table.concat(parts, '-')
end

local function book_figure(args, kwargs)
  local id = pandoc.utils.stringify(args[1] or '')
  local figure = book().figures[id]
  if not figure then error('No figure ' .. id .. ' in the book') end
  local name = figure.src:match('([^/]+)$')
  local caption, alt = figure.caption, figure.alt
  -- crop="left,top,width,height" (fractions of the figure) shows a detail, staged under its own name.
  local crop = value(kwargs, 'crop')
  if crop then
    name = name:gsub('(%.%w+)$', '.crop-' .. crop_key(crop) .. '%1')
    caption, alt = caption .. ' (detail)', 'Detail of: ' .. alt
  end
  -- PowerPoint cannot draw the SVG's HTML labels, so it gets the PNG exported from the same source.
  if quarto.doc.is_format('pptx') then name = name:gsub('%.svg$', '.png') end
  local attributes = 'fig-alt="' .. alt .. '"'
  local width = value(kwargs, 'width')
  if width then attributes = attributes .. ' width="' .. width .. '"' end
  return blocks('![Figure ' .. figure.number .. ' · ' .. caption .. '](/_shared/visuals/' .. name ..
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
  -- An optional range, such as 1-5 and 6-10, splits a long table over two slides by position; rows=
  -- names rows by their first cell, which cannot work when those cells hold commas.
  local first, last = pandoc.utils.stringify(args[2] or ''):match('^(%d+)%-(%d+)$')
  if first then
    rows = {}
    for i = tonumber(first), math.min(tonumber(last), #found.rows) do table.insert(rows, found.rows[i]) end
    if #rows == 0 then error(id .. ' has no rows ' .. first .. '-' .. last) end
  elseif wanted_rows then
    rows = {}
    for _, name in ipairs(names(wanted_rows)) do
      -- Every row whose first cell matches, in the book's order (several rows may share it).
      local matched = false
      for _, candidate in ipairs(found.rows) do
        if plain(candidate[1]) == name:lower() then
          table.insert(rows, candidate)
          matched = true
        end
      end
      if not matched then error(id .. ' has no row "' .. name .. '"') end
    end
  end
  local function line(cells)
    local out = {}
    for _, i in ipairs(keep) do table.insert(out, cells[i] or '') end
    return '| ' .. table.concat(out, ' | ') .. ' |'
  end
  -- Column widths, in percent of the table: each column in proportion to its longest cell (capped at
  -- 60 characters, so long prose shares the room), but never below what its longest word needs at the
  -- table text size (about 1.1% of the width per character, with the cell margins; a word in code
  -- needs two characters more of margin, so a name such as USERELATIONSHIP does not break). Pandoc reads the
  -- widths from the dashes of the separator, which count only when a line exceeds 72 characters.
  local weights, floors, total = {}, {}, 0
  for position, i in ipairs(keep) do
    local width, word, code = 0, 0, 0
    for _, cells in ipairs({found.header, table.unpack(rows)}) do
      local text = plain(cells[i] or '')
      width = math.max(width, #text)
      for token in text:gmatch('%S+') do word = math.max(word, #token) end
      for span in (cells[i] or ''):gmatch('`([^`]+)`') do
        for token in span:gmatch('%S+') do code = math.max(code, #token) end
      end
    end
    weights[position] = math.max(math.min(width, 60), 1)
    floors[position] = math.max(word + 3, code > 0 and code + 5 or 0) * 1.1
    total = total + weights[position]
  end
  local shares, raised, floor_total, rest = {}, {}, 0, 0
  for position, weight in ipairs(weights) do
    if 100 * weight / total < floors[position] then
      shares[position], raised[position] = floors[position], true
      floor_total = floor_total + floors[position]
    else
      rest = rest + weight
    end
  end
  for position, weight in ipairs(weights) do
    if not raised[position] then shares[position] = (100 - floor_total) * weight / rest end
  end
  -- widths="26,17,15,27,15" overrides the estimate, in percent, one per column shown: for a table whose
  -- long headers would starve the short cells under them (the estimate weighs headers like any cell).
  local wanted_widths = value(kwargs, 'widths')
  if wanted_widths then
    local given = names(wanted_widths)
    if #given ~= #keep then error(id .. ': widths= needs ' .. #keep .. ' values, one per column') end
    local sum = 0
    for position, text in ipairs(given) do
      shares[position] = tonumber(text) or error(id .. ': widths= takes numbers, not "' .. text .. '"')
      sum = sum + shares[position]
    end
    for position in ipairs(given) do shares[position] = 100 * shares[position] / sum end
  end
  local dashes = {}
  for position in ipairs(keep) do
    table.insert(dashes, string.rep('-', math.max(3, math.floor(shares[position] + 0.5))))
  end
  -- The source line goes above the table, as the book places table captions; in PowerPoint, text
  -- after a table would start a new slide, and a table caption is drawn at a fixed place over long rows.
  -- It names the table by its caption's first sentence: a caption that goes on to define the table's
  -- symbols would fill PowerPoint's one-line caption box, so the deck's notes carry the rest.
  local title = found.caption:match('^(.-%.)%s') or found.caption
  local lines = {'[Table ' .. found.number .. ' · ' .. title:gsub('%.$', '') .. ']{.source}', '',
                 line(found.header), '|' .. table.concat(dashes, '|') .. '|'}
  for _, row in ipairs(rows) do table.insert(lines, line(row)) end
  return blocks(table.concat(lines, '\n'))
end

local function book_objectives(args, _, meta)
  -- An optional range, such as 1-3 and 4-6, splits a long set over two slides.
  local objectives = chapter(meta).objectives
  local first, last = pandoc.utils.stringify(args[1] or ''):match('^(%d+)%-(%d+)$')
  first, last = tonumber(first) or 1, tonumber(last) or #objectives
  local lines = {}
  for i = first, math.min(last, #objectives) do
    table.insert(lines, i .. '. ' .. objectives[i])
  end
  if #lines == 0 then error('No learning objectives ' .. first .. '-' .. last .. ' in this chapter') end
  return blocks(table.concat(lines, '\n'))
end

local function book_terms(_, _, meta)
  -- One paragraph, so a chapter's twenty-odd terms fit one slide in both formats.
  return blocks(table.concat(chapter(meta).key_terms, ' · '))
end

local function book_steps(args, _, meta)
  -- An optional range, such as 1-6 and 7-11, splits a long tutorial over two slides; each step keeps its number.
  local steps = tutorial(meta, pandoc.utils.stringify(args[1] or '')).steps
  local first, last = pandoc.utils.stringify(args[2] or ''):match('^(%d+)%-(%d+)$')
  first, last = tonumber(first) or 1, tonumber(last) or #steps
  local lines = {}
  for _, step in ipairs(steps) do
    if step.number >= first and step.number <= last then
      table.insert(lines, math.tointeger(step.number) .. '. ' .. step.title)
    end
  end
  if #lines == 0 then error('No steps ' .. first .. '-' .. last .. ' in this tutorial') end
  return blocks(table.concat(lines, '\n'))
end

local function book_checkpoint(args, kwargs, meta)
  local found = tutorial(meta, pandoc.utils.stringify(args[1] or '')).checkpoint
  -- An optional range, such as 1-3 and 4-6, splits a long checkpoint over two slides.
  local first, last = pandoc.utils.stringify(args[2] or ''):match('^(%d+)%-(%d+)$')
  first, last = tonumber(first) or 1, tonumber(last) or #found.items
  local items = {}
  for i, item in ipairs(found.items) do
    if i >= first and i <= last then
      -- answers="hide" drops a question's trailing parenthetical answer, which the notes can give instead.
      if value(kwargs, 'answers') == 'hide' and item:match('%?') then item = item:gsub('%s*%b()%s*$', '') end
      table.insert(items, item)
    end
  end
  if #items == 0 then error('No checkpoint items ' .. first .. '-' .. last .. ' in this tutorial') end
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

local function range(args, position, count)
  -- An optional range such as 1-3; without one, the whole list.
  local first, last = pandoc.utils.stringify(args[position] or ''):match('^(%d+)%-(%d+)$')
  return tonumber(first) or 1, math.min(tonumber(last) or count, count)
end

local function references(text)
  -- A case's lists are the book's text, which may cite a table or figure ("every assumption in
  -- @tbl-18-02"); a deck cannot resolve the book's cross-references, so they become "Table 18.2".
  return (text:gsub('@((%a+)%-[%w%-]*%w)', function(id, kind)
    local found = (kind == 'tbl' and book().tables[id]) or (kind == 'fig' and book().figures[id]) or nil
    if not found then error('No ' .. id .. ' in the book') end
    return (kind == 'tbl' and 'Table ' or 'Figure ') .. found.number
  end))
end

local function case_list(meta, name, label)
  local list = chapter(meta)[name] or {}
  if #list == 0 then error('This chapter has no ' .. label) end
  return list
end

local function requirement_line(found)
  -- A no-break space keeps "Chapter 9" together when a long title wraps its source line.
  local chapters = found.chapters ~= '' and (' (' .. found.chapters:gsub('(Chapters?) (%d)', '%1\u{00A0}%2') .. ')') or ''
  return references(found.title .. chapters)
end

local function book_requirement(args, _, meta)
  -- The requirement's source line, as a table's: "Requirement 3 · Title (Chapters ...)".
  local number = tonumber(pandoc.utils.stringify(args[1] or ''))
  for _, found in ipairs(case_list(meta, 'requirements', 'requirements')) do
    if math.tointeger(found.number) == number then
      return blocks('[Requirement ' .. number .. ' · ' .. requirement_line(found) .. ']{.source}')
    end
  end
  error('No Requirement ' .. tostring(number) .. ' in this chapter')
end

local function book_requirements(args, _, meta)
  local list = case_list(meta, 'requirements', 'requirements')
  local first, last = range(args, 1, math.tointeger(list[#list].number))
  local items = {}
  for _, found in ipairs(list) do
    local number = math.tointeger(found.number)
    if number >= first and number <= last then
      table.insert(items, 'Requirement ' .. number .. ': ' .. requirement_line(found))
    end
  end
  if #items == 0 then error('No requirements ' .. first .. '-' .. last .. ' in this chapter') end
  return blocks(bullets(items))
end

local function book_milestones(args, _, meta)
  -- Numbered as the book numbers them, with the requirements each milestone covers.
  local list = case_list(meta, 'milestones', 'milestones')
  local first, last = range(args, 1, #list)
  if first == last and list[first] then
    -- One milestone, as a phase's slide shows it: "Milestone 2: The adjustments (Requirements 3 to 5): ...".
    local found = list[first]
    local covers = found.requirements ~= '' and (' (' .. found.requirements .. ')') or ''
    return blocks(references('**Milestone ' .. first .. ': ' .. found.name .. '**' .. covers ..
      (found.text ~= '' and (': ' .. found.text) or '')))
  end
  local lines = {}
  for i = first, last do
    local found = list[i]
    local covers = found.requirements ~= '' and (' (' .. found.requirements .. ')') or ''
    table.insert(lines, references(math.tointeger(found.number) .. '. **' .. found.name .. '**' .. covers ..
      (found.text ~= '' and (': ' .. found.text) or '')))
  end
  if #lines == 0 then error('No milestones ' .. first .. '-' .. last .. ' in this chapter') end
  return blocks(table.concat(lines, '\n'))
end

local function book_deliverables(args, _, meta)
  local list = case_list(meta, 'deliverables', 'deliverables')
  -- A comprehensive case states its deliverable in one paragraph, which stays a paragraph.
  if #list == 1 then return blocks(references(list[1])) end
  local first, last = range(args, 1, #list)
  local lines = {}
  for i = first, last do table.insert(lines, i .. '. ' .. references(list[i])) end
  if #lines == 0 then error('No deliverables ' .. first .. '-' .. last .. ' in this chapter') end
  return blocks(table.concat(lines, '\n'))
end

local function book_criteria(args, _, meta)
  -- What a Strong Submission Includes.
  local list = case_list(meta, 'criteria', 'criteria of a strong submission')
  local first, last = range(args, 1, #list)
  local items = {}
  for i = first, last do table.insert(items, references(list[i])) end
  if #items == 0 then error('No criteria ' .. first .. '-' .. last .. ' in this chapter') end
  return blocks(bullets(items))
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
  ['book-requirement'] = book_requirement,
  ['book-requirements'] = book_requirements,
  ['book-milestones'] = book_milestones,
  ['book-deliverables'] = book_deliverables,
  ['book-criteria'] = book_criteria,
}
