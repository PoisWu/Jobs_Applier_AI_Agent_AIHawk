from src.libs.resume_and_cover_builder.template_base import (
    prompt_header_template,
    prompt_education_template,
    prompt_working_experience_template,
    prompt_projects_template,
    prompt_additional_skills_template,
    prompt_certifications_template,
    prompt_achievements_template,
)

prompt_header = (
    """
Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to create a professional and polished header for the resume. The header should:

1. **Contact Information**: Include your full name, phone number, nationality or country, email address, and LinkedIn profile. If GitHub is provided, include it too.
2. **Formatting**: Use centered text with diamond (◇) separators between items on the same line. Do NOT use Font Awesome icons.
3. **Name**: Use the exact name as provided in title case. Do NOT uppercase the entire name.

If any of the contact information fields are not provided (i.e., `None`), omit them from the header.

- **My information:**  
  {personal_information}
"""
    + prompt_header_template
)

prompt_education = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to articulate the educational background in a compact format, ensuring it aligns with the provided job description. For each educational entry:

1. **Single Line Format**: "**Degree**, Institution Name (GPA: X.XX/4.00)" with dates right-aligned.
2. **Optional Description**: One short line below describing the institution or program focus (e.g. "Top leading engineering school in France, Cybersecurity and Cloud major."). Only include if meaningful context is available.
3. **Grade**: Include GPA only if it is strong and relevant. Omit if not provided.

Do not include coursework listings. Keep each entry compact: ideally 2 lines maximum.
If exam details are not provided (i.e., `None`), skip them.

- **My information:**  
  {education_details}

- **Job Description:**  
  {job_description}
"""
    + prompt_education_template
)


prompt_working_experience = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to detail the work experience for a resume, ensuring it aligns with the provided job description. For each job entry:

1. **Line 1**: Bold job title on the left, employment dates on the right.
2. **Line 2**: Italic company name on the left, italic location on the right.
3. **Sub-headings** (optional): If a role contains clearly distinct project areas or workstreams, group them under bold sub-headings with a brief description paragraph, then bullet points. Only use sub-headings when the role truly has multiple distinct work areas.
4. **Bullet Points**: Describe key responsibilities and achievements with measurable results. Use concise, action-oriented language.

Include ALL experience entries from the data. Do not skip any. List in reverse chronological order.
If any work experience details are not provided (i.e., `None`), omit those sections.

- **My information:**  
  {experience_details}

- **Job Description:**  
  {job_description}
"""
    + prompt_working_experience_template
)


prompt_projects = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to highlight personal projects, ensuring they align with the provided job description. For each project:

1. **Header Format**: "**Project Name** | Tech1, Tech2, Tech3" on the left, dates on the right.
2. **Project Name**: Should be a link to the GitHub repo or project page.
3. **Bullet Points**: Describe technical contributions, architecture decisions, and specific implementation details relevant to the job description.

Do not use Font Awesome icons. Include all projects from the data.
If any project details are not provided (i.e., `None`), omit those sections.

- **My information:**  
  {projects}

- **Job Description:**  
  {job_description}
"""
    + prompt_projects_template
)


prompt_achievements = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to list significant achievements based on the provided job description. For each achievement, ensure you include:

1. **Award or Recognition**: Clearly state the name of the award, recognition, scholarship, or honor.
2. **Description**: Provide a brief description of the achievement and its relevance to your career or academic journey.

Ensure that the achievements are clearly presented and effectively highlight your accomplishments.

To implement this:
- If any of the achievement details (e.g., certifications, descriptions) are not provided (i.e., `None`), omit those sections when filling out the template.


- **My information:**  
  {achievements}

- **Job Description:**  
  {job_description}
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

- **Job Description:**  
  {job_description}
"""
    + prompt_certifications_template
)


prompt_additional_skills = (
    """
Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to organize skills into a table with bold category names and comma-separated skill values.
Do not add any information beyond what is listed in the provided data fields. Only use the information provided in the 'languages', 'interests', and 'skills' fields to formulate your responses. Avoid extrapolating or incorporating details from the job description or other external sources.

Categories should be derived from the provided data. Typical categories include:
- **Artificial Intelligence**: LLM orchestration tools, agent frameworks, deep learning, etc.
- **Cloud & Infrastructure**: Container orchestration, service mesh, observability tools, CI/CD, etc.
- **Network & Security**: Protocols, cryptography, security standards, etc.
- **Programming**: Programming languages only.
- **Languages**: Human languages with proficiency levels (e.g. "Chinese: Native, English: TOEIC 960").

Only include categories for which skills are available. Do not invent skills not present in the data.
If any skill details are not provided (i.e., `None`), omit those sections.

- **My information:**  
  {languages}
  {interests}
  {skills}

- **Job Description:**  
  {job_description}
"""
    + prompt_additional_skills_template
)

summarize_prompt_template = """
As a seasoned HR expert, your task is to identify and outline the key skills and requirements necessary for the position of this job. Use the provided job description as input to extract all relevant information. This will involve conducting a thorough analysis of the job's responsibilities and the industry standards. You should consider both the technical and soft skills needed to excel in this role. Additionally, specify any educational qualifications, certifications, or experiences that are essential. Your analysis should also reflect on the evolving nature of this role, considering future trends and how they might affect the required competencies.

Rules:
Remove boilerplate text
Include only relevant information to match the job description against the resume

# Analysis Requirements
Your analysis should include the following sections:
Technical Skills: List all the specific technical skills required for the role based on the responsibilities described in the job description.
Soft Skills: Identify the necessary soft skills, such as communication abilities, problem-solving, time management, etc.
Educational Qualifications and Certifications: Specify the essential educational qualifications and certifications for the role.
Professional Experience: Describe the relevant work experiences that are required or preferred.
Role Evolution: Analyze how the role might evolve in the future, considering industry trends and how these might influence the required skills.

# Final Result:
Your analysis should be structured in a clear and organized document with distinct sections for each of the points listed above. Each section should contain:
This comprehensive overview will serve as a guideline for the recruitment process, ensuring the identification of the most qualified candidates.

# Job Description:
```
{text}
```

---

# Job Description Summary"""
