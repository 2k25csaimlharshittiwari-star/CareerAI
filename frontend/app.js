const API_BASE = '/api';
const TOKEN_KEY = 'careerai_access_token';
const ID_KEY = 'careerai_student_id';
let dashboard = null;
let student = null;

const $ = (id) => document.getElementById(id);
const token = () => localStorage.getItem(TOKEN_KEY);
const studentId = () => localStorage.getItem(ID_KEY);
const val = (id) => $(id)?.value?.trim() || '';
const num = (id) => val(id) === '' ? null : Number(val(id));

function toast(message, error=false){const t=$('toast');t.textContent=message;t.style.background=error?'#9b3f4d':'#172033';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800)}
function setLoading(v){$('loading').classList.toggle('hidden',!v)}
function initials(name='CA'){return name.split(' ').map(x=>x[0]).join('').slice(0,2).toUpperCase()}
function escapeHtml(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]))}
function arr(v){return Array.isArray(v)?v:[]}
function pretty(s){return String(s).replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase())}

async function api(path, options={}){
  const headers = {...(options.headers||{})};
  if(!(options.body instanceof FormData) && options.body !== undefined) headers['Content-Type']='application/json';
  if(token()) headers.Authorization = `Bearer ${token()}`;
  const res = await fetch(`${API_BASE}${path}`, {...options, headers});
  const text = await res.text();
  let data; try{data=text?JSON.parse(text):{}}catch{data={detail:text}}
  if(!res.ok){if(res.status===401){logout(false);toast('Session expired. Please sign in again.',true)}throw new Error(data.detail||`Request failed (${res.status})`)}
  return data;
}

function showAuth(tab='login'){$('authView').classList.remove('hidden');$('appView').classList.add('hidden');document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));$('loginForm').classList.toggle('hidden',tab!=='login');$('registerForm').classList.toggle('hidden',tab!=='register')}
function showApp(){$('authView').classList.add('hidden');$('appView').classList.remove('hidden')}

async function login(email,password){const data=await api('/auth/login',{method:'POST',body:JSON.stringify({email,password})});localStorage.setItem(TOKEN_KEY,data.access_token);localStorage.setItem(ID_KEY,data.student_id);toast('Signed in successfully.');await boot()}
async function register(name,email,password){await api('/auth/register',{method:'POST',body:JSON.stringify({name,email,password})});await login(email,password)}

async function boot(){
  if(!token()||!studentId()){showAuth();return}
  try{setLoading(true);student=await api('/auth/me');showApp();renderIdentity();await loadDashboard();await loadProfileData();
    if(!hasCoreProfile()) openSection('profile');
  }catch(e){toast(e.message,true);showAuth()}finally{setLoading(false)}
}
function hasCoreProfile(){return !!(student.college||student.target_role||student.degree||student.cgpa)}
function openSection(section){document.querySelectorAll('.nav-item').forEach(x=>x.classList.toggle('active',x.dataset.section===section));document.querySelectorAll('.page-section').forEach(x=>x.classList.toggle('hidden',x.id!==section));const names={overview:'Overview',profile:'Profile',learning:'Learning',projects:'Projects',opportunities:'Opportunities',resume:'Resume Analyzer',progress:'Progress',settings:'Settings',action:'Weekly plan',mentor:'AI Mentor'};$('sectionName').textContent=names[section];$('pageTitle').textContent=section==='overview'?'Career dashboard':names[section];if(section==='profile')loadProfileData(); if(section==='resume')loadResumeHistory(); if(section==='progress')renderProgress();}

