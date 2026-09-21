from fastapi import Header, HTTPException
from app.database import connect
from app.security import decode_token


def current_student(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401, 'Authentication required')
    payload = decode_token(authorization.split(' ', 1)[1])
    if not payload:
        raise HTTPException(401, 'Invalid or expired session')
    try:
        sid = int(payload['sub'])
    except Exception:
        raise HTTPException(401, 'Invalid session')
    con = connect(); row = con.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone(); con.close()
    if not row: raise HTTPException(404, 'Student account not found')
    return dict(row)


def owned(student_id: int, me: dict):
    if student_id != me['id']:
        raise HTTPException(403, 'You can only access your own student data')
