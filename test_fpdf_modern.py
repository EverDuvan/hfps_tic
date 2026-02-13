from fpdf import FPDF

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', size=12)
    pdf.cell(40, 10, 'Hello World')
    
    # Test default output
    out = pdf.output()
    print(f"Output type: {type(out)}")
    
except Exception as e:
    print(f"Error: {e}")
