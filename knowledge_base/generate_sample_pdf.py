import fitz  # PyMuPDF

def generate_sample_pdf():
    pdf_path = "knowledge_base/admission_rules_2026.pdf"
    doc = fitz.open()

    # Page 1: General Info & Courses
    page1 = doc.new_page()
    text_p1 = (
        "K.K. WAGH POLYTECHNIC, NASHIK\n"
        "(Approved by AICTE, New Delhi & Affiliated to MSBTE, Mumbai)\n"
        "Official Admission Guidelines & Information Brochure 2026-2027\n\n"
        "1. ABOUT THE INSTITUTE:\n"
        "K.K. Wagh Polytechnic was established in 1983. It is situated at Hirabai Haridas Vidyanagari, Amrutdham, Panchavati, Nashik, Maharashtra 422003.\n"
        "The institute offers 3-year Diploma engineering programs in multiple branches.\n\n"
        "2. DIPLOMA COURSES OFFERED & INTAKE CAPACITY:\n"
        "- Computer Engineering: Intake of 120 seats\n"
        "- Information Technology: Intake of 60 seats\n"
        "- Mechanical Engineering: Intake of 120 seats\n"
        "- Civil Engineering: Intake of 60 seats\n"
        "- Electrical Engineering: Intake of 60 seats\n"
        "- Chemical Engineering: Intake of 30 seats\n\n"
        "3. ELIGIBILITY CRITERIA FOR FIRST YEAR DIPLOMA:\n"
        "Candidate should be an Indian National.\n"
        "Passed 10th Standard / SSC examination of Maharashtra State Board or equivalent with at least 35% aggregate marks.\n"
        "Mathematics, Science, and English are compulsory subjects in 10th Standard.\n"
    )
    page1.insert_text(fitz.Point(50, 50), text_p1, fontsize=11)

    # Page 2: Required Documents & Timings
    page2 = doc.new_page()
    text_p2 = (
        "K.K. WAGH POLYTECHNIC, NASHIK - ADMISSION RULES (PAGE 2)\n\n"
        "4. MANDATORY DOCUMENTS REQUIRED FOR ADMISSION:\n"
        "1. SSC (10th) Marksheet (Original + 3 attested copies)\n"
        "2. School Leaving Certificate / Transfer Certificate (Original)\n"
        "3. Domicile Certificate & Nationality Certificate\n"
        "4. Caste Certificate & Caste Validity Certificate (for Reserved Category)\n"
        "5. Non-Creamy Layer Certificate (valid up to 31st March 2027 for OBC/SBC/VJNT)\n"
        "6. Aadhar Card Copy & 4 Passport size photographs\n\n"
        "5. INSTITUTE TIMINGS & WORKING HOURS:\n"
        "Institute Working Hours: Monday to Saturday from 9:30 AM to 5:15 PM.\n"
        "Library Timings: 8:30 AM to 6:00 PM on working days.\n"
        "Examination Section Working Hours: 10:00 AM to 4:00 PM.\n\n"
        "6. ATTENDANCE & DISCIPLINE RULES:\n"
        "A minimum of 75% attendance in theory lectures and 80% attendance in practical sessions is compulsory to qualify for MSBTE Board Examinations.\n"
        "Ragging is strictly prohibited on campus. Violators face immediate rustication.\n"
    )
    page2.insert_text(fitz.Point(50, 50), text_p2, fontsize=11)

    doc.save(pdf_path)
    doc.close()
    print(f"Sample PDF created successfully at {pdf_path}")

if __name__ == "__main__":
    generate_sample_pdf()
