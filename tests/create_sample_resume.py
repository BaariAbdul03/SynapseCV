from fpdf import FPDF

class ResumePDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

pdf = ResumePDF()
pdf.add_page()
pdf.set_font("helvetica", "B", 20)
pdf.cell(0, 10, "Abdul Baari", new_x="LMARGIN", new_y="NEXT", align="C")

pdf.set_font("helvetica", "", 10)
# Add contact links, including clickable links!
pdf.cell(0, 10, "abdulbaariindian@gmail.com | +918004488791", new_x="LMARGIN", new_y="NEXT", align="C")

# Let's add hyperlink annotations!
pdf.set_text_color(0, 0, 255)
pdf.set_font("helvetica", "U", 10)
pdf.cell(0, 10, "LinkedIn Profile", link="https://linkedin.com/in/abdulbaari", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.cell(0, 10, "GitHub Profile", link="https://github.com/abdulbaari", new_x="LMARGIN", new_y="NEXT", align="C")

pdf.set_text_color(0, 0, 0)
pdf.set_font("helvetica", "B", 14)
pdf.cell(0, 15, "Education", new_x="LMARGIN", new_y="NEXT")

pdf.set_font("helvetica", "", 10)
pdf.cell(0, 8, "B.Tech - Computer Science & Design (82.13%), R.R. Institute of Modern Technology, AKTU, 2022 - 2026", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Intermediate (12th Grade, I.S.C) - 69.8%, Spring Dale College, 2022", new_x="LMARGIN", new_y="NEXT")

pdf.set_font("helvetica", "B", 14)
pdf.cell(0, 15, "Skills", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("helvetica", "", 10)
pdf.cell(0, 8, "Python, Flask, JavaScript, HTML, CSS, SQLite, Git, Java, C++", new_x="LMARGIN", new_y="NEXT")

pdf.output("d:\\ResumeParser\\Resume-Parser\\tests\\sample_resume.pdf")
print("PDF created successfully!")
