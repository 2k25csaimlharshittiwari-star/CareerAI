import json, uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.database import connect
from app.deps import current_student, owned
from app.schemas import ProfileUpdate, SkillIn, ProjectIn, CertIn, AcademicIn, CodingIn, PerformanceIn, TaskUpdate, MentorIn
from app.services.ai_service import analyze, recommendations, action_tasks, mentor_answer
from app.services.resume_service import analyze_resume
from app.config import UPLOAD_DIR, MAX_UPLOAD_MB

router = APIRouter(prefix='/students', tags=['Students'])
RESOURCE_TABLES = {'skills','projects','certifications','academics','coding','performance'}

def get_student(sid):
    con=connect(); row=con.execute('SELECT * FROM students WHERE id=?',(sid,)).fetchone(); con.close()
    if not row: raise HTTPException(404,'Student not found')
    return dict(row)

def rows(table,sid):
    con=connect(); data=[dict(x) for x in con.execute(f'SELECT * FROM {table} WHERE student_id=? ORDER BY id',(sid,)).fetchall()]; con.close(); return data

def context(sid): return get_student(sid),rows('skills',sid),rows('projects',sid),rows('coding',sid),rows('academics',sid),rows('performance',sid),rows('certifications',sid)

def insert_resource(table, sid, data):
    if table not in RESOURCE_TABLES: raise HTTPException(400,'Unsupported resource')
    clean={k:v for k,v in data.items() if v is not None}
    con=connect(); cols=', '.join(['student_id']+list(clean)); qs=', '.join(['?']*(len(clean)+1)); cur=con.execute(f'INSERT INTO {table} ({cols}) VALUES ({qs})',(sid,*clean.values())); con.commit(); row=con.execute(f'SELECT * FROM {table} WHERE id=?',(cur.lastrowid,)).fetchone(); con.close(); return dict(row)

@router.get('/{student_id}')
def get_one(student_id:int, me=Depends(current_student)):
    owned(student_id,me); s,skills,projects,coding,academics,perf,certs=context(student_id)
    return {**s,'skills':skills,'projects':projects,'coding':coding,'academics':academics,'performance':perf,'certifications':certs}

@router.patch('/{student_id}')
def update_profile(student_id:int,p:ProfileUpdate,me=Depends(current_student)):
    owned(student_id,me); data=p.model_dump(exclude_unset=True)
    if data:
      con=connect(); con.execute('UPDATE students SET '+','.join(f'{k}=?' for k in data)+' WHERE id=?',tuple(data.values())+(student_id,)); con.commit(); con.close()
    return get_one(student_id,me)

