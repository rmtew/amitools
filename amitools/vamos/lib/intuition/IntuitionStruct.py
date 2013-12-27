from amitools.vamos.AmigaStruct import AmigaStruct

# This really belongs in graphics.
class TextAttrStruct(AmigaStruct):
  _name = "TextAttr"
  _format = [
    ('APTR', 'ta_Name'),
    ('UWORD', 'ta_YSize'),
    ('UBYTE', 'ta_Style'),
    ('UBYTE', 'ta_Flags'),
  #
  ]
TextAttrDef = TextAttrStruct()


class IntuiTextStruct(AmigaStruct):
  _name = "IntuiText"
  _format = [
    ('UBYTE','it_FrontPen'),
    ('UBYTE','it_BackPen'),
    ('UBYTE','it_DrawMode'),
    ('UBYTE','it_KludgeFill00'),
    ('WORD','it_LeftEdge'),
    ('WORD','it_TopEdge'),
    ('APTR','it_ITextFont'),
    ('APTR','it_IText'),
    ('APTR','it_NextText')
  ]
IntuiTextDef = IntuiTextStruct()
