
PPCB_EXPORT_PDF_TOP_SILK_PDC = 'ppcb-export-pdf-top-silk-pdc'
PPCB_EXPORT_PDF_BOT_SILK_PDC = 'ppcb-export-pdf-bot-silk-pdc'
PPCB_EXPORT_PDF_MID_LAYER_PDC = 'ppcb-export-pdf-mid-layer-pdc'
PPCB_EXPORT_PDF_DRAWING_PDC  = 'ppcb-export-pdf-drill-drawing-pdc'

MACRO_OPS_1 = r"""
Application.ExecuteCommand("Display Colors Setup")
DisplayColorsSetupDlg.ApplyImmediately = false
DisplayColorsSetupDlg.DefaultPalette.Click()
DisplayColorsSetupDlg.Apply.Click()
DisplayColorsSetupDlg.Ok.Click()
"""

MACRO_OPS_2 = r"""
Application.ExecuteCommand("PDF Config")
PDFConfig.OpenPDF = ${enable_open_pdf}
PDFConfig.Tree.Select("PDF Document")
PDFConfig.Import.ChooseFile("${pdc_file}")
PDFConfig.Generate.ChooseFile("${pdf_file}")
PDFConfig.Cancel.Click()
DlgPrompt.Question("Do you want to save the changes ?").Answer(mbNo)
"""

MACRO_OPS_3 = r"""
Application.ExecuteCommand("Pour Manager")
PourManagerDlg.Tabs = "Flood"
PourManagerDlg.Ok.Click()
DlgPrompt.Question("Proceed with flood?").Answer(mbYes)
PourManagerDlg.Cancel.Click()
"""

MACRO_OPS_4 = r"""
Application.ExportDocument("${hyp_file}")
BoardSimDlg.Ok.Click()
MissingHeightDlg.Height = "${missing_height}"
MissingHeightDlg.ForAllParts = true
MissingHeightDlg.Ok.Click()
"""

MACRO_OPS_5 = r"""
Application.ShowBar("Drafting Toolbar")
Application.ExecuteCommand("Create Text")
AddFreeTextDlg.TextString = "${text}"
AddFreeTextDlg.XCoord = "${text_px}"
AddFreeTextDlg.YCoord = "${text_py}"
AddFreeTextDlg.TextHeight = "${text_height}"
AddFreeTextDlg.LineWidth = "${line_width}"
AddFreeTextDlg.LayerName = "${layer}"
AddFreeTextDlg.Mirrored = ${mirrored}
AddFreeTextDlg.Ok.Click()
AddFreeTextDlg.Cancel.Click()
"""
