-- Keep each multiple-choice question on one page in the PDF: its bold number and stem ("**1.** Which ..."),
-- then its options (an A-D list), go in a samepage environment, so the stem never sits at the foot of a page
-- with its options on the next, and the options are never split. A question that does not fit moves whole to
-- the next page (styles/book-pdf.tex sets \raggedbottom, so the space is left at the foot). Other formats are
-- unchanged.

local function is_question(block)
  if block.t ~= 'Para' or #block.content == 0 or block.content[1].t ~= 'Strong' then return false end
  return pandoc.utils.stringify(block.content[1]):match('^%d+%.$') ~= nil
end

local function is_options(block)
  return block ~= nil and block.t == 'OrderedList' and block.style == 'UpperAlpha'
end

function Blocks(blocks)
  if not FORMAT:match('latex') then return nil end
  local result, changed, i = pandoc.Blocks({}), false, 1
  while i <= #blocks do
    if is_question(blocks[i]) and is_options(blocks[i + 1]) then
      -- samepage forbids breaks inside the list and at its end, so the page may break only at the
      -- explicit penalty after each question.
      result:extend({pandoc.RawBlock('latex', '\\begin{samepage}'), blocks[i], blocks[i + 1],
                     pandoc.RawBlock('latex', '\\end{samepage}\n\\penalty0')})
      changed, i = true, i + 2
    else
      result:insert(blocks[i])
      i = i + 1
    end
  end
  if changed then return result end
end