async function loadDashboard(){try{dashboard=await api(`/students/${studentId()}/career-dashboard`);renderDashboard()}catch(e){toast(e.message,true)}}
function renderIdentity(){const name=student.name||'Student';$('welcomeTitle').textContent=`Welcome back, ${name.split(' ')[0]}`;$('welcomeSub').textContent=`Target role: ${student.target_role||'Define your target role'} · Add your evidence to unlock personalized recommendations.`;$('avatar').textContent=initials(name)}
function renderDashboard(){
  const d=dashboard||{}, cr=d.career_readiness||{}, stats=d.profile_statistics||{};
  $('overallScore').textContent=cr.overall_score??0;$('overallBar').style.width=`${Math.min(100,Math.max(0,cr.overall_score||0))}%`;$('analysisSummary').textContent=cr.summary||'Complete your profile to generate a stronger career analysis.';
  $('skillsCount').textContent=stats.skills||0;$('projectsCount').textContent=stats.projects||0;$('certsCount').textContent=stats.certifications||0;
  const bd=cr.score_breakdown||{};$('breakdown').innerHTML=Object.entries(bd).map(([k,v])=>{const is10=['technical','recent_performance'].includes(k);const width=is10?Math.min(100,(Number(v)||0)*10):Math.min(100,Number(v)||0);const shown=is10?`${v}/10`:v;return `<div class="bar-row"><span>${pretty(k)}</span><div class="bar"><i style="width:${width}%"></i></div><b>${shown}</b></div>`}).join('')||'<p class="muted">Complete your profile to see the breakdown.</p>';
  $('gaps').innerHTML=(d.skill_gaps||[]).map(x=>`<span class="tag">${escapeHtml(typeof x==='string'?x:(x.skill||x.name||JSON.stringify(x)))}</span>`).join('')||'<span class="muted">Add skills and a target role to generate skill gaps.</span>';
  const roadmap=d.roadmap||[];$('roadmap').innerHTML=(Array.isArray(roadmap)?roadmap:Object.entries(roadmap).map(([k,v])=>({title:k,description:v}))).map((x,i)=>`<div class="roadmap-step"><span class="pill">STEP ${i+1}</span><b>${escapeHtml(x.title||x.phase||x.name||'Focus area')}</b><p>${escapeHtml(x.description||x.action||x.details||String(x))}</p></div>`).join('')||'<p class="muted">Your roadmap will appear after analysis.</p>';
  renderCards();renderActions();
}
function normalizeRecommendation(x){if(typeof x==='string')return {title:x,description:'Recommended based on your current profile.'};return x||{}}
function card(x,type){x=normalizeRecommendation(x);const title=x.title||x.name||x.role||x.company||x.position||x.course||x.topic||'Recommendation';const desc=x.description||x.reason||x.summary||x.details||x.why||x.about||'Personalized recommendation based on your profile.';const meta=[];['level','duration','skills','match_score','score','location','mode','company','platform','company_size'].forEach(k=>{if(x[k]!==undefined&&x[k]!==null)meta.push(`<span class="pill">${escapeHtml(pretty(k))}: ${escapeHtml(Array.isArray(x[k])?x[k].join(', '):x[k])}</span>`)});let action='';if(type==='LEARN'){action=`<div class="recommend-actions"><a class="ghost" href="${escapeHtml(x.platform_url||'#')}" target="_blank" rel="noopener">Open ${escapeHtml(x.platform||'learning platform')}</a><button class="primary" data-learn-title="${escapeHtml(title)}">✓ Mark task complete</button></div>`}else if(type==='PROJECT'){action=`<div class="project-complete-box"><input type="file" data-project-file="${escapeHtml(title)}" accept=".zip,.pdf,.docx,.txt"><button class="primary" data-project-title="${escapeHtml(title)}">✓ Upload & complete project</button></div>`}else if(type==='COMPANY MATCH'||type==='HACKATHON'){action=`<div class="recommend-actions"><a class="ghost" href="${escapeHtml(x.platform_url||'#')}" target="_blank" rel="noopener">Find on ${escapeHtml(x.platform||'platform')}</a></div>`}return `<article class="recommend-card"><span class="pill">${type}</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(desc)}</p><div class="card-meta">${meta.join('')}</div>${action}</article>`}
function renderCards(){
  $('learningGrid').innerHTML=arr(dashboard?.learning_recommendations).slice(0,4).map(x=>card(x,'LEARN')).join('')||empty('Complete your current learning task to unlock the next one.');
  $('projectGrid').innerHTML=arr(dashboard?.project_recommendations).slice(0,6).map(x=>card(x,'PROJECT')).join('')||empty('Complete your current project to unlock the next project.');
  $('jobGrid').innerHTML=arr(dashboard?.job_recommendations).map(x=>card(x,'COMPANY MATCH')).join('')||empty('Add skills, projects and a target role to generate matches.');
  $('hackGrid').innerHTML=arr(dashboard?.hackathon_recommendations).map(x=>card(x,'HACKATHON')).join('')||empty('Add your skills and target role to generate hackathon matches.');
  document.querySelectorAll('[data-learn-title]').forEach(btn=>btn.addEventListener('click',async()=>{try{await api(`/students/${studentId()}/learning-complete`,{method:'POST',body:JSON.stringify({title:btn.dataset.learnTitle})});toast('Completed. Your next learning task is ready.');await loadDashboard()}catch(e){toast(e.message,true)}}));
  document.querySelectorAll('[data-project-title]').forEach(btn=>btn.addEventListener('click',async()=>{const title=btn.dataset.projectTitle;const selector=`[data-project-file="${CSS.escape(title)}"]`;const file=document.querySelector(selector)?.files?.[0];if(!file){toast('Upload your project file first.',true);return}const fd=new FormData();fd.append('title',title);fd.append('project_file',file);try{setLoading(true);await api(`/students/${studentId()}/project-complete`,{method:'POST',body:fd});toast('Project completed. Your next project is ready.');await loadDashboard()}catch(e){toast(e.message,true)}finally{setLoading(false)}}));
}
function empty(t){return `<div class="panel empty-state"><p class="muted">${escapeHtml(t)}</p><button class="ghost" onclick="openSection('profile')">Complete profile</button></div>`}
function renderActions(){const a=dashboard?.action_plan||{};const tasks=arr(a.tasks);const s=a.summary||{};$('actionSummary').innerHTML=Object.entries(s).map(([k,v])=>`<div class="summary-chip"><b>${v}</b>${pretty(k)}</div>`).join('');$('taskList').innerHTML=tasks.map((t,i)=>`<label class="task"><input type="checkbox" data-task-index="${i}" ${t.completed?'checked':''}><div class="task-main"><b>${escapeHtml(t.title||t.task||`Action ${i+1}`)}</b><p>${escapeHtml(t.impact||t.description||'Build measurable career progress this week.')}</p></div><span class="priority">${escapeHtml(t.priority||'HIGH')}</span></label>`).join('')||empty('Complete your profile to generate a useful weekly plan.');document.querySelectorAll('[data-task-index]').forEach(cb=>cb.addEventListener('change',()=>updateTask(cb.dataset.taskIndex,cb.checked)))}
async function updateTask(index,completed){const t=arr((dashboard?.action_plan||{}).tasks)[Number(index)];if(!t)return;const id=t.id||t.task_id;if(!id){t.completed=completed;return renderActions()}try{await api(`/students/${studentId()}/tasks/${id}`,{method:'PATCH',body:JSON.stringify({completed})});toast(completed?'Task completed':'Task reopened')}catch(e){toast(e.message,true)}}
async function recompute(){try{setLoading(true);await api(`/students/${studentId()}/analysis`,{method:'POST'});await api(`/students/${studentId()}/learning-recommendations`,{method:'POST'});await api(`/students/${studentId()}/project-recommendations`,{method:'POST'});await api(`/students/${studentId()}/hackathon-recommendations`,{method:'POST'});await api(`/students/${studentId()}/job-recommendations`,{method:'POST'});await api(`/students/${studentId()}/action-plan`,{method:'POST'});await loadDashboard();toast('AI career insights refreshed.')}catch(e){toast(e.message,true)}finally{setLoading(false)}}

