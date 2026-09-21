import json
import os
from typing import Any

ROLE_SKILLS = {
    'ai/ml engineer':['Python','Machine Learning','Deep Learning','PyTorch','SQL','MLOps'],
    'data scientist':['Python','Pandas','NumPy','SQL','Machine Learning','Statistics'],
    'data analyst':['Python','SQL','Excel','Power BI','Statistics','Pandas'],
    'full stack developer':['HTML/CSS','JavaScript','React','Node.js','SQL','Git/GitHub'],
    'software developer':['Python','Java','C++','DSA','SQL','Git/GitHub'],
    'backend developer':['Python','Java','SQL','REST API','Docker','Git/GitHub'],
    'cybersecurity engineer':['Networking','Linux','Python','Web Security','SIEM','Cloud'],
    'cloud engineer':['Linux','AWS/Azure','Docker','Kubernetes','Networking','Terraform'],
}


def _fallback_analyze(s, skills, projects, coding, academics, performance):
    role=(s.get('target_role') or 'Software Developer').lower()
    req=ROLE_SKILLS.get(role, ROLE_SKILLS['software developer'])
    names={x['name'].lower() for x in skills}
    gaps=[x for x in req if x.lower() not in names]
    academic=round(min(100, (s.get('cgpa') or 0)*10)) if s.get('cgpa') else 0
    technical=round(sum((x.get('score') if x.get('score') is not None else {'beginner':3.5,'intermediate':6.5,'advanced':9}.get((x.get('level') or '').lower(),5)) for x in skills)/len(skills),1) if skills else 2
    solved=sum(x.get('problems_solved') or 0 for x in coding)
    coding_score=min(100,round(solved/3.5)) if coding else 10
    project_score=min(100,35+len(projects)*20)
    performance10=round(sum(float(x.get('score') or 0) for x in performance)/len(performance),1) if performance else 0
    performance100=performance10*10
    overall=round(0.25*academic+0.25*(technical*10)+0.2*coding_score+0.2*project_score+0.1*performance100)
    overall=max(5,min(100,overall))
    summary=f'Your current profile is strongest in {len(skills)} recorded skills and {len(projects)} project(s). For {s.get("target_role") or "your target role"}, focus next on the highest-priority skill gaps and measurable coding/project evidence.'
    roadmap=[{'title':f'Close the {gaps[0]} gap','description':f'Build practical evidence in {gaps[0]} through a guided course and a small project.'}] if gaps else []
    if solved<150: roadmap.append({'title':'Strengthen DSA','description':f'Build from {solved} solved problems toward 150 with consistent practice.'})
    if len(projects)<3: roadmap.append({'title':'Build portfolio depth','description':'Complete another production-style project with GitHub documentation, testing and deployment.'})
    return {'overall':overall,'summary':summary,'gaps':gaps[:6],'roadmap':roadmap[:5],'score_breakdown':{'academic':academic,'technical':technical,'coding':coding_score,'projects':project_score,'recent_performance':performance10,'career_readiness':overall}}


