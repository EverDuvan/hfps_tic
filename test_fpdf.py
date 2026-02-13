from fpdf import FPDF

try:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    pdf.cell(40, 10, 'Hello World')
    
    # Test dest='S'
    out = pdf.output(dest='S')
    print(f"Output type: {type(out)}")
    print(f"Has encode: {hasattr(out, 'encode')}")
    
except Exception as e:
    print(f"Error: {e}")
