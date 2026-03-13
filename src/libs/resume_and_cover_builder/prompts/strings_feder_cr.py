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
        "Your task is to generate the `<main>` section of an HTML resume.\n"
        "Render sections in this exact order: Summary, Work Experience, Education, "
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
        "<main>\\n"
        "  [Summary section]\\n"
        "  [Work Experience section]\\n"
        "  [Education section]\\n"
        "  [Personal Projects section]\\n"
        "  [Achievements section — omit entirely if achievements data is empty]\\n"
        "  [Certifications section]\\n"
        "  [Skills section]\\n"
        "</main>\\n"
        "- Do NOT include `<header>`, `<body>`, or any tags outside `<main>`.\n"
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

Act as an HR expert and resume writer specializing in ATS-friendly resumes.
Your task is to generate an HTML snippet for the Personal Projects section of a resume, using the provided project data.

## YOUR INPUTS

**Project Data:**
{projects}

## OUTPUT RULES

### Structure
- Include ALL projects from the data. Do not skip any.
- For each project, produce one `<div class="entry">` block using the template below.

### Entry Layout (in this exact order)
1. **Header line**: Bold plain project name (no hyperlink) on the left, date range on the right.
2. **Tech-and-link row**: Tech stack on the left, repo URL on the right — both in one `<div class="entry-tech-row">`.
3. **Bullet points**: Exactly 2–3 bullets below the tech-and-link row.

### Header Format
- Left side: Bold plain text project name — do NOT wrap it in an `<a>` tag.
- Right side: Date range read directly from `date_start` and `date_end` fields. Do not parse dates from any text.

### Tech-and-Link Row
- Left: `<span class="entry-tech">` containing ALL `tech_stack` items verbatim, comma-separated. Do NOT omit any item.
- Right: `<a class="entry-link" href="[full link]">` whose visible text is the URL with `https://` stripped (e.g. `github.com/user/repo`). Omit the `<a>` (but keep the `<span>`) if `link` is null.
- Both are siblings inside `<div class="entry-tech-row">`.

### Bullet Points
- Each bullet must follow this pattern:
  [Strong action verb] + [what you built or decided] + [technical benefit or outcome].
- Optimize for general backend and software engineering roles: emphasize scalability, maintainability, testing practices, and system design decisions.
- Draw from the `highlights` list as your source material — rephrase and elevate them, do not copy verbatim.
- Use the `summary` field only for context, not as a bullet point.

### Formatting
- Do not use Font Awesome icon classes.
- Do not add inline styles.
- Do not include explanations, markdown, or code fences in your output.
- Output only the raw HTML snippet — nothing before or after it.
- If any project field is missing or null, omit that element silently.

## TEMPLATE

