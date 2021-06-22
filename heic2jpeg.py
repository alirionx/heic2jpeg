import os
import sys
import json

from flask import Flask, request, session, redirect, jsonify, render_template

import whatimage
import pyheif
from PIL import Image
#import io

#-Global Vars------------------------------------------------------
curPath = os.path.dirname(os.path.abspath(__file__))
uploadPath = os.path.join(curPath, 'uploaded')
convertPath = os.path.join(curPath, 'converted')

#-Build the flask app object---------------------------------------
app = Flask(__name__ )
#app = Flask(__name__, static_url_path='', static_folder='dist' )
app.secret_key = "changeit"
app.debug = True


#-Global Functions-------------------------------------------------
def convert_heic_to_jpg(srcPath, tgtPath, quality=90 ):

  imgObj = pyheif.read_heif(srcPath)
   
  jpgObj = Image.frombytes(mode=imgObj.mode, size=imgObj.size, data=imgObj.data)
  jpgObj.save(tgtPath, quality=quality, optimize=True, progressive=True, format="jpeg")

  return True

#------------------------------------------------------------------
@app.before_first_request
def before_first_request():
  if not os.path.isdir(uploadPath):
    os.mkdir(uploadPath)
  if not os.path.isdir(convertPath):
    os.mkdir(convertPath)


#-The HTML Render Area---------------------------------------------
@app.route('/', methods=['GET'])
def app_home():
  
  uplFlList = os.listdir(uploadPath)
  uplFlAry = []
  for flName in uplFlList:
    flPath = os.path.join(uploadPath, flName) 
    try:
      flData = open(flPath, 'rb').read()
      fmt = whatimage.identify_image(flData)
      if fmt == 'heic':
        uplFlAry.append(flName)
    except Exception as e:
      print(e)
      continue

  convertFlList = os.listdir(convertPath)
  convertFlAry = []
  for flName in convertFlList:
    flPath = os.path.join(convertPath, flName) 
    try:
      flData = open(flPath, 'rb').read()
      fmt = whatimage.identify_image(flData)
      if fmt == 'jpeg':
        convertFlAry.append(flName)
    except Exception as e:
      print(e)
      continue

  #---------------
  return render_template('home.html', title='Main Page', uplFlAry=uplFlAry, convertFlAry=convertFlAry)

#-------------------------------
@app.route('/upload', methods=['GET'])
def app_upload():
  return render_template('upload.html', title='File Upload Page')

#-------------------------------

#-The API Handler Area--------------------------------------------
@app.route('/api/convert', methods=['POST'])
def api_convert_post():
  
  resObj = {
    "path": request.path,
    "method": request.method,
    "status": 200,
    "msg": "",
    "jpegs": []
  }

  postIn = request.json

  for flName in postIn:
    srcPath = os.path.join(uploadPath, flName)
    if '.' in flName:
      flNameSplt = flName.split('.')
      flName = '.'.join(flNameSplt[:-1])
    
    tgtFlName = flName + '.jpg'
    tgtPath = os.path.join(convertPath, tgtFlName)

    try:
      convert_heic_to_jpg(srcPath=srcPath, tgtPath=tgtPath)
      os.remove(srcPath)
      resObj["jpegs"].append(flName)
    except Exception as e:
      print(e)
  
  return jsonify(resObj), 200

#-----------------------------------
@app.route('/api/upload', methods=['POST'])
def api_upload_post():

  resObj = {
    "path": request.path,
    "method": request.method,
    "status": 200,
    "msg": "",
    "heics": []
  }

  flObjAry = request.files.getlist('files')
  for flObj in flObjAry:
    print(flObj.filename)
    try:
      tgtPath = os.path.join(uploadPath, flObj.filename)
      flObj.save(tgtPath)
      resObj['heics'].append(flObj.filename)
    except Exception as e:
      print(e)
    
  #return jsonify(resObj), 200
  return redirect("/", code=302)

#-----------------------------------
@app.route('/api/<typ>', methods=['DELETE'])
def api_images_delete(typ):
  
  resObj = {
    "path": request.path,
    "method": request.method,
    "status": 200,
    "msg": "",
    "dels": []
  }

  typMap = {
    "converted": convertPath,
    "uploaded": uploadPath
  }
  tgtDir = typMap[typ]
  delIn = request.json
  for flName in delIn:
    delPath = os.path.join(tgtDir, flName)
    try:
      os.remove(delPath)
      resObj["dels"].append(flName)
    except Exception as e:
      print(e)
  
  return jsonify(resObj), 200






#-App Runner------------------------------------------------------
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)

#-----------------------------------------------------------------