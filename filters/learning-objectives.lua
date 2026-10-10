-- The box around a chapter's learning objectives (::: {.learning-objectives}) outside HTML, where styles/book.scss
-- draws it: a blue-tinted panel with a blue bar on its left and the lead line in bold sans. The blocks inside (the
-- heading, the lead line, the list) stay as they are, so the heading keeps its place in each format's table of
-- contents. Keep the colors in step with .learning-objectives in book.scss.
--   PDF: the aaobjectives box of styles/book-pdf.tex.
--   EPUB: nothing here; styles/book-epub-head.html styles the section Pandoc makes of the div.
--   DOCX: a one-cell table in raw Word XML, the way Quarto draws its callouts, with the lead line in the
--         reference document's Objectives Lead style.

local BLUE, TINT, BORDER = '1A5276', 'EAF2F8', 'C9DCEA'

local DOCX_OPEN = [[<w:tbl><w:tblPr><w:tblStyle w:val="Table" /><w:tblW w:w="5000" w:type="pct" />
<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="]] .. BORDER .. [[" />
<w:left w:val="single" w:sz="24" w:space="0" w:color="]] .. BLUE .. [[" />
<w:bottom w:val="single" w:sz="4" w:space="0" w:color="]] .. BORDER .. [[" />
<w:right w:val="single" w:sz="4" w:space="0" w:color="]] .. BORDER .. [[" /></w:tblBorders>
<w:tblCellMar><w:top w:w="72" w:type="dxa" /><w:left w:w="216" w:type="dxa" /><w:bottom w:w="72" w:type="dxa" />
<w:right w:w="216" w:type="dxa" /></w:tblCellMar>
<w:tblLook w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="0" w:val="0000" />
</w:tblPr><w:tr><w:trPr><w:cantSplit /></w:trPr><w:tc><w:tcPr><w:tcW w:w="5000" w:type="pct" />
<w:shd w:val="clear" w:color="auto" w:fill="]] .. TINT .. [[" /></w:tcPr>]]

local DOCX_CLOSE = '</w:tc></w:tr></w:tbl>'

-- The first paragraph is the lead line ("After completing this chapter, you will be able to:").
local function with_lead(blocks, wrap)
  local done = false
  local result = pandoc.Blocks({})
  for _, block in ipairs(blocks) do
    if not done and block.t == 'Para' then
      result:insert(wrap(block))
      done = true
    else
      result:insert(block)
    end
  end
  return result
end

function Div(div)
  if not div.classes:includes('learning-objectives') then return nil end
  if FORMAT:match('latex') then
    local blocks = with_lead(div.content, function(para)
      local inlines = pandoc.Inlines({pandoc.RawInline('latex', '{\\sffamily\\bfseries ')})
      inlines:extend(para.content)
      inlines:insert(pandoc.RawInline('latex', '}'))
      return pandoc.Para(inlines)
    end)
    blocks:insert(1, pandoc.RawBlock('latex', '\\begin{aaobjectives}'))
    blocks:insert(pandoc.RawBlock('latex', '\\end{aaobjectives}'))
    return blocks
  end
  if FORMAT == 'docx' then
    local blocks = with_lead(div.content, function(para)
      return pandoc.Div({para}, pandoc.Attr('', {}, {['custom-style'] = 'Objectives Lead'}))
    end)
    blocks:insert(1, pandoc.RawBlock('openxml', DOCX_OPEN))
    blocks:insert(pandoc.RawBlock('openxml', DOCX_CLOSE))
    return blocks
  end
  return nil
end
