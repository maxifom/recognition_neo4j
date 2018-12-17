from flask import Flask, render_template, request, send_file, redirect
from werkzeug.utils import secure_filename
from _neo4j import *
from event import event

# from main import event
app = Flask(__name__)




@app.route('/face_upload', methods=['GET', 'POST'])
def face_upload():
    if request.method == 'GET':
        return render_template('file.html')
    if request.method == 'POST':
        f = request.files['file']
        f_name = './files/' + r.randomString(10) + secure_filename(f.filename)
        f.save(f_name)
        return f_name


@app.route('/images', methods=['GET'])
def images():
    image_list = os.listdir("./images")
    return render_template('images.html', images=image_list)


@app.route('/getImage/<image>', methods=['GET'])
def getImage(image=None):
    return send_file('./images/' + image, mimetype='image/jpeg')


@app.route('/changeName', methods=['POST'])
def changeName():
    new_name = request.form['new_name']
    old_name = request.form['old_name']
    resp = AddKnownFaceToGraph(old_name, new_name, deleteImages=1)
    if resp == 'Success':
        # event.set()
        return redirect('/images', 302)
    return resp


@app.route('/delete', methods=['POST'])
def delete():
    name = request.form['name']
    resp = DeleteFromGraph(name)
    if resp == 'Success':
        # event.set()
        return redirect('/people', 302)
    return resp


@app.route('/people', methods=['GET'])
def people():
    people = GetPeople()
    return render_template('people.html', people=people)


@app.route('/show/<name>', methods=['GET'])
def show(name):
    person = GetPersonByName(name)
    rel = GetRelathionships(person)
    rel.sort(key=weight, reverse=True)
    return render_template('show.html', person=person, rel=rel)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search.html')
    if request.method == 'POST':
        name = request.form['name']
        results = FindNodesByName(name)
        if len(results) == 1:
            return redirect('/show/' + results[0]['name'])
        return render_template('search_results.html', results=results)


@app.route('/searchPhoto', methods=['GET', 'POST'])
def searchPhoto():
    if request.method == 'GET':
        return render_template('search_photo.html')
    if request.method == 'POST':
        file = request.files['photo']
        filename = './files/' + r.randomString(10) + secure_filename(file.filename)
        file.save(filename)
        people = FindNodesByPhoto(filename)
        return render_template('search_results.html', results=people)


@app.route('/export', methods=['GET', 'POST'])
def export():
    if request.method == 'GET':
        return render_template('export.html')
    if request.method == 'POST':
        filename = ExportToFile()
        return render_template('export_result.html', file=filename)


@app.route('/exports', methods=['GET'])
def exports():
    files = os.listdir('./export')
    return render_template('exports.html', exports=files)


@app.route('/getExport/<file>', methods=['GET'])
def getExport(file):
    return send_file('./export/' + str(file))


@app.route('/updateFaces', methods=['GET'])
def updateFaces():
    event.set()
    return 'Success'

@app.route('/addFace', methods=['GET','POST'])
def addFace():
    if request.method == 'GET':
        return render_template('add_face.html')
    if request.method == 'POST':
        face = request.files['face']
        name = request.form['name']
        filename = './files/' + r.randomString(10) + secure_filename(face.filename)
        face.save(filename)
        AddNamedFace(filename, name)
        event.set()
        return redirect('/people')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def weight(el):
    return el['weight']


def StartFlask():
    app.run(host='127.0.0.1', port=5666)


if __name__ == '__main__':
    StartFlask()
