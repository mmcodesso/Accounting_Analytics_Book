-- Keep things that belong together on one page in the PDF (LaTeX output only; other formats are unchanged).
-- styles/book-pdf.tex sets \raggedbottom, so when something moves to the next page the space is left at the foot.
--
-- Multiple-choice questions: each question's bold number and stem ("**1.** Which ..."), then its options (an A-D
-- list), go in a samepage environment, so the stem never sits at the foot of a page with its options on the next,
-- and the options are never split. A question that does not fit moves whole to the next page.
--
-- Code blocks (the SQL queries, and the Excel, DAX and M formulas): they stay in the order of the text, because
-- they are steps of the tutorials, so they never float like figures and tables. Before each one, \aaNeedspace
-- (styles/book-pdf.tex) asks for room: a block of up to KEEP_LINES lines moves whole to the next page when the page
-- cannot hold it, and a longer block starts only where at least MIN_LINES lines fit. The short paragraph that
-- introduces a block ("a. Type and run the query below.", or the short last items of a list just before it) moves
-- with it, and so does a heading right before them, which would otherwise sit alone at the foot. Lines are counted
-- as printed: a code line longer than WRAP characters wraps (breaklines), a paragraph line holds about TEXT_LINE
-- characters, and PADDING_LINES lines are added for the shading's padding and the space around the block (the
-- lead-in adds one for the space after it), so the estimate errs on the side of moving the block.

local KEEP_LINES = 25
local MIN_LINES = 6
local WRAP = 75
local LEAD_CHARS = 300   -- a paragraph this short before a code block introduces it
local TEXT_LINE = 90
local HEADER_LINES = 3
local PADDING_LINES = 3  -- the shading's padding and the space around the block

local function is_question(block)
  if block.t ~= 'Para' or #block.content == 0 or block.content[1].t ~= 'Strong' then return false end
  return pandoc.utils.stringify(block.content[1]):match('^%d+%.$') ~= nil
end

local function is_options(block)
  return block ~= nil and block.t == 'OrderedList' and block.style == 'UpperAlpha'
end

local function length(text)
  return utf8.len(text) or #text
end

local function code_lines(code)
  local lines = 0
  for line in (code:gsub('\n+$', '') .. '\n'):gmatch('(.-)\n') do
    lines = lines + math.max(1, math.ceil(length(line) / WRAP))
  end
  return lines
end

local function is_lead(block)
  return block ~= nil and (block.t == 'Para' or block.t == 'Plain')
    and length(pandoc.utils.stringify(block)) <= LEAD_CHARS
end

function Blocks(blocks)
  if not FORMAT:match('latex') then return nil end
  local result, changed, i = {}, false, 1
  while i <= #blocks do
    local block = blocks[i]
    if is_question(block) and is_options(blocks[i + 1]) then
      -- samepage forbids breaks inside the list and at its end, so the page may break only at the
      -- explicit penalty after each question.
      for _, item in ipairs({pandoc.RawBlock('latex', '\\begin{samepage}'), block, blocks[i + 1],
                             pandoc.RawBlock('latex', '\\end{samepage}\n\\penalty0')}) do
        table.insert(result, item)
      end
      changed, i = true, i + 2
    else
      if block.t == 'CodeBlock' then
        local lines = code_lines(block.text)
        local wanted = (lines <= KEEP_LINES and lines or MIN_LINES) + PADDING_LINES
        local previous = blocks[i - 1]
        -- a list just before the block whose last items introduce it ("c. Type the query below.",
        -- "d. Record the result."): the short one-paragraph items at its end, LEAD_CHARS in all
        local first_item, chars = nil, 0
        if previous ~= nil and (previous.t == 'OrderedList' or previous.t == 'BulletList') then
          for k = #previous.content, 1, -1 do
            local item = previous.content[k]
            local text = #item == 1 and is_lead(item[1]) and length(pandoc.utils.stringify(item[1])) or nil
            if text == nil or chars + text > LEAD_CHARS then break end
            chars, first_item = chars + text, k
          end
        end
        if first_item ~= nil then
          -- ask for the room at the start of the first of those items, so they move with the code
          wanted = wanted + (#previous.content - first_item + 1) + math.ceil(chars / TEXT_LINE) + 1
          local item = previous.content[first_item]
          item:insert(1, pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
          previous.content[first_item] = item
          result[#result] = previous
        else
          -- the blocks already in result that move with the code: its lead-in, and a heading before it
          local back = 0
          if is_lead(previous) then
            back = 1
            wanted = wanted + math.ceil(length(pandoc.utils.stringify(previous)) / TEXT_LINE) + 1
          end
          if blocks[i - back - 1] ~= nil and blocks[i - back - 1].t == 'Header' then
            back = back + 1
            wanted = wanted + HEADER_LINES
          end
          table.insert(result, #result - back + 1,
                       pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
        end
        changed = true
      end
      table.insert(result, block)
      i = i + 1
    end
  end
  if changed then return pandoc.Blocks(result) end
end
