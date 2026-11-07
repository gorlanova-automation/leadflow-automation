"""Private Bitrix adapter. Only this project's category; no arbitrary REST proxy."""
import json, re, html, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTAL = 'https://crm.example.com'
CATEGORY = 17
HOOK_RE = re.compile(r'https://crm\.example\.com/rest/1/[A-Za-z0-9]+/')
ID_RE = re.compile(r'[A-Za-z0-9_-]{8,80}')

class Upstream(Exception):
    def __init__(self, kind): self.kind = kind

def call(hook, method, body):
    request = urllib.request.Request(hook + method + '.json',
        data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.load(response)
    except urllib.error.HTTPError as e:
        raise Upstream('access_denied' if e.code in (401,403) else 'upstream_http') from None
    except Exception:
        raise Upstream('upstream_unavailable') from None
    if 'error' in data: raise Upstream('upstream_api_error')
    return data.get('result')

def find(hook, request_id):
    found = call(hook, 'crm.deal.list', {'filter':{'=CATEGORY_ID':CATEGORY,
        '=ORIGINATOR_ID':'AUTO01', '=ORIGIN_ID':request_id},
        'select':['ID','CATEGORY_ID','ORIGIN_ID'], 'order':{'ID':'ASC'}})
    if not isinstance(found,list): raise Upstream('invalid_upstream_response')
    if len(found)>1: raise Upstream('duplicate_requires_review')
    return int(found[0]['ID']) if found else None

def dispatch(path, hook, body):
    if not HOOK_RE.fullmatch(hook): return {'ok':False,'error':'invalid_credential'}
    rid=body.get('request_id','')
    if not isinstance(rid,str) or not ID_RE.fullmatch(rid):
        return {'ok':False,'error':'invalid_request_id'}
    if body.get('category_id') != CATEGORY or body.get('demo') is not True:
        return {'ok':False,'error':'scope_guard'}
    if path not in ('/deal/find','/deal/create'): return {'ok':False,'error':'unknown_action'}
    try:
        existing=find(hook,rid)
        if existing or path=='/deal/find':
            return {'ok':True,'deal_id':existing,'reconciled':bool(existing),'category_id':CATEGORY}
        # Reject arbitrary field names and real contact addresses in the demo.
        email=body.get('email','')
        if not isinstance(email,str) or not email.endswith('@example.com'):
            return {'ok':False,'error':'demo_email_required'}
        fields={'CATEGORY_ID':CATEGORY, 'STAGE_ID':'C17:NEW',
            'TITLE':'[УЧЕБНАЯ] '+str(body.get('name','Тест'))[:80]+' / '+rid,
            'ORIGINATOR_ID':'AUTO01','ORIGIN_ID':rid,'SOURCE_ID':'WEB',
            'ASSIGNED_BY_ID':1,'OPENED':'N',
            'COMMENTS':'<b>Вымышленные данные. Автоматизатор, проект 01.</b><br>'+ '<br>'.join(
                html.escape(k+': '+str(body.get(k,''))) for k in ('name','email','phone','message','source'))}
        # Never retry an ambiguous create. Reconcile by ORIGIN_ID first.
        try:
            deal_id=call(hook,'crm.deal.add',{'fields':fields,'params':{'REGISTER_SONET_EVENT':'N'}})
        except Upstream:
            try:
                deal_id=find(hook,rid)
                if deal_id: return {'ok':True,'deal_id':deal_id,'reconciled':True,'category_id':CATEGORY}
            except Upstream: pass
            return {'ok':False,'error':'ambiguous_create','requires_review':True}
        if not isinstance(deal_id,int): return {'ok':False,'error':'ambiguous_create','requires_review':True}
        return {'ok':True,'deal_id':deal_id,'reconciled':False,'category_id':CATEGORY}
    except Upstream as e: return {'ok':False,'error':e.kind,'requires_review':True}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass # Never log headers, credential URLs or request bodies.
    def do_GET(self):
        self.reply({'ok':True,'service':'auto01-bridge','category_id':CATEGORY} if self.path=='/health' else {'ok':False})
    def reply(self, value, status=200):
        raw=json.dumps(value,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16000: return self.reply({'ok':False,'error':'body_size'},400)
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict): raise ValueError()
            self.reply(dispatch(self.path,self.headers.get('X-Bitrix-Webhook',''),body))
        except (ValueError,TypeError): self.reply({'ok':False,'error':'invalid_json'},400)

if __name__=='__main__': ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()
