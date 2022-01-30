#!/usr/bin/env python3
import git
import os
import chardet
import timeago
from flask import *
import datetime
import models
from io import BytesIO
from dulwich.pack import PackStreamReader
import subprocess, os.path
from flask_httpauth import HTTPBasicAuth
import hashlib
import tempfile
auth = HTTPBasicAuth()
TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
app=Flask(__name__)

app.secret_key=b'A\xde57~~~\xea\xdd\xdd\xdd\xea\xea\xaa\xda\xee\xff\xee\xaa[we[]]ddoawei q32hg3wu'

class UnamEr(Exception):pass
class EmEr(Exception):pass
def sha224(t):
    return hashlib.sha224(t.encode()).hexdigest()

def tznow():
    return datetime.datetime.now().replace(tzinfo=TIMEZONE)
class GItem:
    def __init__(self,item):
        self.istree=isinstance(item,git.Tree)
        self.isblob=isinstance(item,git.Blob)
        self.item=item
class GitCommit:
    def __init__(self,commit):
        self.name=commit.summary
        self.id=commit.hexsha
        self.commiter=commit.committer.name
        self.date=commit.committed_datetime.strftime('%d.%M.%Y at %H:%m:%S')
        self.ago=timeago.format(tznow()-commit.committed_datetime)
def repopath(user,name):
    return os.path.join('repos',user,name)
def find_last(gf,pth):
    for i in gf.iter_commits():
        for a in i.diff():
            if pth in a.b_rawpath.decode():
                return GitCommit(i)
def makeUser():
    return models.user_by_uname(session['user'])[0]
@app.route('/profile/')
def profile():
    print(session.get('logged'))
    if not session.get('logged'):return redirect('/login/')
    return '<html><h1>Logged in as'+makeUser().uname+'</h1></html>'
