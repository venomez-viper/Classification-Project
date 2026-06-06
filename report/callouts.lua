-- Wrap fenced Divs with class "keyfinding" or "caution" in matching LaTeX
-- environments for PDF output. For non-LaTeX writers (docx), the raw blocks
-- are dropped and the inner content is kept as ordinary paragraphs.
function Div(el)
  local cls = el.classes[1]
  if cls == "keyfinding" or cls == "caution" then
    local out = pandoc.List()
    if FORMAT:match("latex") then
      out:insert(pandoc.RawBlock("latex", "\\begin{" .. cls .. "}"))
      out:extend(el.content)
      out:insert(pandoc.RawBlock("latex", "\\end{" .. cls .. "}"))
    else
      out:extend(el.content)
    end
    return out
  end
end