@router.post('/{student_id}/skills')
def add_skill(student_id:int,x:SkillIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('skills',student_id,x.model_dump())
@router.post('/{student_id}/projects')
def add_project(student_id:int,x:ProjectIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('projects',student_id,x.model_dump())
@router.post('/{student_id}/certifications')
def add_cert(student_id:int,x:CertIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('certifications',student_id,x.model_dump())
@router.post('/{student_id}/academics')
def add_academic(student_id:int,x:AcademicIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('academics',student_id,x.model_dump())
@router.post('/{student_id}/coding')
def add_coding(student_id:int,x:CodingIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('coding',student_id,x.model_dump())
@router.post('/{student_id}/performance')
def add_perf(student_id:int,x:PerformanceIn,me=Depends(current_student)): owned(student_id,me); return insert_resource('performance',student_id,x.model_dump())

@router.delete('/{student_id}/{resource}/{resource_id}')
def delete_resource(student_id:int,resource:str,resource_id:int,me=Depends(current_student)):
    owned(student_id,me)
    if resource not in RESOURCE_TABLES: raise HTTPException(400,'Unsupported resource')
    con=connect(); cur=con.execute(f'DELETE FROM {resource} WHERE id=? AND student_id=?',(resource_id,student_id)); con.commit(); con.close()
    if cur.rowcount == 0: raise HTTPException(404,'Resource not found')
    return {'message':'Deleted successfully'}

def _completed_titles(student_id:int, table:str):
    con=connect(); out={r['title'] for r in con.execute(f'SELECT title FROM {table} WHERE student_id=? AND completed=1',(student_id,)).fetchall()}; con.close(); return out

@router.get('/{student_id}/recommendation-progress')
def recommendation_progress(student_id:int,me=Depends(current_student)):
    owned(student_id,me); con=connect(); learning=[dict(r) for r in con.execute('SELECT * FROM learning_progress WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]; projects=[dict(r) for r in con.execute('SELECT * FROM project_progress WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]; con.close(); return {'learning':learning,'projects':projects}

@router.post('/{student_id}/learning-complete')
def learning_complete(student_id:int,payload:dict,me=Depends(current_student)):
    owned(student_id,me); title=str(payload.get('title','')).strip()
    if not title: raise HTTPException(400,'Learning task title is required.')
    con=connect(); con.execute('INSERT INTO learning_progress(student_id,title,completed,completed_at) VALUES(?,?,1,?) ON CONFLICT(student_id,title) DO UPDATE SET completed=1,completed_at=excluded.completed_at',(student_id,title,datetime.utcnow().isoformat())); con.commit(); con.close(); return {'message':'Learning task completed. A new task is now available.','title':title}

@router.post('/{student_id}/project-complete')
async def project_complete(student_id:int,title:str=Form(...),project_file:UploadFile|None=File(default=None),me=Depends(current_student)):
    owned(student_id,me); title=title.strip()
    if not title: raise HTTPException(400,'Project title is required.')
    file_name=None; file_path=None
    if project_file:
        allowed={'.zip','.pdf','.docx','.txt'}; suffix=Path(project_file.filename or '').suffix.lower()
        if suffix not in allowed: raise HTTPException(400,'Upload a ZIP, PDF, DOCX or TXT project file.')
        raw=await project_file.read()
        if len(raw)>20*1024*1024: raise HTTPException(413,'Project upload must be smaller than 20 MB.')
        file_name=project_file.filename; safe=f'{student_id}_{uuid.uuid4().hex}{suffix}'; (UPLOAD_DIR/safe).write_bytes(raw); file_path=str(UPLOAD_DIR/safe)
    con=connect(); con.execute('INSERT INTO project_progress(student_id,title,completed,file_name,file_path,completed_at) VALUES(?,?,1,?,?,?) ON CONFLICT(student_id,title) DO UPDATE SET completed=1,file_name=excluded.file_name,file_path=excluded.file_path,completed_at=excluded.completed_at',(student_id,title,file_name,file_path,datetime.utcnow().isoformat())); con.commit(); con.close(); return {'message':'Project marked complete. Your next project is now available.','title':title,'file_name':file_name}

@router.post('/{student_id}/analysis')
def run_analysis(student_id:int,me=Depends(current_student)):
    owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); result=analyze(s,sk,pr,co,ac,pe,ce)
    con=connect(); con.execute('INSERT INTO analyses(student_id,overall,summary,gaps,roadmap,score_breakdown) VALUES(?,?,?,?,?,?)',(student_id,result['overall'],result['summary'],json.dumps(result['gaps']),json.dumps(result['roadmap']),json.dumps(result['score_breakdown']))); con.commit(); con.close(); return result

@router.post('/{student_id}/learning-recommendations')
def learning(student_id:int,me=Depends(current_student)): owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); return recommendations(s,sk,pr,co,ac,pe,ce)[0]
@router.post('/{student_id}/project-recommendations')
def projrec(student_id:int,me=Depends(current_student)): owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); return recommendations(s,sk,pr,co,ac,pe,ce)[1]
@router.post('/{student_id}/hackathon-recommendations')
def hackrec(student_id:int,me=Depends(current_student)): owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); return recommendations(s,sk,pr,co,ac,pe,ce)[2]
@router.post('/{student_id}/job-recommendations')
def jobrec(student_id:int,me=Depends(current_student)): owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); return recommendations(s,sk,pr,co,ac,pe,ce)[3]
@router.post('/{student_id}/internship-recommendations')
def internshiprec(student_id:int,me=Depends(current_student)):
    owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); _,_,_,jobs=recommendations(s,sk,pr,co,ac,pe,ce)
    return [{'company':x['company'],'role':f"{x['role']} / Internship","match_score":x['match_score'],'status':'AI estimate — verify the official opening before applying.'} for x in jobs]

@router.post('/{student_id}/action-plan')
def action(student_id:int,me=Depends(current_student)):
    owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); wanted=action_tasks(s,sk,pr,co); con=connect(); con.execute('DELETE FROM tasks WHERE student_id=? AND completed=0',(student_id,));
    for title,impact,priority in wanted: con.execute('INSERT INTO tasks(student_id,title,impact,priority) VALUES(?,?,?,?)',(student_id,title,impact,priority))
    con.commit(); con.close(); return {'tasks':rows('tasks',student_id),'summary':{'total':len(wanted),'high_priority':sum(1 for x in wanted if x[2]=='HIGH')}}

@router.get('/{student_id}/tasks')
def tasks(student_id:int,me=Depends(current_student)): owned(student_id,me); return rows('tasks',student_id)
@router.patch('/{student_id}/tasks/{task_id}')
def task(student_id:int,task_id:int,x:TaskUpdate,me=Depends(current_student)):
    owned(student_id,me); con=connect(); con.execute('UPDATE tasks SET completed=? WHERE id=? AND student_id=?',(int(x.completed),task_id,student_id)); con.commit(); row=con.execute('SELECT * FROM tasks WHERE id=? AND student_id=?',(task_id,student_id)).fetchone(); con.close()
    if not row: raise HTTPException(404,'Task not found')
    return dict(row)

