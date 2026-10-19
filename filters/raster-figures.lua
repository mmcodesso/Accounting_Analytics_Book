-- Swap Draw.io SVG figures for optimized PNG copies in the EPUB and the DOCX.
--
-- Draw.io's SVG files carry a PNG fallback for every text label, so they are large: Pandoc puts them into the
-- EPUB as they are and into the DOCX twice (the SVG and a PNG it makes from it). scripts/figure_raster.py makes
-- one optimized PNG per figure (outputs/ebook-figures/<name>.png, cached by a hash of the Draw.io source and the
-- settings of the ebook-figures block of _quarto.yml), and this filter points each figure at it. The HTML and the
-- PDF are left alone: the HTML keeps the SVG, and filters/pdf-figures.lua gives the PDF the vector PDF.
--
-- The filter asks the script for every figure the document uses, once, so a render of --to epub or --to docx
-- makes any PNG that is missing or out of date by itself (a cold cache takes about ten minutes, because Draw.io
-- renders each figure; python scripts/figure_raster.py ensure --all does it ahead of time, with progress).
-- A figure that cannot be made stops the render: nothing is left out.

-- AA_EBOOK_FIGURES=svg keeps the SVG diagrams in the EPUB and the DOCX, for a build to compare the optimized
-- files with (scripts/build_ebooks.py --baseline).
local function enabled()
  return os.getenv("AA_EBOOK_FIGURES") ~= "svg"
end

local function target_format()
  if quarto and quarto.doc and quarto.doc.is_format then
    return quarto.doc.is_format("epub") or quarto.doc.is_format("docx")
  end
  local format = FORMAT or ""
  return format:match("^epub") ~= nil or format == "docx"
end

local function project_root()
  if quarto and quarto.project and quarto.project.directory then
    return quarto.project.directory
  end
  return os.getenv("AA_PROJECT_ROOT") or pandoc.system.get_working_directory()
end

-- Ends the render with the message. Quarto replaces Lua's error() with a function that only prints and returns, and
-- its fail() is not visible to a project filter; assert() raises a real error in Quarto and in plain Pandoc.
local function stop(message)
  assert(false, message)
end

-- The first Python that starts: AA_PYTHON, QUARTO_PYTHON, python, python3.
local function find_python()
  local candidates = {}
  for _, name in ipairs({ "AA_PYTHON", "QUARTO_PYTHON" }) do
    local value = os.getenv(name)
    if value and value ~= "" then table.insert(candidates, value) end
  end
  table.insert(candidates, "python")
  table.insert(candidates, "python3")
  for _, candidate in ipairs(candidates) do
    if pcall(pandoc.pipe, candidate, { "--version" }, "") then
      return candidate
    end
  end
  stop("raster-figures.lua: Python was not found (tried " .. table.concat(candidates, ", ") ..
       "). Install Python and Pillow, numpy and PyYAML (python -m pip install -r scripts/requirements-ebook.txt), " ..
       "or set AA_PYTHON to the interpreter.")
end

local function file_exists(path)
  local file = io.open(path, "rb")
  if file then
    file:close()
    return true
  end
  return false
end

-- "../../visuals/svg/fig-01-01.svg" -> "../../", "fig-01-01"
local function figure_of(src)
  local prefix, name = src:match("^(.-)visuals/svg/([^/]+)%.svg$")
  return prefix, name
end

function Pandoc(doc)
  if not enabled() or not target_format() then
    return nil
  end

  local names, seen = {}, {}
  doc:walk({
    Image = function(image)
      local _, name = figure_of(image.src)
      if name and not seen[name] then
        seen[name] = true
        table.insert(names, name)
      end
      return nil
    end,
  })
  if #names == 0 then
    return nil
  end

  local root = project_root()
  local args = { root .. "/scripts/figure_raster.py", "--root", root, "ensure", "--porcelain" }
  for _, name in ipairs(names) do table.insert(args, name) end
  local ok, output = pcall(pandoc.pipe, find_python(), args, "")
  if not ok then
    stop("raster-figures.lua: the optimized figures could not be made.\n" .. tostring(output))
  end

  local paths = {}
  for line in output:gmatch("[^\r\n]+") do
    local name, path = line:match("^([^\t]+)\t(.+)$")
    if name then paths[name] = path end
  end

  return doc:walk({
    Image = function(image)
      local prefix, name = figure_of(image.src)
      if not name then
        return nil
      end
      local path = paths[name]
      if not path or not file_exists(root .. "/" .. path) then
        stop("raster-figures.lua: no optimized PNG for " .. name .. " (expected " .. tostring(path) .. ").")
      end
      image.src = prefix .. path
      return image
    end,
  })
end
