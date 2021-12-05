import git
import os
import chardet
from flask import *
app=Flask(__name__)
class GItem:
    def __init__(self,item):
        self.istree=isinstance(item,git.Tree)
        self.isblob=isinstance(item,git.Blob)
        self.item=item

def repopath(user,name):
    return os.path.join('repos',user,name)
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
        trees=gf.tree()
        print(list(trees))
        if not additional:
            return render_template('dir.html',tree=(GItem(ttr) for ttr in trees),base=f'/repo/{user}/{name}/{additional}/',filename='/',b=rep)

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
                         return render_template('file.html',content="Binary File!",filename=n.path,b=rep)

                    return render_template('file.html',content=content,filename=n.path,b=rep)
                else:
                    abort(404)
            elif isinstance(n,git.Tree):
                if ixm==len(x)-1:

                    return render_template('dir.html',tree=(GItem(ttr) for ttr in n),base=f'/repo/{user}/{name}/{additional}/',filename=n.path,b=rep)
                else:
                    trees=n
        abort(404)
    elif to_view=='commits':
        return 'Commit support will be added tommorow'
app.run(debug=True)    