function setIf(id,v){if($(id))$(id).value=v??''}
function getSemesterLimit(degree){
  const d=(degree||'').toLowerCase().replace(/[.\-]/g,' ');
  if(/\b(phd|ph\.d|doctorate|doctoral)\b/.test(d)) return {min:1,max:12,label:'Doctorate (PhD): 3–6 years → 6–12 semesters'};
  if(/\b(master|masters|m tech|mtech|mca|mba|msc|m sc|ma|m com|mcom)\b/.test(d)) return {min:1,max:4,label:'Master’s degree: 1–2 years → 2–4 semesters'};
  if(/\b(bachelor|bachelor s|b tech|btech|bca|bsc|b sc|ba|b com|bcom|be|b e|bba)\b/.test(d)) return {min:1,max:8,label:'Bachelor’s degree: 3–4 years → 6–8 semesters'};
  if(/\b(diploma|certificate)\b/.test(d)) return {min:1,max:4,label:'Diploma / Certificate: 1–2 years → 2–4 semesters'};
  return {min:1,max:12,label:'Select a recognized program type to set the semester limit.'};
}
function updateSemesterLimit(){
  const degree=val('pDegree');
  const input=$('pSemester');
  const hint=$('semesterHint');
  if(!input) return;
  const limit=getSemesterLimit(degree);
  input.min=limit.min;
  input.max=limit.max;
  if(Number(input.value)>limit.max) input.value='';
  if(hint) hint.textContent=limit.label;
}
function fillProfileForm(){
  const s=student||{};setIf('pCollege',s.college);setIf('pDegree',s.degree);setIf('pBranch',s.branch);setIf('pYear',s.year);setIf('pSemester',s.semester);setIf('pLocation',s.location);setIf('pCgpa',s.cgpa);setIf('pTenth',s.tenth);setIf('pTwelfth',s.twelfth);setIf('pBacklogs',s.backlogs);setIf('pRole',s.target_role);setIf('pGoal',s.career_goal);updateSemesterLimit();
}
function profileCompleteness(){const checks=[['Academic basics',!!(student?.college&&student?.degree&&student?.branch)],['Career target',!!student?.target_role],['Academic scores',!!(student?.cgpa||student?.tenth||student?.twelfth)],['Technical skills',(dashboard?.profile_statistics?.skills||0)>0],['Projects',(dashboard?.profile_statistics?.projects||0)>0],['Coding progress',arr(dashboard?.coding).length>0],['Certifications',(dashboard?.profile_statistics?.certifications||0)>0],['Recent performance',arr(dashboard?.performance).length>0]];const complete=checks.filter(x=>x[1]).length;return {checks,percent:Math.round(complete/checks.length*100)}}
function renderProfileStatus(){const {checks,percent}=profileCompleteness();$('profilePercent').textContent=`${percent}%`;$('baseCompletion').textContent=`${Math.round([student?.college,student?.degree,student?.branch,student?.year,student?.semester,student?.target_role].filter(Boolean).length/6*100)}%`;$('profileChecklist').innerHTML=checks.map(([name,ok])=>`<div class="check-item ${ok?'done':''}"><span>${ok?'✓':'○'}</span>${name}</div>`).join('');$('profileStatus').innerHTML=percent<75?`<strong>Profile is ${percent}% complete.</strong> Add more evidence below, then click <b>Analyze my career readiness</b>.`:`<strong>Great — your profile is ${percent}% complete.</strong> Re-run the AI analysis whenever you add new evidence.`}

