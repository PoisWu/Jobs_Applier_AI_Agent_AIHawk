"""Consolidated prompt strings for all resume/cover-letter generators.

Each namespace corresponds to one generation mode:
- ``resume``                 - base resume (no job description)
- ``resume_job_description`` - job-tailored resume
- ``cover_letter``           - job-tailored cover letter
"""

from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Shared: used by both resume_job_description and cover_letter generators
# ---------------------------------------------------------------------------

_summarize_prompt_template = """\

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

# ---------------------------------------------------------------------------
# Helper: compose single-query full-resume prompt from individual section prompts
# ---------------------------------------------------------------------------

_SECTION_OUTPUT_RULE = (
    "The results should be provided in html format, Provide only the html code for the resume, "
    "without any explanations or additional text and also without ```html ```"
)


def _build_full_resume_prompt(ns: SimpleNamespace, *, with_job_description: bool = False) -> str:
    """Compose a single-query full-resume prompt by reusing the namespace's section prompts.

    Strips the per-section output directive from each section prompt to avoid repetition,
    then wraps everything in a unified intro and a single output instruction.
    """

    def _strip(text: str) -> str:
        return text.replace(_SECTION_OUTPUT_RULE, "").rstrip("\n")

    job_desc_note = (
        "\nIMPORTANT: Tailor every section to align with the provided job description.\n"
        if with_job_description
        else ""
    )

    sections = [
        ("Summary", _strip(ns.prompt_summary)),
        ("Work Experience", _strip(ns.prompt_working_experience)),
        ("Education", _strip(ns.prompt_education)),
        ("Personal Projects", _strip(ns.prompt_projects)),
        ("Achievements", _strip(ns.prompt_achievements)),
        ("Certifications", _strip(ns.prompt_certifications)),
        ("Skills", _strip(ns.prompt_additional_skills)),
    ]
    combined_sections = "\n\n---\n\n".join(f"## {name} Section\n{content}" for name, content in sections)

    data_vars = (
        "- **Personal Information:** {personal_information}\n"
        "- **Work Experience:** {experience_details}\n"
        "- **Education:** {education_details}\n"
        "- **Projects:** {projects}\n"
        "- **Achievements:** {achievements}\n"
        "- **Certifications:** {certifications}\n"
        "- **Languages:** {languages}\n"
        "- **Interests:** {interests}\n"
        "- **Skills:** {skills}\n"
    )
    if with_job_description:
        data_vars += "- **Job Description:** {job_description}\n"

    return (
        "Act as an HR expert and resume writer specialising in ATS-friendly resumes. "
        "Your task is to generate a COMPLETE HTML resume in a SINGLE output.\n"
        "The `<header>` element (name and contact) is rendered FIRST and stands OUTSIDE `<main>`. "
        "Inside `<main>`, render sections in this exact order: Summary, Work Experience, Education, "
        "Projects, Achievements, Certifications, Skills. Sections MUST appear in this exact order. "
        "Skip any section entirely if its corresponding data is None or an empty list.\n"
        "Aim for a single-page output. Keep each bullet point to one line. "
        "Prioritize impact and specificity; omit low-value bullets.\n"
        f"{job_desc_note}\n"
        "Below are the formatting rules and templates for each section:\n\n"
        f"{combined_sections}\n\n"
        "---\n\n"
        "## My Resume Data\n"
        f"{data_vars}\n"
        "---\n\n"
        "**Final Output Rules:**\n"
        "Your output structure MUST follow this exact skeleton:\n"
        "<header>\\n"
        "  [header content — name and contact]\\n"
        "</header>\\n"
        "<main>\\n"
        "  [Summary section]\\n"
        "  [Work Experience section]\\n"
        "  [Education section]\\n"
        "  [Personal Projects section]\\n"
        "  [Achievements section — omit entirely if achievements data is empty]\\n"
        "  [Certifications section]\\n"
        "  [Skills section]\\n"
        "</main>\\n"
        "- `<header>` MUST be the very first element. `<main>` MUST follow directly after `<header>`.\n"
        "- Do NOT include `<body>` tags.\n"
        "- Do NOT include ```html ``` code fences.\n"
        "- No explanations or additional text outside the HTML.\n"
        "- Before emitting HTML, verify: (1) no placeholder text of the form `[...]` appears, "
        "(2) all dates match the input data exactly, (3) `<header>` is the first element, "
        "(4) `<main>` follows directly after `<header>`, "
        "(5) sections inside `<main>` appear in order: Summary, Work Experience, Education, "
        "Projects, Achievements, Certifications, Skills.\n"
    )


# ---------------------------------------------------------------------------
# resume - base resume generation (no job description)
# ---------------------------------------------------------------------------

resume = SimpleNamespace(
    prompt_header=(
        """\

Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to create a professional and polished header for the resume. The header should:

