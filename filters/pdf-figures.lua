-- Swap Draw.io SVG figures for their vector PDF exports in LaTeX output.
--
-- scripts/export_drawio_svgs.py writes visuals/pdf/<name>.pdf next to each
-- visuals/svg/<name>.svg. Converting the SVG in the PDF build would rasterize
-- the figure text, so the PDF copy is used whenever it exists. Other formats
-- keep the SVG.
--
-- The print interiors (profiles print-color and print-bw, scripts/print/build.py)
-- use the recolored copies that scripts/print/recolor.py writes, in CMYK or gray,
-- to outputs/print/figures/<mode>/<name>.pdf. A missing copy stops the render,
-- because an RGB figure must never reach the printer.

local function file_exists(path)
  local file = io.open(path, "rb")
  if file then
    file:close()
    return true
  end
  return false
end

-- "cmyk" or "gray" when a print profile is active, nil otherwise.
local function print_mode()
  for _, profile in ipairs(quarto.project.profile or {}) do
    if profile == "print-color" then return "cmyk" end
    if profile == "print-bw" then return "gray" end
  end
  return nil
end

function Image(el)
  if not quarto.doc.is_format("latex") then
    return nil
  end

  local prefix, name = el.src:match("^(.-)visuals/svg/([^/]+)%.svg$")
  if not name then
    return nil
  end

  local mode = print_mode()
  if mode then
    local copy = "outputs/print/figures/" .. mode .. "/" .. name .. ".pdf"
    if not file_exists(quarto.project.directory .. "/" .. copy) then
      error("pdf-figures.lua: " .. copy .. " is missing; run python scripts/print/recolor.py")
    end
    el.src = prefix .. copy
    return el
  end

  local pdf = "visuals/pdf/" .. name .. ".pdf"
  if not file_exists(quarto.project.directory .. "/" .. pdf) then
    return nil
  end

  el.src = prefix .. pdf
  return el
end