<section id="side-projects">
  <h2>Personal Projects</h2>

  <div class="entry">
    <div class="entry-header">
      <span class="entry-name"><strong>[name]</strong></span>
      <span class="entry-year">[date_start] – [date_end]</span>
    </div>
    <div class="entry-tech-row">
      <span class="entry-tech">[tech_stack, comma-separated]</span>
      <a class="entry-link" href="[link]">[link without https://]</a>
    </div>
    <ul class="compact-list">
      <li>[Action verb + what you did + technical benefit]</li>
      <li>[Action verb + what you did + technical benefit]</li>
      <li>[Action verb + what you did + technical benefit, if needed]</li>
    </ul>
  </div>

  <!-- Repeat <div class="entry"> for each project -->

</section>
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

Act as an expert HR recruiter and resume writer specializing in ATS-friendly resumes. Your task is to write a compelling professional summary (roughly 50 words) that acts as a "sales pitch" to grab a recruiter's attention by answering: "Why should we hire you?"

Follow these guidelines:
1. **Opening Sentence**: Start with the candidate's current title and years of experience using a strong, descriptive headline (e.g., "Result-driven Software Engineer with 5+ years of experience in..."). Do NOT open with vague phrases like "with experience in". Do NOT use first-person pronouns (no "I am...").
2. **Key Skills & Expertise**: Mention 2–3 core skills or technical domains most relevant to the candidate's background.
3. **Quantifiable Achievement**: Include at least one measurable achievement using numbers or percentages (e.g., "increased efficiency by 20%").
4. **Value Addition**: Briefly state the candidate's career goal or what they bring to a prospective employer.

Rules:
- Keep it roughely 50 words.
- Do NOT use first-person pronouns.
- Avoid clichés like "hard-working team player"; use action-oriented, professional language.
- Do NOT add a section heading — output only the `<section>` element.

- **My information:**
  Personal: {personal_information}
  Experience: {experience_details}
  Education: {education_details}

- **Template to Use**
```
<section id="summary">
    <h2>Summary</h2>
    <p>[3–4 sentence professional summary, roughly 50 words]</p>
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

Act as an HR expert and resume writer specializing in ATS-friendly resumes.
Your task is to generate an HTML snippet for the Personal Projects section of a resume, using the provided project data and job description.

## YOUR INPUTS

**Project Data:**
{projects}

**Job Description:**
{job_description}

## OUTPUT RULES

### Structure
- Include ALL projects from the data. Do not skip any.
- For each project, produce one `<div class="entry">` block using the template below.

### Entry Layout (in this exact order)
1. **Header line**: Bold plain project name (no hyperlink) on the left, date range on the right.
2. **Tech-and-link row**: Tech stack on the left, repo URL on the right — both in one `<div class="entry-tech-row">`.
3. **Bullet points**: Exactly 2–3 bullets below the tech-and-link row.

### Header Format
- Left side: Bold plain text project name — do NOT wrap it in an `<a>` tag.
- Right side: Date range read directly from `date_start` and `date_end` fields. Do not parse dates from any text.

### Tech-and-Link Row
- Left: `<span class="entry-tech">` containing ALL `tech_stack` items verbatim, comma-separated. Do NOT omit any item.
- Right: `<a class="entry-link" href="[full link]">` whose visible text is the URL with `https://` stripped (e.g. `github.com/user/repo`). Omit the `<a>` (but keep the `<span>`) if `link` is null.
- Both are siblings inside `<div class="entry-tech-row">`.

### Bullet Points
- Each bullet must follow this pattern:
  [Strong action verb] + [what you built or decided] + [technical benefit or outcome].
- Prioritize language and keywords that match the job description (e.g., scalability, reliability, performance, maintainability).
- Draw from the `highlights` list as your source material — rephrase and elevate them, do not copy verbatim.
- Use the `summary` field only for context, not as a bullet point.
- If no job description is provided, optimize for general backend and software engineering roles: emphasize scalability, maintainability, testing practices, and system design decisions.

### Formatting
- Do not use Font Awesome icon classes.
- Do not add inline styles.
- Do not include explanations, markdown, or code fences in your output.
- Output only the raw HTML snippet — nothing before or after it.
- If any project field is missing or null, omit that element silently.

## TEMPLATE

<section id="side-projects">
  <h2>Personal Projects</h2>

  <div class="entry">
    <div class="entry-header">
      <span class="entry-name"><strong>[name]</strong></span>
      <span class="entry-year">[date_start] – [date_end]</span>
    </div>
    <div class="entry-tech-row">
      <span class="entry-tech">[tech_stack, comma-separated]</span>
      <a class="entry-link" href="[link]">[link without https://]</a>
    </div>
    <ul class="compact-list">
      <li>[Action verb + what you did + technical benefit]</li>
      <li>[Action verb + what you did + technical benefit]</li>
      <li>[Action verb + what you did + technical benefit, if needed]</li>
    </ul>
  </div>

  <!-- Repeat <div class="entry"> for each project -->

</section>
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

Act as an expert HR recruiter and resume writer specializing in ATS-friendly resumes. Your task is to write a compelling professional summary (50–100 words, 3–4 sentences) tailored to the job description, acting as a "sales pitch" to grab the recruiter's attention by answering: "Why should we hire you for this role?"

Follow these guidelines:
1. **Opening Sentence**: Start with the candidate's current title and years of experience using a strong, descriptive headline (e.g., "Result-driven Software Engineer with 5+ years of experience in..."). Do NOT open with vague phrases like "with experience in". Do NOT use first-person pronouns (no "I am...").
2. **Key Skills & Expertise**: Mention 2–3 core skills most relevant to the job description.
3. **Quantifiable Achievement**: Include at least one measurable achievement using numbers or percentages that aligns with the role (e.g., "increased efficiency by 20%").
4. **Value Addition**: Briefly state what the candidate brings to this specific company or role.

Rules:
- Keep it between 50–100 words.
- Tailor every sentence to match the specific job description.
- Do NOT use first-person pronouns.
- Avoid clichés like "hard-working team player"; use action-oriented, professional language.
- Do NOT add a section heading — output only the `<section>` element.

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
    <p>[3–4 sentence professional summary tailored to the job, 50–100 words]</p>
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