async function loadProfileData(){try{student=await api(`/students/${studentId()}`);fillProfileForm();const d=dashboard||{};renderProfileLists(d);renderProfileStatus()}catch(e){toast(e.message,true)}}
function renderProfileLists(d){
  const skills=arr(d.skills||d.student?.skills);$('skillList').innerHTML=skills.map(x=>`<span class="chip"><b>${escapeHtml(x.name)}</b> · ${escapeHtml(x.level||'')}</span>`).join('')||'<span class="muted">No skills added yet.</span>';
  const projects=arr(d.projects||d.student?.projects);$('projectList').innerHTML=projects.map(x=>`<div class="mini-item"><b>${escapeHtml(x.name)}</b><span>${escapeHtml(x.technologies||'')}</span></div>`).join('')||'<span class="muted">No projects added yet.</span>';
  const coding=arr(d.coding||d.student?.coding);$('codingList').innerHTML=coding.map(x=>`<div class="mini-item"><b>${escapeHtml(x.platform||'Coding')}</b><span>${x.problems_solved||0} solved · E ${x.easy||0} · M ${x.medium||0} · H ${x.hard||0}</span></div>`).join('')||'<span class="muted">No coding record added yet.</span>';
  const certs=arr(d.certifications||d.student?.certifications);$('certList').innerHTML=certs.map(x=>`<div class="mini-item"><b>${escapeHtml(x.name)}</b><span>${escapeHtml(x.platform||x.issuer||'')}</span></div>`).join('')||'<span class="muted">No certifications added yet.</span>';
  const academics=arr(d.academics||d.student?.academics);$('academicList').innerHTML=academics.map(x=>`<div class="mini-item"><b>${escapeHtml(x.term)}</b><span>CGPA ${x.cgpa??'—'} · Attendance ${x.attendance??'—'}%</span></div>`).join('')||'<span class="muted">No academic history added yet.</span>';
  const perf=arr(d.performance||d.student?.performance);$('performanceList').innerHTML=perf.map(x=>`<div class="mini-item"><b>${escapeHtml(x.category)}</b><span>${x.score}/10 · ${escapeHtml(x.note||'')}</span></div>`).join('')||'<span class="muted">No performance record added yet.</span>';
}
async function saveProfile(e){e.preventDefault();const body={};const fields=[['college','pCollege'],['degree','pDegree'],['branch','pBranch'],['year','pYear'],['semester','pSemester'],['location','pLocation'],['cgpa','pCgpa'],['tenth','pTenth'],['twelfth','pTwelfth'],['backlogs','pBacklogs'],['target_role','pRole'],['career_goal','pGoal']];for(const [k,id] of fields){const v=val(id);if(v!=='')body[k]=['year','semester','backlogs'].includes(k)?Number(v):['cgpa','tenth','twelfth'].includes(k)?Number(v):v}try{setLoading(true);student=await api(`/students/${studentId()}`,{method:'PATCH',body:JSON.stringify(body)});toast('Profile saved. AI is updating your insights…');await recompute();await loadProfileData();}catch(e){toast(e.message,true)}finally{setLoading(false)}}
async function addResource(path,body,formId){try{setLoading(true);await api(`/students/${studentId()}/${path}`,{method:'POST',body:JSON.stringify(body)});$(formId).reset();toast('Saved successfully.');await loadDashboard();await loadProfileData()}catch(e){toast(e.message,true)}finally{setLoading(false)}}

