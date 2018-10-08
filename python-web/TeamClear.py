#!flask/bin/python

import os
import simplejson
import PIL
from PIL import Image

from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug import secure_filename

from lib._upload_file import *
from lib._function import *

################ Init ################################
folder_init()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TeamClear335'
app.config['UPLOAD_FOLDER'] = '_uploads/'
app.config['THUMBNAIL_FOLDER'] = '_uploads/thumbs/'
bootstrap = Bootstrap(app)


ALLOWED_EXTENSIONS = set(['avi', 'mkv', 'mp4'])
IGNORED_FILES = set(['.gitignore', '.gitkeep', '.DS_Store'])
#######################################################

def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gen_file_name(filename):
  i = 1
  while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
      name, extension = os.path.splitext(filename)
      filename = '%s_%s%s' % (name, str(i), extension)
      i += 1

  return filename


def create_thumbnail(image):
  try:
      base_width = 80
      img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], image))
      w_percent = (base_width / float(img.size[0]))
      h_size = int((float(img.size[1]) * float(w_percent)))
      img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)
      img.save(os.path.join(app.config['THUMBNAIL_FOLDER'], image))

      return True

  except:
      return False

@app.route("/convert", methods=['GET'])
def convert():
  if request.method == 'GET':
    _filename = os.path.splitext(request.args.get("filename"))[0]
    print(video_Process(_filename,'cut'))
    print(video_Process(_filename,'extract'))
    print(vdsr_start())
    print(video_Process(_filename, 'merge'))
  return redirect(url_for('index'))

@app.route("/upload", methods=['GET', 'POST'])
def upload():
  if request.method == 'POST':
    request.form['form-element-name']
    print(request.values)
    files = request.files['file']

    if files:
      filename = secure_filename(files.filename)
      filename = gen_file_name(filename)
      mime_type = files.content_type

      if not allowed_file(files.filename):
          result = uploadfile(name=filename, type=mime_type, size=0, not_allowed_msg="File type not allowed")

      else:
        # save file to disk
        uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        files.save(uploaded_file_path)

        # create thumbnail after saving
        if mime_type.startswith('image'):
            create_thumbnail(filename)

        # get file size after saving
        size = os.path.getsize(uploaded_file_path)

        # return json for js call back
        result = uploadfile(name=filename, type=mime_type, size=size)

      return simplejson.dumps({"files": [result.get_file()]})

  if request.method == 'GET':
    # get all file in ./data directory
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],f)) and f not in IGNORED_FILES ]

    file_display = []

    for f in files:
        size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], f))
        file_saved = uploadfile(name=f, size=size)
        file_display.append(file_saved.get_file())

    return simplejson.dumps({"files": file_display})

  return redirect(url_for('index'))


@app.route("/delete/<string:filename>", methods=['DELETE'])
def delete(filename):
  file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file_thumb_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename)

  if os.path.exists(file_path):
    try:
      os.remove(file_path)

      if os.path.exists(file_thumb_path):
          os.remove(file_thumb_path)

      return simplejson.dumps({filename: 'True'})
    except:
      return simplejson.dumps({filename: 'False'})


# serve static files
@app.route("/thumbnail/<string:filename>", methods=['GET'])
def get_thumbnail(filename):
  return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename=filename)


@app.route("/data/<string:filename>", methods=['GET'])
def get_file(filename):
  return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename=filename)


@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template('index.html')


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)
  app.run(debug=True)
