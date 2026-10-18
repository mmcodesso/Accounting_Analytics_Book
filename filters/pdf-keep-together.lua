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
-- with it, and so does a heading right before them, which would otherwise sit alone at the foot. When a tutorial
-- step's whole list of actions, or the one paragraph after its label, moves with the block, the step's label
-- ("**Step 5. ...**") moves too, so it never sits alone at the foot of a page either. So it does when the block sits
-- inside one of the step's first actions ("a. Type this formula in B28:" and the formula), where the room is asked
-- for before the label. Any other step label asks for room for itself and the first lines of its step
-- (\aaKeepLabel), so a label never ends a page with its actions on the next, and so does any paragraph that is only
-- a bold label, such as an exercise's title line or its "**Requirements.**" (with a heading right before it). Lines are counted
-- as printed: a code line longer than WRAP characters wraps (breaklines), a paragraph line holds about TEXT_LINE
-- characters, and PADDING_LINES lines are added for the shading's padding and the space around the block (the
-- lead-in adds one for the space after it), so the estimate errs on the side of moving the block.
--
-- Callout boxes (never split, see styles/book-pdf.tex): a tall one needs its room as well. A figure placed at the
-- top of a page leaves the text only a tenth of the page (\textfraction), and a box that cannot break and does not
-- fit overflows the page's foot, so a callout of CALLOUT_MIN lines or more asks for its estimated height first, like
-- a code block (a heading right before it moves with it): when the page cannot hold it, the break comes before
-- it, and the figures and tables still waiting are placed after it.
--
-- Section breaks that place the waiting floats first: a level-2 heading with the class new-page starts a new
-- page after \aaClearpageTop (styles/book-pdf.tex: \clearpage, with the floats left over stacked from the top of
-- their pages), so the figures and tables still waiting for room are set before it, never after it.
-- Quarto's {{< pagebreak >}} is a plain \newpage, which leaves them waiting: in the quick reference appendix
-- (almost all tables) the next group's heading and the references were printed between tables of the groups before.

local KEEP_LINES = 25
local MIN_LINES = 6
local WRAP = 75
local LEAD_CHARS = 300   -- a paragraph this short before a code block introduces it
local TEXT_LINE = 90
local HEADER_LINES = 3
local PADDING_LINES = 3  -- the shading's padding and the space around the block
local CALLOUT_LINE = 96     -- characters in a line inside a callout (the box is narrower than the text)
local CALLOUT_TITLE = 2     -- the title bar, in lines
local CALLOUT_PADDING = 1   -- the box's padding, in lines
local CALLOUT_MIN = 8       -- a shorter callout fits in the room a float leaves for text

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

-- Quarto hands a callout to this filter as a custom node: a Div with no callout class, holding a scaffold Div for
-- the title and another for the body
local function is_callout(block)
  return block.t == 'Div' and block.attributes['__quarto_custom_type'] == 'Callout'
end

-- printed lines of blocks inside a callout: a paragraph line holds CALLOUT_LINE characters, a block adds a
-- fraction of a line of space after it, and a list adds its items
local function text_lines(blocks)
  local lines = 0
  for _, inner in ipairs(blocks) do
    if inner.t == 'Header' then
      lines = lines + CALLOUT_TITLE
    elseif inner.t == 'CodeBlock' then
      lines = lines + code_lines(inner.text) + 1
    elseif inner.t == 'BulletList' or inner.t == 'OrderedList' then
      for _, item in ipairs(inner.content) do lines = lines + text_lines(item) end
    elseif inner.t == 'Div' then
      lines = lines + text_lines(inner.content)
    elseif inner.t == 'Para' or inner.t == 'Plain' then
      lines = lines + math.ceil(length(pandoc.utils.stringify(inner)) / CALLOUT_LINE) + 0.4
    else
      lines = lines + 2
    end
  end
  return lines
end

