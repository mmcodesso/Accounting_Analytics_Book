-- Opt-in teaching layouts and progressive disclosure for Reveal.
-- PowerPoint keeps the original block structure and all content editable.
local function has_class(block, name)
  return block.classes and block.classes:includes(name)
end

local function reveal_steps(blocks, rows_only)
  local step = 0
  local function mark(block)
    local current = step
    step = step + 1
    if current == 0 then return block end
    return pandoc.Div({block}, pandoc.Attr('', {'fragment'},
      {['data-fragment-index'] = tostring(current - 1)}))
  end
  local result = pandoc.List()
  for _, block in ipairs(blocks) do
    if block.t == 'Div' and has_class(block, 'persistent') then
      -- Qualifications and activity instructions remain visible at every step.
      result:insert(block)
    elseif rows_only and block.t == 'Table' then
      for _, body in ipairs(block.bodies) do
        for _, row in ipairs(body.body) do
          if step > 0 then
            row.classes:insert('fragment')
            row.attributes['data-fragment-index'] = tostring(step - 1)
          end
          step = step + 1
        end
      end
      result:insert(block)
    elseif rows_only then
      result:insert(block)
    elseif block.t == 'BulletList' or block.t == 'OrderedList' then
      for i, item in ipairs(block.content) do
        local current = step
        step = step + 1
        if current > 0 then
          block.content[i] = {pandoc.Div(item, pandoc.Attr('', {'fragment'},
            {['data-fragment-index'] = tostring(current - 1)}))}
        end
      end
      result:insert(block)
    elseif block.t == 'Div' and has_class(block, 'columns') then
      for _, column in ipairs(block.content) do
        if column.t == 'Div' and has_class(column, 'column') then
          if step > 0 then
            column.classes:insert('fragment')
            column.attributes['data-fragment-index'] = tostring(step - 1)
          end
          step = step + 1
        end
      end
      result:insert(block)
    else
      result:insert(mark(block))
    end
  end
  return result
end

function Pandoc(doc)
  if not quarto.doc.is_format('revealjs') then return doc end
  local result, heading, content = pandoc.List(), nil, pandoc.List()
  local function flush()
    if not heading then
      result:extend(content)
      content = pandoc.List()
      return
    end
    result:insert(heading)
    local visible, notes = pandoc.List(), pandoc.List()
    for _, block in ipairs(content) do
      if block.t == 'Div' and has_class(block, 'notes') then
        notes:insert(block)
      else
        visible:insert(block)
      end
    end
    if has_class(heading, 'stepwise') or has_class(heading, 'step-rows') then
      visible = reveal_steps(visible, has_class(heading, 'step-rows'))
    end
    if has_class(heading, 'balanced') then
      result:insert(pandoc.Div(visible, pandoc.Attr('', {'slide-body'})))
    else
      result:extend(visible)
    end
    result:extend(notes)
    content = pandoc.List()
  end
  for _, block in ipairs(doc.blocks) do
    if block.t == 'Header' and block.level <= 2 then
      flush()
      heading = block
    else
      content:insert(block)
    end
  end
  flush()
  doc.blocks = result
  return doc
end