@router.post('/{student_id}/mentor')
def mentor(student_id:int,payload:MentorIn,me=Depends(current_student)):
    owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id)
    answer=mentor_answer(s,sk,pr,co,ac,pe,ce,payload.question)
    return {'response':answer,'disclaimer':'AI guidance is informational and does not guarantee admission, internship or employment.'}

@router.post('/{student_id}/resume-analysis')
async def resume_analysis(student_id:int,resume:UploadFile=File(...),me=Depends(current_student)):
    owned(student_id,me)
    allowed={'application/pdf','text/plain','application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
    if resume.content_type not in allowed: raise HTTPException(400,'Upload a PDF, DOCX or TXT resume.')
    raw=await resume.read()
    if len(raw)>MAX_UPLOAD_MB*1024*1024: raise HTTPException(413,f'Resume must be smaller than {MAX_UPLOAD_MB} MB.')
    suffix=Path(resume.filename or '').suffix.lower()
    text=''
    try:
        if suffix=='.pdf':
            from pypdf import PdfReader
            import io
            text='\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(raw)).pages)
        elif suffix=='.docx':
            from docx import Document
            import io
            doc=Document(io.BytesIO(raw)); text='\n'.join(p.text for p in doc.paragraphs)
        else:
            text=raw.decode('utf-8','ignore')
    except Exception as exc:
        raise HTTPException(400,f'Could not read this resume: {exc}')
    student=get_student(student_id); result=analyze_resume(text,student.get('target_role'))
    filename=f'{student_id}_{uuid.uuid4().hex}{suffix}'
    (UPLOAD_DIR/filename).write_bytes(raw)
    con=connect(); con.execute('INSERT INTO resume_analyses(student_id,filename,resume_score,result_json) VALUES(?,?,?,?)',(student_id,resume.filename or 'resume',result['resume_score'],json.dumps(result))); con.commit(); con.close()
    return {'message':'Resume analyzed successfully','analysis':result,'filename':resume.filename}

@router.get('/{student_id}/resume-analyses')
def resume_history(student_id:int,me=Depends(current_student)):
    owned(student_id,me); con=connect(); out=[]
    for r in con.execute('SELECT id,filename,resume_score,created_at,result_json FROM resume_analyses WHERE student_id=? ORDER BY id DESC LIMIT 10',(student_id,)).fetchall():
        x=dict(r); x['result']=json.loads(x.pop('result_json')); out.append(x)
    con.close(); return out

@router.delete('/{student_id}/account')
def delete_account(student_id:int,me=Depends(current_student)):
    owned(student_id,me); con=connect(); con.execute('DELETE FROM students WHERE id=?',(student_id,)); con.commit(); con.close();
    return {'message':'Account and associated career data deleted.'}

@router.get('/{student_id}/career-dashboard')
def career_dashboard(student_id:int,me=Depends(current_student)):
    owned(student_id,me); s,sk,pr,co,ac,pe,ce=context(student_id); a=analyze(s,sk,pr,co,ac,pe,ce); l,p,h,j=recommendations(s,sk,pr,co,ac,pe,ce); completed_l=_completed_titles(student_id,'learning_progress'); completed_p=_completed_titles(student_id,'project_progress'); l=[x for x in l if x.get('title') not in completed_l]; p=[x for x in p if x.get('title') not in completed_p]; t=action_tasks(s,sk,pr,co)
    con=connect(); saved=[dict(x) for x in con.execute('SELECT * FROM tasks WHERE student_id=? ORDER BY id',(student_id,)).fetchall()]; con.close()
    if not saved: saved=[{'id':None,'title':x[0],'impact':x[1],'priority':x[2],'completed':0} for x in t]
    internships=[{'company':x['company'],'role':f"{x['role']} / Internship","match_score":x['match_score'],'status':'AI estimate — verify the official opening.'} for x in j]
    return {'student':s,'profile_statistics':{'skills':len(sk),'projects':len(pr),'certifications':len(ce),'coding_records':len(co),'performance_records':len(pe)},'career_readiness':{'overall_score':a['overall'],'summary':a['summary'],'score_breakdown':a['score_breakdown']},'skill_gaps':a['gaps'],'roadmap':a['roadmap'],'learning_recommendations':l,'project_recommendations':p,'hackathon_recommendations':h,'job_recommendations':j,'internship_recommendations':internships,'action_plan':{'summary':{'total':len(saved),'high_priority':sum(1 for x in saved if x.get('priority')=='HIGH')},'tasks':saved},'skills':sk,'projects':pr,'coding':co,'academics':ac,'performance':pe,'certifications':ce}