1. **Contact Information**: Include your full name, phone number, nationality or country, email address, and LinkedIn profile. If GitHub is provided, include it too.
2. **Formatting**: Use centered text with diamond (◇) separators between items on the same line. Do NOT use Font Awesome icons.
3. **Name**: Use the exact name as provided in title case. Do NOT uppercase the entire name.

Exclude any information that is not provided (None).

- **My information:**
  {personal_information}

- **Template to Use**
```
<header>
  <h1>[Name and Surname]</h1>
  <div class="contact-info">
    <p class="contact-line">[Your Prefix Phone number] <span class="separator">◇</span> [Nationality or Country]</p>
    <p class="contact-line"><a href="mailto:[Your Email]">[Your Email]</a> <span class="separator">◇</span> <a href="[Link LinkedIn account]">[LinkedIn display text, e.g. linkedin.com/in/username]</a></p>
  </div>
</header>
```
Important formatting rules:
- The name must NOT be uppercase; use normal title case exactly as provided (e.g. "[First Last]").
- Use the diamond symbol ◇ (U+25C7, LaTeX $\\diamond$) as separator between contact items on the same line.
- If LinkedIn or GitHub or any field is not provided (None), omit that item from the contact line.
- If GitHub is provided, add it to the second contact line after LinkedIn, separated by a diamond.
- Do not use any Font Awesome icon classes.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_education=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to articulate the educational background in a compact format. For each educational entry:

1. **Single Line Format**: "**Degree**, Institution Name (GPA: X.XX/4.00)" with dates right-aligned.
2. **Optional Description**: One short line below describing the institution or program focus (e.g. "Top leading engineering school in France, Cybersecurity and Cloud major."). Only include if meaningful context is available.
3. **Grade**: Include GPA only if it is strong and relevant. Omit if not provided.

Do not include coursework listings. Keep each entry compact: ideally 2 lines maximum.

- **My information:**
  {education_details}

- **Template to Use**
```
<section id="education">
    <h2>Education</h2>
    <div class="education-entry">
      <div class="edu-line">
          <span><strong>[Degree]</strong>, [University Name] (GPA: [Your Grade])</span>
          <span class="entry-year">[Start Year] – [End Year]</span>
      </div>
      <p class="edu-description">[One-line description of the institution or program, e.g. "Top leading engineering school in France, Cybersecurity and Cloud major."]</p>
    </div>
</section>
```
Important formatting rules:
- Each education entry should be compact: degree + institution + GPA on one line, dates right-aligned.
- The description line below is optional; include it only if relevant context is available (e.g. school ranking, major focus). Keep it to one line.
- If the grade is not provided or not strong, omit "(GPA: ...)" entirely.
- List education entries in reverse chronological order.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_working_experience=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to detail the work experience for a resume. For each job entry:

1. **Line 1**: Bold job title on the left, employment dates on the right.
2. **Line 2**: Italic company name on the left, italic location on the right.
3. **Sub-headings** (optional): If a role contains clearly distinct project areas or workstreams, group them under bold sub-headings with a brief description paragraph, then bullet points. Only use sub-headings when the role truly has multiple distinct work areas.
4. **Bullet Points**: Describe key responsibilities and achievements with measurable results. Use concise, action-oriented language.

Include ALL experience entries from the data. Do not skip any. List in reverse chronological order.
If a role has zero technical achievements (e.g. military service), render the full `<div class="entry">` with `entry-header` (job title + dates) and `entry-details` (company + location), but replace the `<ul>` with a single `<p class="entry-description">` containing the description. Do NOT omit the wrapper or the header rows.

- **My information:**
  {experience_details}

