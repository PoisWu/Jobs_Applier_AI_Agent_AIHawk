"""
This module is used to store the global configuration of the application.
"""

# app/libs/resume_and_cover_builder/template_base.py


prompt_cover_letter_template = """
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
prompt_header_template = """
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
- The name must NOT be uppercase; use normal title case exactly as provided (e.g. "Cheng-Yen Wu").
- Use the diamond symbol ◇ (U+25C7, LaTeX $\diamond$) as separator between contact items on the same line.
- If LinkedIn or GitHub or any field is not provided (None), omit that item from the contact line.
- If GitHub is provided, add it to the second contact line after LinkedIn, separated by a diamond.
- Do not use any Font Awesome icon classes.
The results should be provided in html format, Provide only the html code for the resume, without any explanations or additional text and also without ```html ```
"""

prompt_education_template = """
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


prompt_working_experience_template = """
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


prompt_projects_template = """
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


prompt_achievements_template = """
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

prompt_certifications_template = """
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

prompt_additional_skills_template = """
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