@app.route('/new/',methods=['GET','POST'])
def new():
    if not session.get('logged'):return redirect('/login/')
    if request.method=='POST':
        if os.path.exists('./repos/'+makeUser().uname+'/'+request.form['name']):
            return render_template('new.html',wrong=True)
        bareinitpopen=subprocess.Popen(['git', 'init','--bare','./repos/'+makeUser().uname+'/'+request.form['name']],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        bareinitpopen.wait()
        dbrepo=models.Repo(name=request.form['name'],owner=makeUser().id,visible=False,allowed='')
        models.session.add(dbrepo)
        models.session.commit()
        return redirect('/repo/'+makeUser().uname+'/'+request.form['name'])
    return render_template('new.html',wrong=False)

@app.route('/login/',methods=['GET','POST'])
def login():
    if session.get('logged'):
        return redirect('/profile')
    if request.method=='POST':
        if ver_pw(**request.form):
            session['logged']=True
            
            session['user']=request.form['username']
            return redirect('/profile')
        print('AT login() Invalid PASSWORD')
        return render_template('login.html',invalid=True)
    return render_template('login.html',invalid=False)
@app.route('/repo/<string:user>/<string:name>/')
@app.route('/repo/<string:user>/<string:name>/<path:additional>')
def repo(user,name,additional=''):
    
    if additional.startswith('?'):
        additional=''
    print(additional)
    rp=repopath(user,name)
    if not os.path.exists(rp):
        abort(404)

    gf=git.Repo(rp)
    if not gf.active_branch.is_valid():
        return render_template('dir.html',tree=[],base=f'/repo/{user}/{name}/{additional}/',filename='/',commit=None,b=None)
    rep='/repo/'+user+'/'+name+'/'
    to_view=request.args.get('view','base')
    if to_view=='base':
        if 'commit' in request.args:
            try:
                csd=next(filter(lambda a:a.hexsha==request.args['commit'],gf.iter_commits()))
                trees=csd.tree

            except StopIteration:
                trees=gf.tree()
                csd=gf.commit()
        else:    
            trees=gf.tree()
            csd=gf.commit()
        csd=GitCommit(csd)
        print(list(trees))
        if not additional:
            return render_template('dir.html',tree=(GItem(ttr) for ttr in trees),base=f'/repo/{user}/{name}/{additional}/',filename='/',b=rep,commit=csd)

        x=additional.split('/')
        for ixm,i in enumerate(x):
            
            for t in trees:
                if t.name==i:
                    n=t
                    break
            else:
                abort(404)
            if isinstance(n,git.Blob):
                if ixm==len(x)-1:
                    content=n.data_stream.read()
                    if 'download' in request.args:
                        return Response(content,mimetype=n.mime_type)
                    try:
                        content=content.decode(chardet.detect(content)['encoding'])
                    except:
                         return render_template('file.html',content="Binary File!",filename=n.path,b=rep,commit=find_last(gf,n.path),base=f'/repo/{user}/{name}/{additional}')

                    return render_template('file.html',content=content,filename=n.path,b=rep,commit=find_last(gf,n.path) ,base=f'/repo/{user}/{name}/{additional}')

                else:
                    abort(404)
            elif isinstance(n,git.Tree):
                if ixm==len(x)-1:

                    return render_template('dir.html',tree=(GItem(ttr) for ttr in n),base=f'/repo/{user}/{name}/{additional}/',filename=n.path,b=rep,commit=find_last(gf,n.path))
                else:
                    trees=n
        abort(404)
    elif to_view=='commits':
        comts=[]
        for  i in gf.iter_commits():
            comts.append(GitCommit(i))
            print('Analyzed '+str(i))
        return render_template('commits.html',reponame=f'{user}/{name}',base=f'/repo/{user}/{name}/',commits=comts)
@app.route('/signup/',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        f=request.form
        try:
            new_user(**f)
        except UnamEr:
            return render_template("signup.html",msg="Username already exists.",on="uname")
        except EmEr:
            return render_template("signup.html",msg="Username already exists.",on="email")
        return "Success"
    return render_template("signup.html",msg="",on="")
@auth.verify_password
def ver_pw(username,pw):
    print("VERIFY")
    print(username,pw)
    us=models.user_by_uname(username) 
    if not list(us):
        return False
    return us[0].pw==sha224(pw)
def new_user(uname,pw,fn,ln,email):
    if  tuple(models.user_by_uname(uname)):
        raise UnamEr
    if tuple(models.user_by_email(email)):
        raise EmEr
    models.session.add(models.User(uname=uname,pw=sha224(pw),fname=fn,lname=ln,email=email,admin=False))
    models.session.commit()
    os.mkdir("./repos/"+uname)
@app.route('/<path:project_name>/info/refs')
@auth.login_required
def info_refs(project_name):
    if request.authorization.username != project_name.split('/')[0] and not models.user_by_uname(request.authorization.username)[0].admin:
        abort(401)
    project_name='./repos/'+project_name
    service = request.args.get('service')
    if service[:4] != 'git-': 
        abort(500)
    p = subprocess.Popen([service,  '--stateless-rpc','--advertise-refs', project_name], stdout=subprocess.PIPE)
    packet = '# service=%s\n' % service
    length = len(packet) + 4
    _hex = '0123456789abcdef'
    prefix = ''
    prefix += _hex[length >> 12 & 0xf]
    prefix += _hex[length >> 8  & 0xf]
    prefix += _hex[length >> 4 & 0xf]
    prefix += _hex[length & 0xf]
    data = prefix + packet + '0000'
    data += p.stdout.read().decode()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-%s-advertisement' % service
    p.wait()
    return res

@app.route('/<path:project_name>/git-receive-pack', methods=('POST',))
@auth.login_required
def git_receive_pack(project_name):
    if not list(models.user_by_uname(request.authorization.username)):
        abort (401)
    if request.authorization.username != project_name.split('/')[0] and not models.user_by_uname(request.authorization.username)[0].admin:
        abort(401)

    project_name='./repos/'+project_name
    
    p = subprocess.Popen(['git-receive-pack','--stateless-rpc', project_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data_in = request.data
    print(data_in)
    try:
        pack_file = data_in[data_in.index(b'PACK'):]
    except:
        pack_file=b''
    objects = PackStreamReader(BytesIO(pack_file).read)
    for obj in objects.read_objects():
        if obj.obj_type_num == 1: # Commit
            print(obj)
    data_out=p.communicate(data_in)[0]
    res = make_response(data_out)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-receive-pack-result'
    p.wait()
    return res

@app.route('/<path:project_name>/git-upload-pack', methods=('POST',))
@auth.login_required
def git_upload_pack(project_name):
    if request.authorization.username != project_name.split('/')[0] and not models.user_by_uname(request.authorization.username)[0].admin:
        abort(401)

    project_name='./repos/'+project_name
    p = subprocess.Popen(['git-upload-pack','--stateless-rpc', project_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    data=p.communicate(request.data)[0]
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-upload-pack-result'
    p.wait()
    return res

if __name__=='__main__':        
    app.run(debug=True)    