def _fallback_recommendations(s, skills, projects, coding):
    role=(s.get('target_role') or 'Software Developer').lower()
    req=ROLE_SKILLS.get(role, ROLE_SKILLS['software developer'])
    have={x['name'].lower() for x in skills}
    gaps=[r for r in req if r.lower() not in have]
    learning_platforms=[('freeCodeCamp','https://www.freecodecamp.org/'),('Coursera','https://www.coursera.org/'),('Kaggle Learn','https://www.kaggle.com/learn'),('Microsoft Learn','https://learn.microsoft.com/training/'),('edX','https://www.edx.org/'),('AWS Skill Builder','https://skillbuilder.aws/')]
    learning=[]; seen=set()
    for i,g in enumerate(gaps + req + ['Git/GitHub','DSA','Communication','System Design']):
        if g.lower() in seen: continue
        seen.add(g.lower()); platform,url=learning_platforms[i%len(learning_platforms)]
        learning.append({'title':f'Learn {g}','description':f'Complete a focused {g} learning task and produce a small proof of learning for your target role.','level':'Recommended','platform':platform,'platform_url':url,'task_type':'learning'})
        if len(learning)>=12: break
    project_ideas=[('Personalized Career Dashboard','Build a student career dashboard with authentication, analytics and recommendations.'),('AI Resume Analyzer','Build a resume analyzer that extracts skills and suggests improvements.'),('Student Performance Predictor','Create a model that analyzes academic and coding signals to predict learning needs.'),('DSA Progress Tracker','Build a tracker for coding-platform problems, difficulty and weekly goals.'),('Job Skill Matcher','Match a resume/profile to role requirements using explainable skill scoring.'),('Hackathon Finder','Build a searchable hackathon aggregator with filters for skills and deadlines.'),('Expense & Budget API','Create a secure backend API with authentication, categories and analytics.'),('Real-Time Chat App','Build a full-stack chat application with rooms, authentication and deployment.'),('Course Recommendation Engine','Recommend learning resources from a student skill-gap profile.'),('Campus Event Platform','Create an event discovery and registration platform for college communities.'),('Cloud Deployment Monitor','Build a dashboard that tracks deployed services and health status.'),('Interview Practice Coach','Create an app that organizes technical questions by role and topic.')]
    projects_rec=[]
    for i,(title,desc) in enumerate(project_ideas):
        skills_for=req[:4] if i<3 else [req[i%len(req)],req[(i+1)%len(req)]]
        projects_rec.append({'title':title,'description':desc,'difficulty':'Intermediate' if i<8 else 'Advanced','duration':'2–6 weeks','skills':skills_for,'task_type':'project'})
    hack_platforms=[('Unstop','https://unstop.com/hackathons'),('Devfolio','https://devfolio.co/hackathons'),('MLH','https://mlh.io/')]
    hacks=[{'title':f'{pname} hackathon search','description':'Find a current event matching your skills. Verify the official event page for dates and eligibility.','mode':'Online / Hybrid','match_score':min(95,60+len(skills)*4),'platform':pname,'platform_url':url} for pname,url in hack_platforms for _ in range(2)]
    job_platforms=[('LinkedIn Jobs','https://www.linkedin.com/jobs/'),('Wellfound','https://wellfound.com/jobs'),('Internshala','https://internshala.com/'),('Indeed','https://in.indeed.com/'),('Cutshort','https://cutshort.io/'),('YC Jobs','https://www.ycombinator.com/jobs')]
    companies=[('Small/startup companies','Startup / early-stage roles'),('Growing tech companies','Software / product roles'),('Local technology companies','Developer / analyst roles'),('Small SaaS companies','Engineering / support roles'),('Product startups','Full-stack / backend roles'),('AI startups','AI / data roles')]
    jobs=[]
    for i,(company,job) in enumerate(companies):
        match=55+min(25,len(projects)*7)+sum(1 for n in req if n.lower() in have)*3; platform,url=job_platforms[i%len(job_platforms)]
        jobs.append({'company':company,'role':job,'match_score':min(95,match),'reason':'AI estimate based on your profile. Search and verify the actual opening before applying.','platform':platform,'platform_url':url,'company_size':'Startup / small / growing company'})
    return learning,projects_rec,hacks,jobs


def _fallback_action_tasks(s, skills, projects, coding):
    solved=sum(x.get('problems_solved') or 0 for x in coding)
    tasks=[]
    if len(skills)<5: tasks.append(('Add 2–3 verified technical skills','Improves skill evidence and matching accuracy.','HIGH'))
    if solved<50: tasks.append(('Solve 15 DSA problems','Build consistent problem-solving evidence.','HIGH'))
    elif solved<150: tasks.append(('Solve 20 medium-level DSA problems','Strengthen interview readiness.','HIGH'))
    else: tasks.append(('Take one timed DSA assessment','Maintain problem-solving speed and accuracy.','MEDIUM'))
    if len(projects)<3: tasks.append(('Build one production-style project','Increases portfolio depth and practical evidence.','HIGH'))
    tasks += [('Improve GitHub README for your strongest project','Makes project impact easier to verify.','MEDIUM'),('Review 5 relevant opportunities','Build awareness of current role requirements.','MEDIUM'),('Practice 5 technical interview questions','Improve interview readiness.','MEDIUM')]
    return tasks


def _profile_payload(s, skills, projects, coding, academics, performance, certifications=None):
    return {
        'student': s,
        'skills': skills,
        'projects': projects,
        'coding': coding,
        'academics': academics,
        'performance': performance,
        'certifications': certifications or [],
    }


def _llm_client():
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None


def _json_response(client, system_prompt: str, user_payload: dict[str, Any], schema: dict[str, Any]):
    """Call the OpenAI Responses API and return parsed structured JSON."""
    model=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
    response=client.responses.create(
        model=model,
        instructions=system_prompt,
        input=json.dumps(user_payload, ensure_ascii=False),
        text={
            'format': {
                'type': 'json_schema',
                'name': schema['name'],
                'strict': True,
                'schema': schema['schema'],
            }
        },
        max_output_tokens=1800,
    )
    return json.loads(response.output_text)


ANALYSIS_SCHEMA={
    'name':'career_analysis',
    'schema':{
        'type':'object','additionalProperties':False,
        'properties':{
            'summary':{'type':'string'},
            'gaps':{'type':'array','items':{'type':'string'},'maxItems':6},
            'roadmap':{'type':'array','maxItems':5,'items':{'type':'object','additionalProperties':False,'properties':{'title':{'type':'string'},'description':{'type':'string'}},'required':['title','description']}},
            'score_adjustment_reason':{'type':'string'},
        },
        'required':['summary','gaps','roadmap','score_adjustment_reason']
    }
}

