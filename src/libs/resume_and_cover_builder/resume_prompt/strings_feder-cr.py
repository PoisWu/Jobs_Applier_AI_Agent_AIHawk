from src.libs.resume_and_cover_builder.template_base import (
    prompt_header_template,
    prompt_education_template,
    prompt_working_experience_template,
    prompt_projects_template,
    prompt_achievements_template,
    prompt_certifications_template,
    prompt_additional_skills_template,
)

prompt_header = (
    """
Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to create a professional and polished header for the resume. The header should:

1. **Contact Information**: Include your full name, phone number, nationality or country, email address, and LinkedIn profile. If GitHub is provided, include it too.
2. **Formatting**: Use centered text with diamond (◇) separators between items on the same line. Do NOT use Font Awesome icons.
3. **Name**: Use the exact name as provided in title case. Do NOT uppercase the entire name.

Exclude any information that is not provided (None).

- **My information:**  
  {personal_information}
"""
    + prompt_header_template
)


prompt_education = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to articulate the educational background in a compact format. For each educational entry:

1. **Single Line Format**: "**Degree**, Institution Name (GPA: X.XX/4.00)" with dates right-aligned.
2. **Optional Description**: One short line below describing the institution or program focus (e.g. "Top leading engineering school in France, Cybersecurity and Cloud major."). Only include if meaningful context is available.
3. **Grade**: Include GPA only if it is strong and relevant. Omit if not provided.

Do not include coursework listings. Keep each entry compact: ideally 2 lines maximum.

- **My information:**  
  {education_details}
"""
    + prompt_education_template
)


prompt_working_experience = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to detail the work experience for a resume. For each job entry:

1. **Line 1**: Bold job title on the left, employment dates on the right.
2. **Line 2**: Italic company name on the left, italic location on the right.
3. **Sub-headings** (optional): If a role contains clearly distinct project areas or workstreams, group them under bold sub-headings with a brief description paragraph, then bullet points. Only use sub-headings when the role truly has multiple distinct work areas.
4. **Bullet Points**: Describe key responsibilities and achievements with measurable results. Use concise, action-oriented language.

Include ALL experience entries from the data. Do not skip any. List in reverse chronological order.

- **My information:**  
  {experience_details}
"""
    + prompt_working_experience_template
)


prompt_projects = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to highlight personal projects. For each project:

1. **Header Format**: "**Project Name** | Tech1, Tech2, Tech3" on the left, dates on the right.
2. **Project Name**: Should be a link to the GitHub repo or project page.
3. **Bullet Points**: Describe technical contributions, architecture decisions, and specific implementation details. Focus on what you built and how, not just what the project is.

Do not use Font Awesome icons. Include all projects from the data.

- **My information:**  
  {projects}
"""
    + prompt_projects_template
)


prompt_achievements = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to list significant achievements. For each achievement, ensure you include:

1. **Award or Recognition**: Clearly state the name of the award, recognition, scholarship, or honor.
2. **Description**: Provide a brief description of the achievement and its relevance to your career or academic journey.

- **My information:**  
  {achievements}
"""
    + prompt_achievements_template
)


prompt_certifications = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to list significant certifications based on the provided details. For each certification, ensure you include:

1. **Certification Name**: Clearly state the name of the certification.
2. **Description**: Provide a brief description of the certification and its relevance to your professional or academic career.

Ensure that the certifications are clearly presented and effectively highlight your qualifications.

To implement this:

If any of the certification details (e.g., descriptions) are not provided (i.e., None), omit those sections when filling out the template.

- **My information:**  
  {certifications}

"""
    + prompt_certifications_template
)


prompt_additional_skills = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to organize skills into a table with bold category names and comma-separated skill values.

Categories should be derived from the provided data. Typical categories include:
- **Artificial Intelligence**: LLM orchestration tools, agent frameworks, deep learning, etc.
- **Cloud & Infrastructure**: Container orchestration, service mesh, observability tools, CI/CD, etc.
- **Network & Security**: Protocols, cryptography, security standards, etc.
- **Programming**: Programming languages only.
- **Languages**: Human languages with proficiency levels (e.g. "Chinese: Native, English: TOEIC 960").

Only include categories for which skills are available. Do not invent skills not present in the data.

- **My information:**  
  {languages}
  {interests}
  {skills}
"""
    + prompt_additional_skills_template
)
