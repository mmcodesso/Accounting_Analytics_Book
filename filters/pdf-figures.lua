-- Swap Draw.io SVG figures for their vector PDF exports in LaTeX output.
--
-- scripts/export_drawio_svgs.py writes visuals/pdf/<name>.pdf next to each
-- visuals/svg/<name>.svg. Converting the SVG in the PDF build would rasterize
-- the figure text, so the PDF copy is used whenever it exists. Other formats
-- keep the SVG.

local function file_exists(path)
  local file = io.open(path, "rb")
  if file then
    file:close()
    return true
  end
  return false
end

function Image(el)
  if not quarto.doc.is_format("latex") then
    return nil
  end

  local prefix, name = el.src:match("^(.-)visuals/svg/([^/]+)%.svg$")
  if not name then
    return nil
  end

  local pdf = "visuals/pdf/" .. name .. ".pdf"
  if not file_exists(quarto.project.directory .. "/" .. pdf) then
    return nil
  end

  el.src = prefix .. pdf
  return el
end