RECOMMENDATION_SCHEMA={
    'name':'career_recommendations','schema':{'type':'object','additionalProperties':False,'properties':{
      'learning':{'type':'array','maxItems':12,'items':{'type':'object','additionalProperties':False,'properties':{'title':{'type':'string'},'description':{'type':'string'},'level':{'type':'string'},'platform':{'type':'string'},'platform_url':{'type':'string'},'task_type':{'type':'string'}},'required':['title','description','level','platform','platform_url','task_type']}},
      'projects':{'type':'array','maxItems':12,'items':{'type':'object','additionalProperties':False,'properties':{'title':{'type':'string'},'description':{'type':'string'},'difficulty':{'type':'string'},'duration':{'type':'string'},'skills':{'type':'array','items':{'type':'string'}},'task_type':{'type':'string'}},'required':['title','description','difficulty','duration','skills','task_type']}},
      'hackathons':{'type':'array','maxItems':8,'items':{'type':'object','additionalProperties':False,'properties':{'title':{'type':'string'},'description':{'type':'string'},'mode':{'type':'string'},'match_score':{'type':'integer'},'platform':{'type':'string'},'platform_url':{'type':'string'}},'required':['title','description','mode','match_score','platform','platform_url']}},
      'jobs':{'type':'array','maxItems':10,'items':{'type':'object','additionalProperties':False,'properties':{'company':{'type':'string'},'role':{'type':'string'},'match_score':{'type':'integer'},'reason':{'type':'string'},'platform':{'type':'string'},'platform_url':{'type':'string'},'company_size':{'type':'string'}},'required':['company','role','match_score','reason','platform','platform_url','company_size']}}
    },'required':['learning','projects','hackathons','jobs']}
}


def analyze(s, skills, projects, coding, academics, performance, certifications=None):
    fallback=_fallback_analyze(s,skills,projects,coding,academics,performance)
    client=_llm_client()
    if not client:
        return fallback
    try:
        ai=_json_response(client,
            'You are CareerAI, a careful student career mentor. Analyze only the supplied student profile. Do not invent grades, skills, jobs, deadlines, or achievements. Identify realistic skill gaps and a practical roadmap. Keep advice age-appropriate and educational. Do not guarantee employment. Return concise structured JSON.',
            _profile_payload(s,skills,projects,coding,academics,performance,certifications),
            ANALYSIS_SCHEMA)
        fallback['summary']=ai['summary']
        fallback['gaps']=ai['gaps']
        fallback['roadmap']=ai['roadmap']
        return fallback
    except Exception:
        return fallback


def recommendations(s, skills, projects, coding, academics=None, performance=None, certifications=None):
    fallback=_fallback_recommendations(s,skills,projects,coding)
    client=_llm_client()
    if not client:
        return fallback
    try:
        ai=_json_response(client,
            'You are CareerAI. Create highly personalized educational and career recommendations from the supplied student profile. Return many options: up to 12 learning tasks, 12 portfolio projects, 8 hackathons and 10 company/job matches. Include startups, small companies, growing companies and local/smaller employers, not only famous MNCs. For learning use a known platform and its official home URL. For jobs use one of LinkedIn Jobs, Wellfound, Internshala, Indeed, Cutshort or YC Jobs. For hackathons use one of Unstop, Devfolio or MLH. Do not invent live openings, event dates, deadlines or URLs. Clearly label opportunity matches as estimates and tell the student to verify the official page. Never guarantee hiring. Make recommendations meaningfully different when profiles differ.',
            _profile_payload(s,skills,projects,coding,academics or [],performance or [],certifications or []),
            RECOMMENDATION_SCHEMA)
        for job in ai['jobs']:
            job['match_score']=max(0,min(100,int(job['match_score'])))
        for hack in ai['hackathons']:
            hack['match_score']=max(0,min(100,int(hack['match_score'])))
        return ai['learning'],ai['projects'],ai['hackathons'],ai['jobs']
    except Exception:
        return fallback


def action_tasks(s, skills, projects, coding, academics=None, performance=None):
    return _fallback_action_tasks(s,skills,projects,coding)


def mentor_answer(s, skills, projects, coding, academics, performance, certifications, question):
    fallback=f"Based on your profile, your target is {s.get('target_role') or 'your target role'}. Ask me about learning, DSA, projects, internships, or improving your score."
    client=_llm_client()
    if not client:
        return fallback
    try:
        response=client.responses.create(
            model=os.getenv('OPENAI_MODEL','gpt-5.6-luna'),
            instructions='You are CareerAI, a supportive student career mentor. Answer using only the supplied profile and question. Give practical, concise educational guidance. Never guarantee admission, internships or jobs. Do not invent current openings or deadlines. Do not ask for passwords, API keys, or other secrets.',
            input=json.dumps({'profile':_profile_payload(s,skills,projects,coding,academics,performance,certifications),'question':question},ensure_ascii=False),
            max_output_tokens=500,
        )
        return response.output_text.strip() or fallback
    except Exception:
        return fallback