async function mentor(message){const data=await api(`/students/${studentId()}/mentor`,{method:'POST',body:JSON.stringify({question:message})});return data.response||data.message||data.answer||data.detail||JSON.stringify(data)}
function addChat(text,user=false){const box=$('chatMessages');const el=document.createElement('div');el.className=`chat ${user?'user-msg':''}`;el.innerHTML=user?`<div>${escapeHtml(text)}</div>`:`<div class="chat-avatar">CA</div><div>${escapeHtml(text)}</div>`;box.appendChild(el);box.scrollTop=box.scrollHeight}

async function analyzeResume(e){e.preventDefault();const file=$('resumeFile').files[0];if(!file)return;const fd=new FormData();fd.append('resume',file);try{setLoading(true);const data=await api(`/students/${studentId()}/resume-analysis`,{method:'POST',body:fd});const a=data.analysis||{};$('resumeResult').innerHTML=`<div class="score-line"><span>${a.resume_score??0}</span><small>/100</small></div><p>${escapeHtml(a.role_alignment||'')}</p><h4>Detected keywords</h4><div class="tag-list">${arr(a.detected_keywords).map(x=>`<span class="tag">${escapeHtml(x)}</span>`).join('')||'<span class="muted">None detected</span>'}</div><h4>Improvements</h4><ul>${arr(a.improvements).map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul>`;await loadResumeHistory();toast('Resume analyzed successfully.')}catch(err){toast(err.message,true)}finally{setLoading(false)}}
async function loadResumeHistory(){try{const items=await api(`/students/${studentId()}/resume-analyses`);$('resumeHistory').innerHTML=items.map(x=>`<div class="mini-item"><b>${escapeHtml(x.filename)}</b><span>Score ${x.resume_score}/100 · ${escapeHtml(x.created_at||'')}</span></div>`).join('')||'<span class="muted">No resume analyses yet.</span>'}catch(e){toast(e.message,true)}}
function renderProgress(){const {percent}=profileCompleteness();$('progressProfile').textContent=`${percent}%`;$('progressScore').textContent=dashboard?.career_readiness?.overall_score??'—';$('progressCoding').textContent=arr(dashboard?.coding).reduce((n,x)=>n+(Number(x.problems_solved)||0),0);$('progressProjects').textContent=dashboard?.profile_statistics?.projects||0;const checks=[['Profile basics',!!(student?.college&&student?.degree)],['Target role',!!student?.target_role],['Skills',(dashboard?.profile_statistics?.skills||0)>0],['Projects',(dashboard?.profile_statistics?.projects||0)>0],['Coding evidence',arr(dashboard?.coding).length>0],['Academic history',arr(dashboard?.academics).length>0],['Recent performance',arr(dashboard?.performance).length>0],['Resume analyzed',false]];$('progressEvidence').innerHTML=checks.map(([n,ok])=>`<div class="check-item ${ok?'done':''}"><span>${ok?'✓':'○'}</span>${n}</div>`).join('')}
async function deleteAccount(){if(!confirm('Delete your CareerAI account and all associated data? This cannot be undone.'))return;try{setLoading(true);await api(`/students/${studentId()}/account`,{method:'DELETE'});logout(false);toast('Account deleted.')}catch(e){toast(e.message,true)}finally{setLoading(false)}}
function logout(show=true){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(ID_KEY);dashboard=null;student=null;showAuth('login');if(show)toast('Logged out.')}