- **Template to Use**
```
<section id="work-experience">
    <h2>Experience</h2>
    <div class="entry">
      <div class="entry-header">
          <span class="entry-name">[Your Job Title]</span>
          <span class="entry-year">[Start Date] – [End Date]</span>
      </div>
      <div class="entry-details">
          <span class="entry-title">[Company Name]</span>
          <span class="entry-location">[Location]</span>
      </div>
      <p class="entry-subtitle">[Optional: Sub-heading grouping related work, e.g. "Document Understanding"]</p>
      <p class="entry-description">[Optional: One or two sentences summarizing this sub-area of work]</p>
      <ul class="compact-list">
          <li>[Describe your responsibilities and achievements]</li>
          <li>[Describe any key projects or technologies you worked with]</li>
      </ul>
      <p class="entry-subtitle">[Optional: Another sub-heading, e.g. "Architecture of the multi-agent system"]</p>
      <p class="entry-description">[Optional: Summary of this sub-area]</p>
      <ul class="compact-list">
          <li>[Describe responsibilities and achievements for this sub-area]</li>
          <li>[Mention any notable accomplishments or results]</li>
      </ul>
    </div>
</section>
```
Important formatting rules:
- Line 1: Bold job title on the left, dates on the right.
- Line 2: Italic company name on the left, italic location on the right.
- Sub-headings (entry-subtitle) are OPTIONAL. Only use them when a role has clearly distinct project areas or workstreams that benefit from grouping. For most roles, simply list bullet points directly without sub-headings.
- When sub-headings are used, include a brief entry-description paragraph below each sub-heading summarizing that work area, then the bullet points.
- Include all experience entries from the data. Do not skip any.
- List in reverse chronological order.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_projects=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to highlight personal projects. For each project:

1. **Header Format**: "**Project Name** | Tech1, Tech2, Tech3" on the left, dates on the right.
2. **Project Name**: Should be a link to the GitHub repo or project page.
3. **Bullet Points**: Describe technical contributions, architecture decisions, and specific implementation details. Focus on what you built and how, not just what the project is.

Do not use Font Awesome icons. Include all projects from the data.
If a `tech_stack` list is present on the project data, copy ALL items from it verbatim and comma-separated for the `| Tech1, Tech2` field. Do NOT select a subset — every item in the list must appear. Extract dates from the trailing parenthetical in the description string (e.g. `(Dec 2025 - Jan 2026)`) when no separate date field exists.

- **My information:**
  {projects}

- **Template to Use**
```
<section id="side-projects">
    <h2>Personal Projects</h2>
    <div class="entry">
      <div class="entry-header">
          <span class="entry-name"><strong><a href="[Github Repo or Link]">[Project Name]</a></strong> | [Tech1, Tech2, Tech3]</span>
          <span class="entry-year">[Month Year] – [Month Year]</span>
      </div>
      <ul class="compact-list">
          <li>[Describe what the project does and key technical decisions]</li>
          <li>[Describe specific implementation details or outcomes]</li>
      </ul>
    </div>
</section>
```
Important formatting rules:
- The entry-name contains the bolded project name as a link, followed by " | " and a comma-separated list of key technologies.
- Dates are right-aligned.
- Bullet points should describe technical contributions, not just what the project is.
- Do not use Font Awesome icon classes.
- Include all projects from the data.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_achievements=(
        """\

If the achievements list is empty or None, output nothing at all — no `<section>` tag, no heading, no empty list.

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to list significant achievements. For each achievement, ensure you include:

1. **Award or Recognition**: Clearly state the name of the award, recognition, scholarship, or honor.
2. **Description**: Provide a brief description of the achievement and its relevance to your career or academic journey.

- **My information:**
  {achievements}

- **Template to Use**
```
<section id="achievements">
    <h2>Achievements</h2>
    <ul class="compact-list">
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
    </ul>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_certifications=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to list significant certifications based on the provided details. For each certification, ensure you include:

1. **Certification Name**: Clearly state the name of the certification.
2. **Description**: Provide a brief description of the certification and its relevance to your professional or academic career.

Ensure that the certifications are clearly presented and effectively highlight your qualifications.

To implement this:

If any of the certification details (e.g., descriptions) are not provided (i.e., None), omit those sections when filling out the template.

- **My information:**
  {certifications}


- **Template to Use**
```
<section id="certifications">
    <h2>Certifications</h2>
    <ul class="compact-list">
      <li><strong>[Certification Name]:</strong> [Describe]</li>
      <li><strong>[Certification Name]:</strong> [Describe]</li>
    </ul>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_additional_skills=(
        """\

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

- **Template to Use**
'''
<section id="skills-languages">
    <h2>Skills</h2>
    <table class="skills-table">
      <tr>
        <td>[Category 1, e.g. Artificial Intelligence]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>[Category 2, e.g. Cloud &amp; Infrastructure]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>[Category 3, e.g. Network &amp; Security]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>Programming</td>
        <td>[Language1, Language2, ...]</td>
      </tr>
      <tr>
        <td>Languages</td>
        <td>[Language: Level, Language: Level, ...]</td>
      </tr>
    </table>
</section>
'''
Important formatting rules:
- Use a table layout with bold category names in the left column and comma-separated skills in the right column.
- Group skills into meaningful categories derived from the provided data (e.g. AI, Cloud & Infrastructure, Network & Security, Programming, Languages).
- The "Languages" row should list human languages with proficiency levels.
- Only include categories for which skills are available. Do not invent skills.
- Each category-value pair is one table row.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
)

