-- Pandoc Lua filters for the instructor PDFs (facts/instructor/guides.py pdf), LaTeX output only.
--
--  * a paragraph that is one image of a built figure (../figures/<unit folder>/IF-06-1-A.pdf, the figure's vector PDF,
--    the same Draw.io export the book's PDF uses) becomes a float with that PDF and its alt text as an unnumbered caption;
--  * inline code is wrapped in \aacode (defined in instructor.tex) so a long formula can break at the line's end;
--  * every table gets column widths from its content, because pandoc leaves a pipe table whose lines are short
--    unwrapped, and gives equal widths to one whose lines are long;
--  * a heading, a short bold label ("**What students should see.**") or a table asks for the room of its first lines
--    (\Needspace), counting what follows the heading or label, so none of them ends a page alone; and a heading is
--    preceded by \FloatBarrier, so a waiting figure is set before the next section starts instead of pages later.
-- Metadata: figure-dir (the folder of <unit folder>/<id>.pdf).
if not FORMAT:match('latex') then
  return {}
end

local figure_dir

local function file_exists(path)
  local file = io.open(path, 'rb')
  if file then
    file:close()
    return true
  end
  return false
end

local function stringify(meta, key)
  if meta[key] then return pandoc.utils.stringify(meta[key]) end
  return nil
end

local read_meta = {
  Meta = function(meta)
    figure_dir = stringify(meta, 'figure-dir')
  end,
}

local function latex_text(inlines)
  local text = pandoc.write(pandoc.Pandoc({pandoc.Plain(inlines)}), 'latex')
  return (text:gsub('%s+$', ''))
end

-- A table's column widths: each column asks for its longest word (so identifiers do not overflow) and for its
-- longest cell up to a cap; what the line can hold (about 100 characters of small type) is shared by preference.
local LINE = 100
local CAP = 64

local function column_widths(tbl)
  local n = #tbl.colspecs
  local longest, word = {}, {}
  for i = 1, n do longest[i], word[i] = 0, 0 end
  local function scan(rows)
    for _, row in ipairs(rows) do
      for i, cell in ipairs(row.cells) do
        if i <= n then
          local text = pandoc.utils.stringify(cell.contents)
          if #text > longest[i] then longest[i] = #text end
          for w in text:gmatch('%S+') do
            if #w > word[i] then word[i] = #w end
          end
        end
      end
    end
  end
  scan(tbl.head.rows)
  for _, body in ipairs(tbl.bodies) do scan(body.body) end
  scan(tbl.foot.rows)
  local need, want, total_need, total_want = {}, {}, 0, 0
  for i = 1, n do
    need[i] = math.min(word[i], 34) + 2
    want[i] = math.max(need[i], math.min(longest[i], CAP) + 2)
    total_need, total_want = total_need + need[i], total_want + want[i]
  end
  local weights = {}
  if total_want <= LINE then
    for i = 1, n do weights[i] = want[i] end
  elseif total_need < LINE then
    local spare = LINE - total_need
    for i = 1, n do weights[i] = need[i] + spare * (want[i] - need[i]) / math.max(total_want - total_need, 1) end
  else
    for i = 1, n do weights[i] = need[i] end
  end
  local sum = 0
  for i = 1, n do sum = sum + weights[i] end
  local widths = {}
  for i = 1, n do widths[i] = weights[i] / sum end
  return widths
end

local main = {
  Para = function(el)
    if #el.content ~= 1 or el.content[1].t ~= 'Image' then return nil end
    local img = el.content[1]
    local folder, id = img.src:match('figures/([^/]+)/(IF%-[%w%-]+)%.pdf$')
    if not folder or not figure_dir then return nil end
    local path = figure_dir .. '/' .. folder .. '/' .. id .. '.pdf'
    if not file_exists(path) then return nil end
    local caption = latex_text(img.caption)
    return pandoc.RawBlock('latex',
      '\\begin{figure}[htbp]\n\\centering\n' ..
      '\\includegraphics[width=\\linewidth,height=0.72\\textheight,keepaspectratio]{"' .. path .. '"}\n' ..
      '\\caption*{' .. caption .. '}\n\\end{figure}')
  end,

  -- a code block asks for room first, so a short query does not start in the last lines of a page
  CodeBlock = function(block)
    return {pandoc.RawBlock('latex', '\\Needspace{6\\baselineskip}'), block}
  end,

  Code = function(code)
    return {pandoc.RawInline('latex', '\\aacode{'), code, pandoc.RawInline('latex', '}')}
  end,

  Table = function(tbl)
    if #tbl.colspecs < 2 then return nil end
    -- a table with an empty header row (the header table of each file) loses it, and its double rule
    local empty = #tbl.head.rows > 0
    for _, row in ipairs(tbl.head.rows) do
      for _, cell in ipairs(row.cells) do
        if pandoc.utils.stringify(cell.contents) ~= '' then empty = false end
      end
    end
    if empty then tbl.head.rows = {} end
    local widths = column_widths(tbl)
    for i, spec in ipairs(tbl.colspecs) do
      tbl.colspecs[i] = {spec[1], widths[i]}
    end
    return tbl
  end,
}

-- the printed lines a block needs at the top of its page: a table its head and first rows, a short list all of it
-- (so the last discussion question never sits alone on a page), anything else a few lines
local LIST_WHOLE = 14   -- a list of up to this many printed lines moves whole
local function first_lines(block)
  if block == nil then return 0 end
  if block.t == 'Table' then
    -- the head and the first two rows, each row as tall as its longest cell needs in its column (the widths are
    -- set by the table filter above); a tall first row, as in a grading table, needs more than a fixed few lines
    local total, counted = 2, 0
    for _, body in ipairs(block.bodies) do
      for _, row in ipairs(body.body) do
        if counted >= 2 then break end
        local lines = 1
        for i, cell in ipairs(row.cells) do
          local width = block.colspecs[i] and block.colspecs[i][2]
          if type(width) ~= 'number' then width = 1 / #row.cells end
          lines = math.max(lines, math.ceil(#pandoc.utils.stringify(cell.content or cell.contents) / math.max(width * 100, 8)))
        end
        total, counted = total + lines, counted + 1
      end
    end
    return total + 2   -- a table's rules and cell padding take more than its text lines
  end
  if block.t == 'CodeBlock' then
    -- a short block moves whole (its own \Needspace asks for six lines), so a label before it moves with it
    local n = select(2, block.text:gsub('\n', '\n')) + 1
    return (n <= LIST_WHOLE and n or 6) + 1
  end
  if block.t == 'BulletList' or block.t == 'OrderedList' then
    local total = 0
    for _, item in ipairs(block.content) do
      total = total + math.ceil(#pandoc.utils.stringify(item) / 95) + 0.3
    end
    total = math.ceil(total)
    if total <= LIST_WHOLE then return total end
  end
  return 3
end

-- a paragraph that is only a short bold label, such as "**Assignment bundles**" or "**Step 2. Plan the test.**"
local function is_label(block)
  return block ~= nil and block.t == 'Para' and #block.content >= 1 and block.content[1].t == 'Strong'
    and #pandoc.utils.stringify(block) <= 90
end

local function needspace(lines)
  return pandoc.RawBlock('latex', '\\Needspace{' .. lines .. '\\baselineskip}')
end

-- the next block that prints, past the raw LaTeX the filter above adds (the room a code block asks for)
local function content_at(blocks, j)
  while blocks[j] ~= nil and blocks[j].t == 'RawBlock' do j = j + 1 end
  return blocks[j]
end

local keep = {
  Blocks = function(blocks)
    local result, held = {}, false
    for i, block in ipairs(blocks) do
      local following = content_at(blocks, i + 1)
      if block.t == 'Header' and held then
        -- a heading right under another heading or a label: the room was asked for before the first of them
        held = 'heading'
      elseif block.t == 'Header' then
        table.insert(result, pandoc.RawBlock('latex', '\\FloatBarrier'))
        -- the heading, any headings and labels right under it, and the first lines of what follows them
        local wanted, j = 3, i + 1
        while blocks[j] ~= nil and (blocks[j].t == 'Header' or is_label(blocks[j])) do
          wanted, j = wanted + (blocks[j].t == 'Header' and 3 or 2), j + 1
        end
        table.insert(result, needspace(wanted + first_lines(content_at(blocks, j))))
        held = 'heading'
      elseif is_label(block) and following ~= nil and following.t ~= 'Header' then
        -- a label right under a heading was counted with it; a label after another label (a short Check line, then
        -- the next step's label) asks for its own room
        if held ~= 'heading' then table.insert(result, needspace(2 + first_lines(following))) end
        held = 'label'
      elseif block.t == 'Table' then
        if not held then table.insert(result, needspace(first_lines(block))) end
        held = false
      else
        held = false
      end
      table.insert(result, block)
    end
    return result
  end,
}

return {read_meta, main, keep}