// Navigation
 document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>showAuth(b.dataset.tab)));
document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>openSection(b.dataset.section)));
$('loginForm').addEventListener('submit',async e=>{e.preventDefault();try{setLoading(true);await login(val('loginEmail'),$('loginPassword').value)}catch(err){toast(err.message,true)}finally{setLoading(false)}});
$('registerForm').addEventListener('submit',async e=>{e.preventDefault();try{setLoading(true);await register(val('regName'),val('regEmail'),$('regPassword').value)}catch(err){toast(err.message,true)}finally{setLoading(false)}});
$('logoutBtn').addEventListener('click',()=>logout());$('refreshBtn').addEventListener('click',async()=>{await loadDashboard();await loadProfileData()});$('recomputeBtn').addEventListener('click',recompute);
$('studentProfileForm').addEventListener('submit',saveProfile);
$('pDegree').addEventListener('input',updateSemesterLimit);
$('pDegree').addEventListener('change',updateSemesterLimit);
$('pSemester').addEventListener('input',()=>{const limit=getSemesterLimit(val('pDegree'));const n=Number(val('pSemester'));if(n>limit.max)$('pSemester').value=limit.max;});
updateSemesterLimit();
$('skillForm').addEventListener('submit',e=>{e.preventDefault();addResource('skills',{name:val('skillName'),level:val('skillLevel'),score:num('skillScore')},'skillForm')});
$('projectForm').addEventListener('submit',e=>{e.preventDefault();addResource('projects',{name:val('projectName'),description:val('projectDescription'),technologies:val('projectTech'),github_url:val('projectGithub')||null,live_url:val('projectLive')||null},'projectForm')});
$('codingForm').addEventListener('submit',e=>{e.preventDefault();addResource('coding',{platform:val('codingPlatform'),problems_solved:num('codingProblems')||0,easy:num('codingEasy')||0,medium:num('codingMedium')||0,hard:num('codingHard')||0,rating:num('codingRating')},'codingForm')});
$('certForm').addEventListener('submit',e=>{e.preventDefault();addResource('certifications',{name:val('certName'),platform:val('certPlatform'),issuer:val('certIssuer'),url:val('certUrl')||null},'certForm')});
$('academicForm').addEventListener('submit',e=>{e.preventDefault();addResource('academics',{term:val('academicTerm'),cgpa:num('academicCgpa'),attendance:num('academicAttendance'),backlogs:num('academicBacklogs')||0},'academicForm')});
$('performanceForm').addEventListener('submit',e=>{e.preventDefault();addResource('performance',{category:val('performanceCategory'),score:num('performanceScore'),note:val('performanceNote')},'performanceForm')});
$('analyzeFromProfile').addEventListener('click',recompute); $('resumeForm').addEventListener('submit',analyzeResume); $('deleteAccountBtn').addEventListener('click',deleteAccount);
$('mentorForm').addEventListener('submit',async e=>{e.preventDefault();const input=$('mentorInput');const msg=input.value.trim();if(!msg)return;input.value='';addChat(msg,true);try{addChat(await mentor(msg))}catch(err){addChat(`I couldn't answer right now: ${err.message}`)}});
boot();