resume.prompt_summary = """\

Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to write a concise professional summary of exactly 3 sentences:
1. Sentence 1 MUST begin with a specific number of years (e.g. "3+ years of experience in…"). Do NOT use vague openers like "with experience in". Cover core technical domains (e.g. AI/ML Engineering, Cloud Infrastructure, Cybersecurity).
2. The single most impactful quantified achievement from the most recent role.
3. Educational background (institutions and fields of study).

Do NOT use first-person pronouns. Do NOT add a section heading — output only the `<section>` element.

- **My information:**
  Personal: {personal_information}
  Experience: {experience_details}
  Education: {education_details}

- **Template to Use**
```
<section id="summary">
    <h2>Summary</h2>
    <p>[3-sentence professional summary]</p>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""

resume.prompt_full_resume = _build_full_resume_prompt(resume)

# ---------------------------------------------------------------------------
# resume_job_description - job-tailored resume
# ---------------------------------------------------------------------------

resume_job_description = SimpleNamespace(
    summarize_prompt_template=_summarize_prompt_template,
    prompt_header=(
        """\

Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to create a professional and polished header for the resume. The header should:

1. **Contact Information**: Include your full name, phone number, nationality or country, email address, and LinkedIn profile. If GitHub is provided, include it too.
2. **Formatting**: Use centered text with diamond (◇) separators between items on the same line. Do NOT use Font Awesome icons.
3. **Name**: Use the exact name as provided in title case. Do NOT uppercase the entire name.

If any of the contact information fields are not provided (i.e., `None`), omit them from the header.

- **My information:**
  {personal_information}

