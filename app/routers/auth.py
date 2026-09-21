from fastapi import APIRouter, Depends, HTTPException
from app.database import connect
from app.security import hash_password, verify_password, create_token
from app.deps import current_student
from app.schemas import RegisterIn, LoginIn

router = APIRouter(prefix='/auth', tags=['Authentication'])

@router.post('/register')
def register(data: RegisterIn):
    con = connect()
    if con.execute('SELECT id FROM students WHERE lower(email)=lower(?)', (str(data.email),)).fetchone():
        con.close(); raise HTTPException(409, 'Email already registered')
    cur = con.execute('INSERT INTO students(name,email,password_hash) VALUES(?,?,?)', (data.name.strip(), str(data.email).lower(), hash_password(data.password)))
    con.commit(); sid = cur.lastrowid; con.close()
    return {'message': 'Registration successful', 'student_id': sid, 'email': str(data.email).lower()}

@router.post('/login')
def login(data: LoginIn):
    con = connect(); row = con.execute('SELECT * FROM students WHERE lower(email)=lower(?)', (str(data.email),)).fetchone(); con.close()
    if not row or not verify_password(data.password, row['password_hash']):
        raise HTTPException(401, 'Invalid email or password')
    return {'access_token': create_token(row['id']), 'token_type': 'bearer', 'student_id': row['id'], 'expires_in': 28800}

@router.get('/me')
def me(s=Depends(current_student)):
    return {k: s.get(k) for k in ['id','name','email','college','degree','branch','year','semester','location','cgpa','tenth','twelfth','backlogs','target_role','career_goal','created_at']}