local function starts_page(block)
  return block ~= nil and block.t == 'Header' and block.level == 2 and block.classes:includes('new-page')
end

local function is_lead(block)
  return block ~= nil and (block.t == 'Para' or block.t == 'Plain')
    and length(pandoc.utils.stringify(block)) <= LEAD_CHARS
end

-- a tutorial step's label ("**Step 5. Create the role.**", with at most a short sentence after it)
local function is_step_label(block)
  return block ~= nil and block.t == 'Para' and #block.content > 0 and block.content[1].t == 'Strong'
    and pandoc.utils.stringify(block.content[1]):match('^Step %d+%.') ~= nil
    and length(pandoc.utils.stringify(block)) <= LEAD_CHARS
end

-- a paragraph that is only a bold label, such as an exercise's "**Requirements.**" or its title line
-- ("**Exercise 1.6: Evaluating Journal Entry Data for Audit Purposes**")
local function is_bold_label(block)
  return block ~= nil and block.t == 'Para' and #block.content == 1 and block.content[1].t == 'Strong'
    and length(pandoc.utils.stringify(block)) <= LEAD_CHARS
end

-- the bold line that opens a tutorial's steps ("**Step-by-step instructions.**")
local function is_instructions(block)
  return block ~= nil and block.t == 'Para' and #block.content > 0 and block.content[1].t == 'Strong'
    and pandoc.utils.stringify(block):match('^Step%-by%-step instructions%.$') ~= nil
end

-- the printed lines from the start of a step's list of actions to the first lines of a code block inside one of
-- its first actions ("a. On the Analysis worksheet, enter this formula in B28:" and the formula), when the text
-- before the block is short (LEAD_CHARS); nil when no such block opens the list
local function nested_code_lines(list)
  if list == nil or (list.t ~= 'OrderedList' and list.t ~= 'BulletList') then return nil end
  local lines, chars = 0, 0
  for k, item in ipairs(list.content) do
    if k > 3 then return nil end
    for _, inner in ipairs(item) do
      if inner.t == 'CodeBlock' then
        local n = code_lines(inner.text)
        return lines + (n <= KEEP_LINES and n or MIN_LINES) + PADDING_LINES
      elseif inner.t ~= 'RawBlock' then
        if not is_lead(inner) then return nil end
        local text = length(pandoc.utils.stringify(inner))
        chars = chars + text
        if chars > LEAD_CHARS then return nil end
        lines = lines + math.ceil(text / TEXT_LINE) + 1
      end
    end
  end
  return nil
end

local LABEL_FOLLOW = 3   -- lines of a step's first action that must fit on the page with its label