- **Template to Use**
```
<header>
  <h1>[Name and Surname]</h1>
  <div class="contact-info">
    <p class="contact-line">[Your Prefix Phone number] <span class="separator">◇</span> [Nationality or Country]</p>
    <p class="contact-line"><a href="mailto:[Your Email]">[Your Email]</a> <span class="separator">◇</span> <a href="[Link LinkedIn account]">[LinkedIn display text, e.g. linkedin.com/in/username]</a></p>
  </div>
</header>
```
Important formatting rules:
- The name must NOT be uppercase; use normal title case exactly as provided (e.g. "[First Last]").
- Use the diamond symbol ◇ (U+25C7, LaTeX $\\diamond$) as separator between contact items on the same line.
- If LinkedIn or GitHub or any field is not provided (None), omit that item from the contact line.
- If GitHub is provided, add it to the second contact line after LinkedIn, separated by a diamond.
- Do not use any Font Awesome icon classes.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_education=(
        """\

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

- **Template to Use**
```
<section id="education">
    <h2>Education</h2>
    <div class="education-entry">
      <div class="edu-line">
          <span><strong>[Degree]</strong>, [University Name] (GPA: [Your Grade])</span>
          <span class="entry-year">[Start Year] – [End Year]</span>
      </div>
      <p class="edu-description">[One-line description of the institution or program, e.g. "Top leading engineering school in France, Cybersecurity and Cloud major."]</p>
    </div>
</section>
```
Important formatting rules:
- Each education entry should be compact: degree + institution + GPA on one line, dates right-aligned.
- The description line below is optional; include it only if relevant context is available (e.g. school ranking, major focus). Keep it to one line.
- If the grade is not provided or not strong, omit "(GPA: ...)" entirely.
- List education entries in reverse chronological order.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_working_experience=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to detail the work experience for a resume, ensuring it aligns with the provided job description. For each job entry:

1. **Line 1**: Bold job title on the left, employment dates on the right.
2. **Line 2**: Italic company name on the left, italic location on the right.
3. **Sub-headings** (optional): If a role contains clearly distinct project areas or workstreams, group them under bold sub-headings with a brief description paragraph, then bullet points. Only use sub-headings when the role truly has multiple distinct work areas.
4. **Bullet Points**: Describe key responsibilities and achievements with measurable results. Use concise, action-oriented language.

Include ALL experience entries from the data. Do not skip any. List in reverse chronological order.
If a role has zero technical achievements (e.g. military service), render the full `<div class="entry">` with `entry-header` (job title + dates) and `entry-details` (company + location), but replace the `<ul>` with a single `<p class="entry-description">` containing the description. Do NOT omit the wrapper or the header rows.
If any work experience details are not provided (i.e., `None`), omit those sections.

- **My information:**
  {experience_details}

- **Job Description:**
  {job_description}

- **Template to Use**
```
<section id="work-experience">
    <h2>Experience</h2>
    <div class="entry">
      <div class="entry-header">
          <span class="entry-name">[Your Job Title]</span>
          <span class="entry-year">[Start Date] – [End Date]</span>
      </div>
      <div class="entry-details">
          <span class="entry-title">[Company Name]</span>
          <span class="entry-location">[Location]</span>
      </div>
      <p class="entry-subtitle">[Optional: Sub-heading grouping related work, e.g. "Document Understanding"]</p>
      <p class="entry-description">[Optional: One or two sentences summarizing this sub-area of work]</p>
      <ul class="compact-list">
          <li>[Describe your responsibilities and achievements]</li>
          <li>[Describe any key projects or technologies you worked with]</li>
      </ul>
      <p class="entry-subtitle">[Optional: Another sub-heading, e.g. "Architecture of the multi-agent system"]</p>
      <p class="entry-description">[Optional: Summary of this sub-area]</p>
      <ul class="compact-list">
          <li>[Describe responsibilities and achievements for this sub-area]</li>
          <li>[Mention any notable accomplishments or results]</li>
      </ul>
    </div>
</section>
```
Important formatting rules:
- Line 1: Bold job title on the left, dates on the right.
- Line 2: Italic company name on the left, italic location on the right.
- Sub-headings (entry-subtitle) are OPTIONAL. Only use them when a role has clearly distinct project areas or workstreams that benefit from grouping. For most roles, simply list bullet points directly without sub-headings.
- When sub-headings are used, include a brief entry-description paragraph below each sub-heading summarizing that work area, then the bullet points.
- Include all experience entries from the data. Do not skip any.
- List in reverse chronological order.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_projects=(
        """\

Act as an HR expert and resume writer with a specialization in creating ATS-friendly resumes. Your task is to highlight personal projects, ensuring they align with the provided job description. For each project:

1. **Header Format**: "**Project Name** | Tech1, Tech2, Tech3" on the left, dates on the right.
2. **Project Name**: Should be a link to the GitHub repo or project page.
3. **Bullet Points**: Describe technical contributions, architecture decisions, and specific implementation details relevant to the job description.

Do not use Font Awesome icons. Include all projects from the data.
If a `tech_stack` list is present on the project data, copy ALL items from it verbatim and comma-separated for the `| Tech1, Tech2` field. Do NOT select a subset — every item in the list must appear. Extract dates from the trailing parenthetical in the description string (e.g. `(Dec 2025 - Jan 2026)`) when no separate date field exists.
If any project details are not provided (i.e., `None`), omit those sections.

- **My information:**
  {projects}

- **Job Description:**
  {job_description}

- **Template to Use**
```
<section id="side-projects">
    <h2>Personal Projects</h2>
    <div class="entry">
      <div class="entry-header">
          <span class="entry-name"><strong><a href="[Github Repo or Link]">[Project Name]</a></strong> | [Tech1, Tech2, Tech3]</span>
          <span class="entry-year">[Month Year] – [Month Year]</span>
      </div>
      <ul class="compact-list">
          <li>[Describe what the project does and key technical decisions]</li>
          <li>[Describe specific implementation details or outcomes]</li>
      </ul>
    </div>
</section>
```
Important formatting rules:
- The entry-name contains the bolded project name as a link, followed by " | " and a comma-separated list of key technologies.
- Dates are right-aligned.
- Bullet points should describe technical contributions, not just what the project is.
- Do not use Font Awesome icon classes.
- Include all projects from the data.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_achievements=(
        """\

If the achievements list is empty or None, output nothing at all — no `<section>` tag, no heading, no empty list.

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

- **Template to Use**
```
<section id="achievements">
    <h2>Achievements</h2>
    <ul class="compact-list">
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
      <li><strong>[Award or Recognition or Scholarship or Honor]:</strong> [Describe]</li>
    </ul>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_certifications=(
        """\

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

- **Template to Use**
```
<section id="certifications">
    <h2>Certifications</h2>
    <ul class="compact-list">
      <li><strong>[Certification Name]:</strong> [Describe]</li>
      <li><strong>[Certification Name]:</strong> [Describe]</li>
    </ul>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
    prompt_additional_skills=(
        """\

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

- **Template to Use**
'''
<section id="skills-languages">
    <h2>Skills</h2>
    <table class="skills-table">
      <tr>
        <td>[Category 1, e.g. Artificial Intelligence]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>[Category 2, e.g. Cloud &amp; Infrastructure]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>[Category 3, e.g. Network &amp; Security]</td>
        <td>[Skill1, Skill2, Skill3, ...]</td>
      </tr>
      <tr>
        <td>Programming</td>
        <td>[Language1, Language2, ...]</td>
      </tr>
      <tr>
        <td>Languages</td>
        <td>[Language: Level, Language: Level, ...]</td>
      </tr>
    </table>
</section>
'''
Important formatting rules:
- Use a table layout with bold category names in the left column and comma-separated skills in the right column.
- Group skills into meaningful categories derived from the provided data (e.g. AI, Cloud & Infrastructure, Network & Security, Programming, Languages).
- The "Languages" row should list human languages with proficiency levels.
- Only include categories for which skills are available. Do not invent skills.
- Each category-value pair is one table row.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""
    ),
)

resume_job_description.prompt_summary = """\

Act as an HR expert and resume writer specializing in ATS-friendly resumes. Your task is to write a concise professional summary of exactly 3 sentences tailored to the job description:
1. Sentence 1 MUST begin with a specific number of years (e.g. "3+ years of experience in…"). Do NOT use vague openers like "with experience in". Cover core technical domains most relevant to the job description.
2. The single most impactful quantified achievement from the most recent role that aligns with the job.
3. Educational background (institutions and fields of study).

Do NOT use first-person pronouns. Do NOT add a section heading — output only the `<section>` element.

- **My information:**
  Personal: {personal_information}
  Experience: {experience_details}
  Education: {education_details}

- **Job Description:**
  {job_description}

- **Template to Use**
```
<section id="summary">
    <h2>Summary</h2>
    <p>[3-sentence professional summary tailored to the job]</p>
</section>
```
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""

resume_job_description.prompt_full_resume = _build_full_resume_prompt(resume_job_description, with_job_description=True)

# ---------------------------------------------------------------------------
# cover_letter - job-tailored cover letter
# ---------------------------------------------------------------------------

cover_letter = SimpleNamespace(
    summarize_prompt_template=_summarize_prompt_template,
    cover_letter_template=(
        """\

Compose a brief and impactful cover letter based on the provided job description and resume. The letter should be no longer than three paragraphs and should be written in a professional, yet conversational tone. Avoid using any placeholders, and ensure that the letter flows naturally and is tailored to the job.

Analyze the job description to identify key qualifications and requirements. Introduce the candidate succinctly, aligning their career objectives with the role. Highlight relevant skills and experiences from the resume that directly match the job’s demands, using specific examples to illustrate these qualifications. Reference notable aspects of the company, such as its mission or values, that resonate with the candidate’s professional goals. Conclude with a strong statement of why the candidate is a good fit for the position, expressing a desire to discuss further.

Please write the cover letter in a way that directly addresses the job role and the company’s characteristics, ensuring it remains concise and engaging without unnecessary embellishments. The letter should be formatted into paragraphs and should not include a greeting or signature.

## Rules:
- Do not include any introductions, explanations, or additional information.

## Details :
- **Job Description:**
```
{job_description}
```
- **My resume:**
```
{resume}
```

- **Template to Use**
```
<section id="cover-letter">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
        <div>
            <p>[Your Name]</p>
            <p>[Your Address]</p>
            <p>[City, State ZIP]</p>
            <p>[Your Email]</p>
            <p>[Your Phone Number]</p>
        </div>
        <div style="text-align: right;">
            <p>[Company Name]</p>
        </div>
    </div>
    <div>
    <p>Dear [Recipient Team],</p>
    <p>[Opening paragraph: Introduce yourself and state the position you are applying for.]</p>
    <p>[Body paragraphs: Highlight your qualifications, experiences, and how they align with the job requirements.]</p>
    <p>[Closing paragraph: Express your enthusiasm for the position and thank the recipient for their consideration.]</p>
    <p>Sincerely,</p>
    <p>[Your Name]</p>
    <p>[Date]</p>
    </div>
</section>
```
The results should be provided in html format, Provide only the html code for the cover letter, without any explanations or additional text and also without ```html ```
"""
    ),
)
