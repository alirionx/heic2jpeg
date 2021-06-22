import os
import sys
import json

from flask import Flask, request, session, redirect, jsonify, render_template, send_from_directory

import whatimage
import pyheif
from PIL import Image
#import io

import zipfile
import tarfile

#-Global Vars------------------------------------------------------
curPath = os.path.dirname(os.path.abspath(__file__))
uploadPath = os.path.join(curPath, 'uploaded')
convertPath = os.path.join(curPath, 'converted')
dlPath = os.path.join(curPath, 'downloads')

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

#-------------
def create_zip(flDict:dict):
  tgtFlName = "tmp_image_arch.zip"
  tgtPath = os.path.join(dlPath, tgtFlName)
  zipObj = zipfile.ZipFile(tgtPath, "w")
  for flName, flPath in flDict.items():
    zipObj.write(flPath, arcname=flName)
  zipObj.close()
  return tgtFlName

#-------------
def create_targz(flDict:dict):
  tgtFlName = "tmp_image_arch.tar.gz"
  tgtPath = os.path.join(dlPath, tgtFlName)
  tarObj = tarfile.open(tgtPath, "w:gz")
  for flName, flPath in flDict.items():
    tarObj.add(flPath, arcname=flName)
  tarObj.close()
  return tgtFlName


#------------------------------------------------------------------
@app.before_first_request
def before_first_request():
  fldList = [uploadPath, convertPath, dlPath]
  for fld in fldList: 
    if not os.path.isdir(fld):
      os.mkdir(fld)
  
  for f in os.listdir(dlPath):
    os.remove(os.path.join(dlPath, f))
  

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
  if "images" not in postIn:
    resObj["msg"] = "please post image names in json fomat"
    resObj["status"] = 400
    return jsonify(resObj), 400

  imagesIn = postIn["images"]
  try:
    compressionIn = int(postIn["compression"])
  except:
    compressionIn = 90


  for flName in imagesIn:
    srcPath = os.path.join(uploadPath, flName)
    if '.' in flName:
      flNameSplt = flName.split('.')
      flName = '.'.join(flNameSplt[:-1])
    
    tgtFlName = flName + '.jpg'
    tgtPath = os.path.join(convertPath, tgtFlName)

    try:
      convert_heic_to_jpg(srcPath=srcPath, tgtPath=tgtPath, quality=compressionIn)
      os.remove(srcPath)
      resObj["jpegs"].append(flName)
    except Exception as e:
      print(e)

  #------------------
  return jsonify(resObj), 200


#------------------------------------------------
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
      
      #-chk if is heic-----
      flData = open(tgtPath, 'rb').read()
      fmt = whatimage.identify_image(flData)
      if str(fmt).lower() != 'heic':
        os.remove(tgtPath)
        continue
      else:
        resObj['heics'].append(flObj.filename)
      #-------------------

    except Exception as e:
      print(e)
    
  #return jsonify(resObj), 200
  return redirect("/", code=302)

#--------------------------------------------
@app.route('/api/download', methods=['POST'])
def api_download_post():

  postIn = request.json
  if "images" not in postIn:
    return "rong", 400

  imagesIn = postIn["images"]
  try:
    downloadFormat = postIn["format"]
  except:
    downloadFormat = 'zip'

  funcMap = {
    "zip": create_zip,
    "tar.gz": create_targz
  }

  flDict = {}
  for flName in imagesIn:
    srcPath = os.path.join(convertPath, flName)
    flDict[flName] = srcPath

  flName = funcMap[downloadFormat](flDict)
  
  #----------------
  return send_from_directory(directory=dlPath, filename=flName, path=os.path.join(dlPath,flName), as_attachment=True)
  #return 'Palim', 200

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
  
  #----------------
  return jsonify(resObj), 200






#-App Runner------------------------------------------------------
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)

#-----------------------------------------------------------------