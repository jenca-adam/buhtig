import git
import os
from flask import *
app=Flask(__name__)
def repopath(user,name):
    return os.path.join('repos',user,name)
@app.route('/repo/<string:user>/<string:name>/')
@app.route('/repo/<string:user>/<string:name>/<path:additional>')
def repo(user,name,additional=''):
    print(additional)
    rep=repopath(user,name)
    if not os.path.exists(rep):
        abort(404)

    gf=git.Repo(rep)
    rp=os.path.join(rep,additional)
    if not os.path.exists(rp):
        abort(404)

    if os.path.isdir(rp):
        return render_template('dir.html',r=os.listdir(rp),base='/repo/{}/{}/{}/'.format(user,name,additional),filename=os.path.split(rp)[-1])
    return render_template('file.html',content=open(rp,'r').read(),filename=additional)
app.run(debug=True)    