function Blocks(blocks)
  if not FORMAT:match('latex') then return nil end
  local result, changed, i = {}, false, 1
  while i <= #blocks do
    local block = blocks[i]
    if starts_page(block) then
      table.insert(result, pandoc.RawBlock('latex', '\\aaClearpageTop'))
      table.insert(result, block)
      changed, i = true, i + 1
    elseif is_question(block) and is_options(blocks[i + 1]) then
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
        if first_item == 1 and is_step_label(blocks[i - 2]) and is_step_label(result[#result - 1]) then
          -- the whole list moves with the code, so the tutorial step's label just before it moves too, rather
          -- than sit alone at the foot of the page
          wanted = wanted + #previous.content + math.ceil(chars / TEXT_LINE) + 1
                   + math.ceil(length(pandoc.utils.stringify(blocks[i - 2])) / TEXT_LINE) + 1
          table.insert(result, #result - 1, pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
        elseif first_item == 1 and is_bold_label(blocks[i - 2]) and not is_instructions(blocks[i - 2]) then
          -- the same for any other bold label right before that list (Exercise 6.6's "Requirements." before its
          -- first requirement and that requirement's formula): the room is asked for before the label
          wanted = wanted + #previous.content + math.ceil(chars / TEXT_LINE) + 1
                   + math.ceil(length(pandoc.utils.stringify(blocks[i - 2])) / TEXT_LINE) + 1
          local at = #result
          while at > 1 and result[at] ~= blocks[i - 2] do at = at - 1 end
          table.insert(result, at, pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
        elseif first_item ~= nil then
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
            if not is_step_label(previous) and is_step_label(blocks[i - 2]) then
              -- a step whose only action is the lead-in: its label moves with it
              back = 2
              wanted = wanted + math.ceil(length(pandoc.utils.stringify(blocks[i - 2])) / TEXT_LINE) + 1
            end
          end
          if blocks[i - back - 1] ~= nil and blocks[i - back - 1].t == 'Header' then
            back = back + 1
            wanted = wanted + HEADER_LINES
          end
          table.insert(result, #result - back + 1,
                       pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
        end
        changed = true
      elseif is_step_label(block) and blocks[i + 1] ~= nil and blocks[i + 1].t ~= 'CodeBlock' then
        -- a step label (a label right before a code block is handled with the block): room for the label and
        -- the start of its step, or, when a code block sits in its first actions, for everything up to the block
        local wanted = math.ceil(length(pandoc.utils.stringify(block)) / TEXT_LINE) + 1
        local nested = nested_code_lines(blocks[i + 1])
        local macro = nested ~= nil and 'aaNeedspace' or 'aaKeepLabel'
        wanted = wanted + (nested or LABEL_FOLLOW)
        local back = 0
        local before = blocks[i - 1]
        if before ~= nil and before.t == 'Header' then
          back, wanted = 1, wanted + HEADER_LINES
        elseif is_instructions(before) then
          back, wanted = 1, wanted + 2
        end
        table.insert(result, #result - back + 1,
                     pandoc.RawBlock('latex', '\\' .. macro .. '{' .. wanted .. '\\baselineskip}'))
        changed = true
      elseif is_bold_label(block) and not is_instructions(block) and blocks[i + 1] ~= nil
          and blocks[i + 1].t ~= 'CodeBlock' and blocks[i + 1].t ~= 'Header' then
        -- any other bold label line: room for it and the first lines after it, like a step label, or, when a code
        -- block sits in the first items of the list after it (Exercise 6.6's "(1) ..." and its formula), room for
        -- everything up to the block, which would otherwise take its lead-in to the next page and leave the label
        local wanted = math.ceil(length(pandoc.utils.stringify(block)) / TEXT_LINE) + 1
        local nested = nested_code_lines(blocks[i + 1])
        local macro = nested ~= nil and 'aaNeedspace' or 'aaKeepLabel'
        wanted = wanted + (nested or LABEL_FOLLOW)
        local back = 0
        if blocks[i - 1] ~= nil and blocks[i - 1].t == 'Header' then
          back, wanted = 1, wanted + HEADER_LINES
        end
        table.insert(result, #result - back + 1,
                     pandoc.RawBlock('latex', '\\' .. macro .. '{' .. wanted .. '\\baselineskip}'))
        -- and no break right after it: a list that follows would otherwise invite one (LaTeX's \@beginparpenalty)
        table.insert(result, block)
        block = pandoc.RawBlock('latex', '\\aaNoBreakAfter')
        changed = true
      elseif is_callout(block) then
        local wanted = math.ceil(text_lines(block.content)) + CALLOUT_PADDING
        if wanted >= CALLOUT_MIN then
          local back = 0
          if blocks[i - 1] ~= nil and blocks[i - 1].t == 'Header' then
            back = 1
            wanted = wanted + HEADER_LINES
          end
          table.insert(result, #result - back + 1,
                       pandoc.RawBlock('latex', '\\aaNeedspace{' .. wanted .. '\\baselineskip}'))
          changed = true
        end
      end
      table.insert(result, block)
      i = i + 1
    end
  end
  if changed then return pandoc.Blocks(result) end
end
