import unittest,tempfile,os,subprocess,socket,time,json,urllib.request,urllib.error,sqlite3,sys
from pathlib import Path
class AccountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.path=cls.tmp.name+'/ledger.sqlite3'
        sock=socket.socket();sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1];sock.close()
        cls.proc=subprocess.Popen([sys.executable,str(Path(__file__).with_name('app.py'))],env={**os.environ,'LEDGER_DB':cls.path,'ADMIN_PASSWORD':'fixture-password-only','PORT':str(cls.port),'COOKIE_SECURE':'0'})
        for _ in range(100):
            try:cls.call('/health');break
            except Exception:time.sleep(.05)
    @classmethod
    def tearDownClass(cls):cls.proc.terminate();cls.proc.wait();cls.tmp.cleanup()
    @classmethod
    def call(cls,path,method='GET',data=None,cookie=None):
        headers={'Content-Type':'application/json'}
        if cookie:headers['Cookie']=cookie
        req=urllib.request.Request(f'http://127.0.0.1:{cls.port}'+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers=headers)
        try:
            with urllib.request.urlopen(req) as r:return r.status,json.load(r),r.headers.get('Set-Cookie','').split(';')[0]
        except urllib.error.HTTPError as e:return e.code,json.load(e),''
    def login(self):return self.call('/login','POST',{'username':'admin','password':'fixture-password-only'})[2]
    def test_protected_ledger_and_login(self):
        self.assertEqual(self.call('/ledger')[0],401)
        self.assertEqual(self.call('/login','POST',{'username':'admin','password':'wrong'})[0],401)
        cookie=self.login();self.assertEqual(self.call('/session',cookie=cookie)[1]['username'],'admin')
        self.call('/logout','POST',{},cookie);self.assertEqual(self.call('/session',cookie=cookie)[0],401)
    def test_save_restore_and_stale_device_conflict(self):
        cookie=self.login();snapshot=self.call('/ledger',cookie=cookie)[1]
        ledger={'version':1,'initialSalary':6000,'birthday':'','referenceAge':80,'periods':[],'profiles':[{'effectiveFrom':0,'expenses':[]}],'events':[],'extras':[{'id':'example','timestamp':1,'amount':20,'note':'test','kind':'income'}]}
        status,data,_=self.call('/ledger','PUT',{'data':ledger,'revision':snapshot['revision']},cookie);self.assertEqual(status,200)
        loaded=self.call('/ledger',cookie=cookie)[1];self.assertEqual(loaded['data']['extras'][0]['amount'],20);self.assertEqual(loaded['data']['extras'][0]['kind'],'income')
        self.assertEqual(self.call('/ledger','PUT',{'data':ledger,'revision':snapshot['revision']},cookie)[0],409)
        with sqlite3.connect(self.path) as db:stored=db.execute('SELECT password_hash FROM users').fetchone()[0];self.assertNotEqual(stored,'fixture-password-only')
if __name__=='__main__':unittest.main()
