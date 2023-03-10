
MACRO_OPS_1 = r"""
Application.ExecuteCommand("Display Colors")
DlgDisplayColors.DefaultPalette.Click()
DlgDisplayColors.Apply.Click()
DlgDisplayColors.Ok.Click()
"""

MACRO_OPS_2 = r"""
Application.CreatePDF("${pdf_file}")
DlgPDFOut.StartAcrobat = ${enable_open_pdf}
DlgPDFOut.HyperlinksAttr = ${enable_hyperlinks_attr}
DlgPDFOut.HyperlinksNets = ${enable_hyperlinks_nets}
DlgPDFOut.ColorSchemeSetting = ${color_scheme_setting}
DlgPDFOut.Ok.Click()
"""
