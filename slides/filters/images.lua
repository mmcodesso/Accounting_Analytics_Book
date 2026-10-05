-- The same image authority supplies browser SVG and high-resolution PPTX PNG.
function Image(image)
  if quarto.doc.is_format('pptx') and image.src:match('%.svg$') then
    local png = image.src:gsub('%.svg$', '.png')
    local path = png
    if png:sub(1, 1) == '/' then path = quarto.project.directory .. png end
    local file = io.open(path, 'rb')
    if not file then error('Missing prepared PowerPoint image: ' .. png) end
    file:close()
    image.src = png
  end
  return image
end
