#!/usr/bin/env python3
import git
import os
import chardet
import timeago
from flask import *
import datetime
TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
app=Flask(__name__)
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
                    try:
                        content=content.decode(chardet.detect(content)['encoding'])
                    except:
                         return render_template('file.html',content="Binary File!",filename=n.path,b=rep,commit=find_last(gf,n.path))

                    return render_template('file.html',content=content,filename=n.path,b=rep,commit=find_last(gf,n.path))
                else:
                    abort(404)
            elif isinstance(n,git.Tree):
                if ixm==len(x)-1:

                    return render_template('dir.html',tree=(GItem(ttr) for ttr in n),base=f'/repo/{user}/{name}/{additional}/',filename=n.path,b=rep,commit=find_last(gf,n.path))
                else:
                    trees=n
        abort(404)
    elif to_view=='commits':
        comts=(GitCommit(i)for i in gf.iter_commits())
        return render_template('commits.html',reponame=f'{user}/{name}',base=f'/repo/{user}/{name}/',commits=comts)
        
app.run(debug=True)    
