#!/usr/bin/env python3
"""Time Ledger account API. Python standard library only; bind to loopback."""
import os,json,sqlite3,secrets,hashlib,hmac,time,math
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlsplit
DB=os.environ.get('LEDGER_DB','/var/lib/time-ledger/ledger.sqlite3')
SECURE=os.environ.get('COOKIE_SECURE','1')=='1'
def db():
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;return c

def password_hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
def setup():
    os.makedirs(os.path.dirname(os.path.abspath(DB)),exist_ok=True)
    with db() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ledgers(user_id INTEGER PRIMARY KEY,data TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(ip TEXT PRIMARY KEY,count INTEGER NOT NULL,expires INTEGER NOT NULL);''')
        if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            password=os.environ.get('ADMIN_PASSWORD')
            if not password:raise RuntimeError('Set ADMIN_PASSWORD for first initialization; never commit passwords')
            salt=secrets.token_hex(16)
            c.execute('INSERT INTO users(username,salt,password_hash) VALUES(?,?,?)',('admin',salt,password_hash(password,salt)))
    os.chmod(DB,0o600)
def valid_ledger(data):
    if not isinstance(data,dict) or data.get('version')!=1:raise ValueError('无效账本版本')
    def finite(v):return type(v) in (int,float) and math.isfinite(v)
    if not finite(data.get('initialSalary')) or data['initialSalary']<=0:raise ValueError('无效工资')
    for k in ('periods','profiles','events'):
        if not isinstance(data.get(k),list) or len(data[k])>10000:raise ValueError('无效账本结构')
    if not data['profiles']:raise ValueError('费用配置不可为空')
    prev=None
    for p in sorted(data['periods'],key=lambda p:p.get('startAt',0)):
        if p.get('type') not in ('working','unemployed','paused') or not finite(p.get('startAt')):raise ValueError('无效职业区间')
        end=p.get('endAt')
        if end is not None and (not finite(end) or end<=p['startAt']):raise ValueError('无效结束时间')
        if prev is not None and (prev.get('endAt') is None or prev['endAt']>p['startAt']):raise ValueError('区间重叠')
        for k in ('targetSalary','actualSalary','expenseReferenceIncome'):
            if not finite(p.get(k)) or p[k]<0:raise ValueError('无效工资')
        prev=p
    for p in data['profiles']:
        if not finite(p.get('effectiveFrom')) or not isinstance(p.get('expenses'),list):raise ValueError('无效费用配置')
        for e in p['expenses']:
            for k in ('fixed','ratio','fallbackRatio'):
                if k in e and (not finite(e[k]) or e[k]<0):raise ValueError('无效费用值')
    for e in data.get('extras',[]):
        if not finite(e.get('amount')) or e['amount']<=0 or not finite(e.get('timestamp')):raise ValueError('无效额外支出')
    return json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':'))
class API(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass
    def respond(self,status,data,cookie=None):
        content=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(content)))
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(content)
    def cookie(self,token,age):return f'time_ledger_session={token}; Path=/time-ledger/; HttpOnly; SameSite=Strict; Max-Age={age}'+('; Secure' if SECURE else '')
    def user(self,c):
        cookie=SimpleCookie()
        try:cookie.load(self.headers.get('Cookie',''));token=cookie['time_ledger_session'].value
        except Exception:return None
        return c.execute('SELECT users.id,users.username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n<1 or n>2_000_000:raise ValueError('请求过大或为空')
        return json.loads(self.rfile.read(n),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('无效数值')))
    def do_GET(self):self.handle_api('GET')
    def do_POST(self):self.handle_api('POST')
    def do_PUT(self):self.handle_api('PUT')
    def handle_api(self,method):
        path=urlsplit(self.path).path
        try:
            if SECURE and path not in ('/health',) and self.headers.get('X-Forwarded-Proto')!='https':return self.respond(403,{'error':'请使用 HTTPS 访问'})
            if method!='GET':
                origin=self.headers.get('Origin')
                if origin and urlsplit(origin).netloc!=self.headers.get('Host'):return self.respond(403,{'error':'来源不匹配'})
            with db() as c:
                user=self.user(c)
                if path=='/health' and method=='GET':return self.respond(200,{'ok':True})
                if path=='/login' and method=='POST':
                    body=self.body();ip=self.headers.get('X-Real-IP',self.client_address[0]);attempt=c.execute('SELECT * FROM attempts WHERE ip=?',(ip,)).fetchone()
                    if attempt and attempt['expires']>time.time() and attempt['count']>=5:return self.respond(429,{'error':'登录尝试过多，请一分钟后再试'})
                    u=c.execute('SELECT * FROM users WHERE username=?',(str(body.get('username','')),)).fetchone();password=str(body.get('password',''))
                    if len(password)>1024 or not u or not hmac.compare_digest(u['password_hash'],password_hash(password,u['salt'])):
                        count=attempt['count']+1 if attempt and attempt['expires']>time.time() else 1
                        c.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',(ip,count,int(time.time())+60));return self.respond(401,{'error':'账号或密码不正确'})
                    c.execute('DELETE FROM attempts WHERE ip=?',(ip,));c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
                    token=secrets.token_urlsafe(32);c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['id'],int(time.time())+604800))
                    return self.respond(200,{'username':u['username']},self.cookie(token,604800))
                if not user:return self.respond(401,{'error':'请先登录'})
                if path=='/session' and method=='GET':return self.respond(200,{'username':user['username']})
                if path=='/logout' and method=='POST':
                    cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''));token=cookie['time_ledger_session'].value;c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),));return self.respond(200,{'ok':True},self.cookie('',0))
                if path=='/password' and method=='POST':
                    body=self.body();u=c.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone();new=str(body.get('newPassword',''))
                    if not hmac.compare_digest(u['password_hash'],password_hash(str(body.get('oldPassword','')),u['salt'])):return self.respond(400,{'error':'原密码不正确'})
                    if len(new)<8 or len(new)>1024:return self.respond(400,{'error':'新密码至少 8 位，最多 1024 位'})
                    salt=secrets.token_hex(16);c.execute('UPDATE users SET salt=?,password_hash=? WHERE id=?',(salt,password_hash(new,salt),user['id']));c.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],));return self.respond(200,{'ok':True},self.cookie('',0))
                if path=='/ledger' and method=='GET':
                    row=c.execute('SELECT data,revision FROM ledgers WHERE user_id=?',(user['id'],)).fetchone();return self.respond(200,{'data':json.loads(row['data']) if row else None,'revision':row['revision'] if row else 0})
                if path=='/ledger' and method=='PUT':
                    body=self.body();serialized=valid_ledger(body.get('data'));c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT revision FROM ledgers WHERE user_id=?',(user['id'],)).fetchone();rev=row['revision'] if row else 0
                    if body.get('revision')!=rev:return self.respond(409,{'error':'另一设备已更新账本，请刷新后重试。当前输入未保存。'})
                    c.execute('INSERT INTO ledgers VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data,revision=excluded.revision',(user['id'],serialized,rev+1));return self.respond(200,{'revision':rev+1})
                return self.respond(404,{'error':'接口不存在'})
        except (ValueError,TypeError,KeyError,AttributeError):self.respond(400,{'error':'请求数据不完整或格式错误'})
        except Exception:self.respond(500,{'error':'服务器暂时无法保存，请稍后重试'})
if __name__=='__main__':
    setup();ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('PORT','5187'))),API).serve_forever()
