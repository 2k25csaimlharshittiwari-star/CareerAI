import re

ROLE_KEYWORDS = {
    'software': ['python','java','c++','dsa','sql','git','api'],
    'full stack': ['javascript','react','node','sql','html','css','git'],
    'ai/ml': ['python','machine learning','pandas','numpy','tensorflow','pytorch','sql'],
    'data': ['python','sql','pandas','numpy','statistics','power bi','excel'],
    'cyber': ['linux','networking','python','security','siem','cloud'],
}

def analyze_resume(text: str, target_role: str | None = None):
    clean = re.sub(r'\s+', ' ', text or '').strip()
    lower = clean.lower()
    role = (target_role or 'software').lower()
    keywords = next((v for k,v in ROLE_KEYWORDS.items() if k in role), ROLE_KEYWORDS['software'])
    found = [k for k in keywords if k in lower]
    missing = [k for k in keywords if k not in lower]
    sections = {name: bool(re.search(rf'\b{name}\b', lower)) for name in ['education','experience','projects','skills','certifications']}
    score = min(100, 40 + len(found)*8 + sum(sections.values())*4)
    strengths = [f'Contains evidence for {x}.' for x in found[:5]] or ['Your resume has not yet surfaced enough role-specific keywords.']
    improvements = [f'Add measurable evidence for {x} where it is genuinely part of your experience.' for x in missing[:5]]
    if not sections['projects']: improvements.append('Add a projects section with outcomes, technologies and links.')
    if not sections['experience']: improvements.append('Add experience/internship evidence if applicable.')
    return {'resume_score': score, 'detected_keywords': found, 'missing_keywords': missing, 'sections_detected': sections, 'strengths': strengths, 'improvements': improvements, 'role_alignment': f'AI estimate for {target_role or "Software Developer"}; verify against the target job description.'}
