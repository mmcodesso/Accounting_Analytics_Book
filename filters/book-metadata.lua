-- The book's metadata for catalogs, search engines and stores, in each format (book-pages.lua prints the title and
-- copyright pages). Every value comes from _quarto.yml: book (title, the author with the ORCID iD, ISNI, ROR ID and
-- faculty page, date, site-url), isbn, doi, indexing (summary, keywords, audience, BISAC codes), citation (publisher,
-- language), license, copyright and image; the edition and the revision come from _variables.yml.
--   HTML: every page links its license (<link rel="license">, which search engines read as its terms of reuse). The
--         homepage also carries the book as schema.org structured data (JSON-LD: the book with one edition per ISBN,
--         its author with the ORCID iD and ISNI, its publisher and subjects, and the website), and the two Google
--         Scholar tags that Quarto's own (google-scholar in index.qmd) leave out for a book: keywords and publisher.
--   EPUB: the long description, the BISAC subjects (Quarto's schema takes a single subject), and the author's name as
--         catalogs sort it (Codesso, Mauricio). book-pages.lua writes the identifiers (ISBN, DOI).
--   DOCX: the long description, the file's Comments.
--   PDF:  the digital PDF's language (/Lang, set without babel, which would change the line breaks) and its XMP
--         metadata, through hyperxmp: copyright and license, publisher, ISBN, DOI, edition, revision, website and the
--         author's ORCID iD. The print interiors (print: true) keep only the document properties, as Ghostscript
--         rewrites their metadata for PDF/X.

local function is_format(name)
  if name == 'latex' then return FORMAT:match('latex') ~= nil end
  if name == 'epub' then return FORMAT:match('^epub') ~= nil end
  if name == 'html' then return FORMAT:match('^html') ~= nil end
  return FORMAT == name
end

-- A metadata value as plain text, or nil when it is missing or blank.
local function text(value)
  if value == nil then return nil end
  local result = pandoc.utils.stringify(value):gsub('^%s+', ''):gsub('%s+$', '')
  if result == '' then return nil end
  return result
end

-- A metadata value as a list (a single value becomes a list of one).
local function list(value)
  if value == nil then return {} end
  if pandoc.utils.type(value) == 'List' then return value end
  return {value}
end

local function texts(value)
  local result = {}
  for _, item in ipairs(list(value)) do
    local item_text = text(item)
    if item_text then result[#result + 1] = item_text end
  end
  return result
end

-- A key of a metadata map, or nil when the value is not a map (a string, inlines, a list or a boolean).
local function field(map, key)
  local kind = pandoc.utils.type(map)
  if kind ~= 'table' and kind ~= 'Meta' then return nil end
  return map[key]
end

-- The book --------------------------------------------------------------------------------------------------------

-- The ISBNs in the order the structured data lists the editions, with each edition's schema.org format.
local EDITIONS = {
  {key = 'pdf', format = 'EBook', encoding = 'application/pdf', label = 'PDF'},
  {key = 'epub', format = 'EBook', encoding = 'application/epub+zip', label = 'EPUB'},
  {key = 'paperback-color', format = 'Paperback', label = 'paperback, color'},
  {key = 'paperback-bw', format = 'Paperback', label = 'paperback, black and white'},
  {key = 'hardcover', format = 'Hardcover', label = 'hardcover'},
}

local function read_book(meta)
  local book = meta.book or {}
  local indexing = meta.indexing or {}
  local citation = meta.citation or {}
  local vars = meta['_quarto-vars'] or {}
  local site = text(field(book, 'site-url'))
  if site then site = site:gsub('/*$', '/') end
  local edition = text(field(field(vars, 'book'), 'edition'))
  local info = {
    title = text(field(book, 'title')) or text(meta.title),
    site = site,
    -- book.date, as typed (Quarto turns citation.issued into CSL date parts).
    date = text(field(book, 'date')) or text(meta.date),
    language = text(field(citation, 'language')) or 'en-US',
    publisher = text(field(citation, 'publisher')),
    summary = text(field(indexing, 'summary')),
    keywords = texts(field(indexing, 'keywords')),
    audience = texts(field(indexing, 'audience')),
    levels = texts(field(indexing, 'educational-level')),
    resource_type = text(field(indexing, 'resource-type')),
    bisac = {},
    edition = edition and (edition:gsub('^%l', string.upper) .. ' edition'),
    revision = text(field(field(vars, 'book'), 'revision')),
    doi = text(meta.doi),
    license = text(field(meta.license, 'link')),
    license_text = text(field(meta.license, 'text')),
    holder = text(field(meta.copyright, 'holder')),
    year = text(field(meta.copyright, 'year')),
    image = text(meta.image),
    isbns = {},
    authors = {},
  }
  for _, subject in ipairs(list(field(indexing, 'bisac'))) do
    info.bisac[#info.bisac + 1] = {code = text(field(subject, 'code')), heading = text(field(subject, 'heading'))}
  end
  for _, edition_info in ipairs(EDITIONS) do
    local isbn = text(field(meta.isbn, edition_info.key))
    if isbn then info.isbns[#info.isbns + 1] = {isbn = isbn, edition = edition_info} end
  end
  info.pdf_isbn = text(field(meta.isbn, 'pdf'))
  for _, author in ipairs(list(field(book, 'author'))) do
    local name = text(field(author, 'name')) or text(author)
    local given, family = name:match('^(.-)%s+(%S+)$')
    local person = {name = name, given = given, family = family, orcid = text(field(author, 'orcid')),
                    isni = text(field(author, 'isni')), url = text(field(author, 'url')), affiliations = {}}
    if person.isni then person.isni = person.isni:gsub('%s', '') end
    for _, affiliation in ipairs(list(field(author, 'affiliations'))) do
      person.affiliations[#person.affiliations + 1] = {
        name = text(field(affiliation, 'name')) or text(affiliation), department = text(field(affiliation, 'department')),
        city = text(field(affiliation, 'city')), region = text(field(affiliation, 'region')),
        country = text(field(affiliation, 'country')), ror = text(field(affiliation, 'ror'))}
    end
    info.authors[#info.authors + 1] = person
  end
  return info
end

-- JSON with its keys in a fixed order: object{{key, value}, ...} keeps the order, and a nil value leaves its key out.

local Object = {}
local function object(fields) return setmetatable(fields, Object) end

local function nonempty(items) if #items > 0 then return items end return nil end

local JSON_ESCAPES = {['"'] = '\\"', ['\\'] = '\\\\', ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t'}

-- A JSON string that is also safe inside a <script> element (no <, > or & as such).
local function json_string(value)
  return '"' .. value:gsub('[%c"\\<>&]', function(char)
    return JSON_ESCAPES[char] or string.format('\\u%04x', char:byte())
  end) .. '"'
end

local function json(value)
  local kind = type(value)
  if kind == 'string' then return json_string(value) end
  if kind == 'boolean' then return value and 'true' or 'false' end
  if kind == 'number' then return tostring(math.tointeger(value) or value) end
  local parts = {}
  if getmetatable(value) == Object then
    for _, pair in ipairs(value) do
      if pair[2] ~= nil then parts[#parts + 1] = json_string(pair[1]) .. ': ' .. json(pair[2]) end
    end
    return '{' .. table.concat(parts, ', ') .. '}'
  end
  for _, item in ipairs(value) do parts[#parts + 1] = json(item) end
  return '[' .. table.concat(parts, ', ') .. ']'
end

local function reference(id) return object({{'@id', id}}) end

local function organization(affiliation)
  local address = nil
  if affiliation.city or affiliation.region or affiliation.country then
    address = object({{'@type', 'PostalAddress'}, {'addressLocality', affiliation.city},
                      {'addressRegion', affiliation.region}, {'addressCountry', affiliation.country}})
  end
  local institution = object({{'@type', 'Organization'}, {'name', affiliation.name}, {'sameAs', affiliation.ror},
                              {'address', address}})
  if not affiliation.department then return institution end
  return object({{'@type', 'Organization'}, {'name', affiliation.department}, {'parentOrganization', institution}})
end

local function person_node(person, id)
  local same_as, identifiers, affiliations = {}, {}, {}
  if person.orcid then
    same_as[#same_as + 1] = 'https://orcid.org/' .. person.orcid
    identifiers[#identifiers + 1] = object({{'@type', 'PropertyValue'}, {'propertyID', 'ORCID'}, {'value', person.orcid}})
  end
  if person.isni then
    same_as[#same_as + 1] = 'https://isni.org/isni/' .. person.isni
    identifiers[#identifiers + 1] = object({{'@type', 'PropertyValue'}, {'propertyID', 'ISNI'}, {'value', person.isni}})
  end
  for _, affiliation in ipairs(person.affiliations) do affiliations[#affiliations + 1] = organization(affiliation) end
  return object({{'@type', 'Person'}, {'@id', id}, {'name', person.name}, {'givenName', person.given},
                 {'familyName', person.family}, {'url', person.url}, {'sameAs', nonempty(same_as)},
                 {'identifier', nonempty(identifiers)}, {'affiliation', nonempty(affiliations)}})
end

local function structured_data(info)
  local site = info.site
  local book_id, publisher_id = site .. '#book', site .. '#publisher'
  local graph, author_refs, editions, subjects, audience = {}, {}, {}, {}, {}
  for i, person in ipairs(info.authors) do
    local id = site .. '#author' .. (i > 1 and ('-' .. i) or '')
    author_refs[#author_refs + 1] = reference(id)
    graph[#graph + 1] = person_node(person, id)
  end
  for _, entry in ipairs(info.isbns) do
    editions[#editions + 1] = object({{'@type', 'Book'}, {'name', info.title .. ' (' .. entry.edition.label .. ')'},
      {'isbn', entry.isbn}, {'bookFormat', 'https://schema.org/' .. entry.edition.format},
      {'encodingFormat', entry.edition.encoding}, {'bookEdition', info.edition}, {'inLanguage', info.language}})
  end
  for _, subject in ipairs(info.bisac) do
    subjects[#subjects + 1] = object({{'@type', 'DefinedTerm'}, {'name', subject.heading}, {'termCode', subject.code},
      {'inDefinedTermSet', object({{'@type', 'DefinedTermSet'}, {'name', 'BISAC Subject Headings'}})}})
  end
  for _, role in ipairs(info.audience) do
    audience[#audience + 1] = object({{'@type', 'EducationalAudience'}, {'educationalRole', role}})
  end
  local holder = nil
  if info.holder then
    holder = (info.authors[1] and info.authors[1].name == info.holder) and author_refs[1]
             or object({{'@type', 'Person'}, {'name', info.holder}})
  end
  local doi_url = info.doi and ('https://doi.org/' .. info.doi)
  local publisher = nil
  if info.publisher then
    publisher = reference(publisher_id)
    graph[#graph + 1] = object({{'@type', 'Organization'}, {'@id', publisher_id}, {'name', info.publisher}})
  end
  table.insert(graph, 1, object({
    {'@type', 'Book'}, {'@id', book_id}, {'name', info.title}, {'url', site},
    {'description', info.summary}, {'author', nonempty(author_refs)}, {'publisher', publisher},
    {'datePublished', info.date}, {'copyrightYear', info.year and tonumber(info.year)}, {'copyrightHolder', holder},
    {'license', info.license}, {'isAccessibleForFree', true}, {'inLanguage', info.language},
    {'bookEdition', info.edition}, {'version', info.revision},
    {'image', info.image and (site .. info.image:gsub('^/', ''))},
    {'identifier', info.doi and object({{'@type', 'PropertyValue'}, {'propertyID', 'DOI'}, {'value', info.doi}})},
    {'sameAs', doi_url}, {'keywords', nonempty(info.keywords)}, {'about', nonempty(subjects)},
    {'learningResourceType', info.resource_type}, {'educationalLevel', nonempty(info.levels)},
    {'audience', nonempty(audience)}, {'workExample', nonempty(editions)}}))
  graph[#graph + 1] = object({{'@type', 'WebSite'}, {'@id', site .. '#website'}, {'url', site}, {'name', info.title},
    {'inLanguage', 'en'}, {'publisher', publisher}, {'about', reference(book_id)}})
  return json(object({{'@context', 'https://schema.org'}, {'@graph', graph}}))
end

-- HTML ------------------------------------------------------------------------------------------------------------

local function attribute(value)
  return (value:gsub('&', '&amp;'):gsub('"', '&quot;'):gsub('<', '&lt;'):gsub('>', '&gt;'))
end

-- The homepage is index.qmd at the project's root (paths compared without regard to case, for Windows drive letters).
local function is_homepage()
  local input = quarto.doc.input_file
  local root = quarto.project and quarto.project.directory
  if not input or not root then return false end
  return pandoc.path.normalize(input):lower() == pandoc.path.normalize(pandoc.path.join({root, 'index.qmd'})):lower()
end

local function html_metadata(info)
  local head = {}
  if info.license then head[#head + 1] = '<link rel="license" href="' .. attribute(info.license) .. '">' end
  if is_homepage() and info.site then
    if info.publisher then
      head[#head + 1] = '<meta name="citation_publisher" content="' .. attribute(info.publisher) .. '">'
    end
    if #info.keywords > 0 then
      head[#head + 1] = '<meta name="citation_keywords" content="' .. attribute(table.concat(info.keywords, '; ')) .. '">'
    end
    head[#head + 1] = '<script type="application/ld+json">' .. structured_data(info) .. '</script>'
  end
  if #head > 0 then quarto.doc.include_text('in-header', table.concat(head, '\n')) end
end

-- EPUB and DOCX ---------------------------------------------------------------------------------------------------

local function epub_metadata(doc, info)
  if info.summary then doc.meta.description = pandoc.MetaString(info.summary) end
  local subjects = pandoc.MetaList({})
  for _, subject in ipairs(info.bisac) do
    subjects:insert(pandoc.MetaMap({text = pandoc.MetaString(subject.heading), authority = pandoc.MetaString('BISAC'),
                                    term = pandoc.MetaString(subject.code)}))
  end
  if #subjects > 0 then doc.meta.subject = subjects end
  local creators = pandoc.MetaList({})
  for _, person in ipairs(info.authors) do
    local entry = {text = pandoc.MetaString(person.name), role = pandoc.MetaString('aut')}
    if person.family then entry['file-as'] = pandoc.MetaString(person.family .. ', ' .. person.given) end
    creators:insert(pandoc.MetaMap(entry))
  end
  if #creators > 0 then doc.meta.creator = creators end
end

-- PDF -------------------------------------------------------------------------------------------------------------

-- A value for \hypersetup inside the \def below. hyperxmp drops \_ and its kin from its keys, so each special
-- character goes in as \string and the character (# doubled for the \def); a backslash or a brace, which no DOI, URL or
-- name here holds, is left out rather than garbled.
local LATEX_ESCAPES = {['_'] = '\\string_', ['&'] = '\\string&', ['#'] = '\\string##', ['$'] = '\\string$',
                       ['~'] = '\\string~', ['^'] = '\\string^', ['%'] = '\\@percentchar ', ['\\'] = '', ['{'] = '',
                       ['}'] = ''}

local function latex_text(value)
  return (value:gsub('[\\{}#$%%&_~^]', LATEX_ESCAPES))
end

-- hyperxmp needs hyperref, which Quarto's template loads after the header, so both settings wait for it. keeppdfinfo
-- keeps the Author and Keywords of the document properties, which hyperxmp otherwise moves into the XMP alone. The
-- keywords are set here rather than through Quarto's `keywords`, whose \xmpquote would print each one in quotes.
local function pdf_metadata(info)
  local keys = {'keeppdfinfo', 'pdfpubtype={book}'}
  local function add(key, value) if value then keys[#keys + 1] = key .. '={' .. latex_text(value) .. '}' end end
  if #info.keywords > 0 then add('pdfkeywords', table.concat(info.keywords, ', ')) end
  if info.holder and info.year then
    add('pdfcopyright', 'Copyright © ' .. info.year .. ' ' .. info.holder .. '.'
        .. (info.license_text and (' Licensed under the ' .. info.license_text .. '.') or ''))
  end
  add('pdflicenseurl', info.license)
  add('pdfpublisher', info.publisher)
  add('pdfurl', info.site)
  add('pdfisbn', info.pdf_isbn)
  add('pdfdoi', info.doi)
  add('pdfidentifier', info.doi and ('https://doi.org/' .. info.doi)
      or (info.pdf_isbn and ('urn:isbn:' .. info.pdf_isbn:gsub('[%s%-]', ''))))
  add('pdfbookedition', info.edition)
  add('pdfversionid', info.revision)
  add('pdfcontacturl', info.authors[1] and info.authors[1].orcid and ('https://orcid.org/' .. info.authors[1].orcid))
  quarto.doc.include_text('in-header', table.concat({
    '% The digital PDF\'s language and XMP metadata (filters/book-metadata.lua), set once hyperref is loaded.',
    '\\makeatletter',
    '\\def\\aa@pdfmetadata{\\hypersetup{pdflang={' .. latex_text(info.language) .. '}}\\RequirePackage{hyperxmp}%',
    '  \\hypersetup{' .. table.concat(keys, ', ') .. '}}',
    '\\@ifpackageloaded{hyperref}{\\aa@pdfmetadata}{\\AddToHook{package/hyperref/after}{\\aa@pdfmetadata}}',
    '\\makeatother'}, '\n'))
end

-- The filter ------------------------------------------------------------------------------------------------------

return {
  {Pandoc = function(doc)
    local info = read_book(doc.meta)
    if is_format('html') then
      html_metadata(info)
    elseif is_format('epub') then
      epub_metadata(doc, info)
    elseif is_format('docx') then
      if info.summary then doc.meta.description = pandoc.MetaString(info.summary) end
    elseif is_format('latex') and not doc.meta.print then
      pdf_metadata(info)
    end
    return doc
  end},
}
