-- Pandoc Lua filters for the instructor PDFs (facts/instructor/guides.py pdf), LaTeX output only.
--
--  * a paragraph that is one image of a built figure (../figures/<unit folder>/IF-06-1-A.pdf, the figure's vector PDF,
--    the same Draw.io export the book's PDF uses) becomes a float with that PDF and its alt text as an unnumbered caption;
--  * inline code is wrapped in \aacode (defined in instructor.tex) so a long formula can break at the line's end;
--  * every table gets column widths from its content, because pandoc leaves a pipe table whose lines are short
--    unwrapped, and gives equal widths to one whose lines are long.
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

return {read_meta, main}
