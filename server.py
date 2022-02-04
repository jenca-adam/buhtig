#!/usr/bin/env python3
import git
import os
import chardet
import timeago
from flask import Flask,session,render_template,request,redirect,abort,Response,make_response
import datetime
import models
from io import BytesIO
from dulwich.pack import PackStreamReader
import subprocess, os.path
from flask_httpauth import HTTPBasicAuth
import hashlib
import shutil

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

getUser=makeUser

@app.route('/logout/')
def logout():
    session['logged']=False
    del session['user']
    return redirect('/login/')

#TODO:Allow admins to read other users' profiles
@app.route('/profile/<string:user>')
def aprof(user):
    if session.get('user')==user:
        return redirect('/profile/')

    if not isAdmin():
        abort(403)
    dbust=list(models.user_by_uname(user))
    if not dbust:
        abort(404)
    dbust=dbust[0]
    
    return templatize('admin-profile.html',user=dbust,repos=models.repos_by_uname(user))

@app.route('/profile/')
def profile():
    print(session.get('logged'))
    if not session.get('logged'):return redirect('/login/')
    return templatize('profile.html',user=makeUser(),repos=models.repos_by_uname(session['user']))

@app.route('/new/',methods=['GET','POST'])
def new():
    if not session.get('logged'):return redirect('/login/')
    if request.method=='POST':
        if os.path.exists('./repos/'+makeUser().uname+'/'+request.form['name']):
            return templatize('new.html',wrong=True)
        bareinitpopen=subprocess.Popen(['git', 'init','--bare','./repos/'+makeUser().uname+'/'+request.form['name']],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        bareinitpopen.wait()
        dbrepo=models.Repo(name=request.form['name'],owner=makeUser().id,visible=False,allowed='')
        models.session.add(dbrepo)
        models.session.commit()
        return redirect('/'+makeUser().uname+'/'+request.form['name'])
    return templatize('new.html',wrong=False)

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
        return templatize('login.html',invalid=True)
    return templatize('login.html',invalid=False)

def isAdmin():
    try:
        u=makeUser()
    except:
        return False
    return u.admin
def templatize(fn,**kwargs):
    return render_template(fn,session=session,**kwargs)

@app.route('/delete/<path:repo>',methods=['GET','POST'])
def delete(repo):
    try:
        x=makeUser()
    except:
        abort(403)
    if repo.endswith('/'):
        repo=repo[:-1]
    dbrepo=models.repo_by_strid(repo)
    if not list(dbrepo):
        abort(404)
    dbrepo=dbrepo[0]

    if not x.admin and x.id!=dbrepo.owner:
        abort(403)
    if request.method=='POST':
        models.session.delete(dbrepo)
        models.session.commit()
        shutil.rmtree('repos/'+repo)
        return redirect('/profile/')
    return render_template('delete.html',repo=repo)

@app.route('/<string:user>/<string:name>/')
@app.route('/<string:user>/<string:name>/<path:additional>')
def repo(user,name,additional=''):
    try:
        dbrepo=models.repo_by_strid('/'.join([user,name]))[0]

    except:
        abort(404)
    if not dbrepo:
        abort(404)
    try:
        getUser()
    except:
        abort(403)
    if getUser().id!=dbrepo.owner and not getUser().admin:
        abort(403)
    if additional.startswith('?'):
        additional=''
    print(additional)
    rp=repopath(user,name)
    if not os.path.exists(rp):
        abort(404)

    gf=git.Repo(rp)
    if not gf.active_branch.is_valid():
        return templatize('dir.html',tree=[],base='/'+'/'.join([user,name,additional]),b='/'+'/'.join([user,name,additional]),filename='/',commit=None)
    rep='/'+user+'/'+name+'/'
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
            return templatize('dir.html',tree=(GItem(ttr) for ttr in trees),base=f'/{user}/{name}/{additional}/',filename='/',b=rep,commit=csd)

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
                         return templatize('file.html',content="Binary File!",filename=n.path,b=rep,commit=find_last(gf,n.path),base=f'/{user}/{name}/{additional}')

                    return templatize('file.html',content=content,filename=n.path,b=rep,commit=find_last(gf,n.path) ,base=f'/{user}/{name}/{additional}')

                else:
                    abort(404)
            elif isinstance(n,git.Tree):
                if ixm==len(x)-1:

                    return templatize('dir.html',tree=(GItem(ttr) for ttr in n),base=f'/{user}/{name}/{additional}/',filename=n.path,b=rep,commit=find_last(gf,n.path))
                else:
                    trees=n
        abort(404)
    elif to_view=='commits':
        comts=[]
        for  i in gf.iter_commits():
            comts.append(GitCommit(i))
            print('Analyzed '+str(i))
        return templatize('commits.html',reponame=f'{user}/{name}',base=f'/{user}/{name}/',commits=comts)

@app.route('/signup/',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        f=request.form
        try:
            new_user(**f,fromform=True)
        except UnamEr:
            return templatize("signup.html",msg="Username already exists.",on="uname")
        except EmEr:
            return templatize("signup.html",msg="Username already exists.",on="email")
        except:
            return templatize("signup.html")
        return "Success"
    return templatize("signup.html",msg="",on="")

@auth.verify_password
def ver_pw(username,pw):
    print("VERIFY")
    print(username,pw)
    us=models.user_by_uname(username) 
    if not list(us):
        return False
    return us[0].pw==sha224(pw)

def new_user(uname,pw,fn,ln,email,admin=False,fromform=False):
    if admin.lower() in ['true','1']:
        admin=True
    else:
        admin=False
    if admin and fromform:
        raise Exception
    if  tuple(models.user_by_uname(uname)):
        raise UnamEr
    if tuple(models.user_by_email(email)):
        raise EmEr

    models.session.add(models.User(uname=uname,pw=sha224(pw),fname=fn,lname=ln,email=email,admin=admin))
    models.session.commit()
    os.mkdir("./repos/"+uname)

@app.route('/api/addUser/',methods=['POST'])
@auth.login_required
def APIAddUser():
    if not models.user_by_uname(request.authorization.username)[0].admin:
        abort(403)
    try:
        new_user(**request.form,fromform=False)
    except UnamEr:
        return Response('{status:"error",message:"User with username given already exists"}',status=409,mimetype="application/json")
    except EmEr:
        return Response('{status:"error",message:"User with e-mail given already exists"}',status=409,mimetype="application/json")
    except Exception as e:
        return Response(f'{{status:"error",message:"{str(e)}"}}', status=422 ,mimetype="application/json")
    return Response('{status:"success",message:"User successfully created"}',mimetype="application/json")

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
    app.run(debug=True,port=5000)    
