import os
import sys
import json

from flask import Flask, request, session, redirect, jsonify, render_template

import whatimage
#import pyheif
from PIL import Image

#-Global Vars------------------------------------------------------
curPath = os.path.dirname(os.path.abspath(__file__))
uploadPath = os.path.join(curPath, 'uploaded')
convertPath = os.path.join(curPath, 'converted')

#-Build the flask app object---------------------------------------
app = Flask(__name__ )
#app = Flask(__name__, static_url_path='', static_folder='dist' )
app.secret_key = "changeit"
app.debug = True


#------------------------------------------------------------------
@app.before_first_request
def before_first_request():
  if not os.path.isdir(uploadPath):
    os.mkdir(uploadPath)
  if not os.path.isdir(convertPath):
    os.mkdir(convertPath)


#-The APP Request Handler Area-------------------------------------
@app.route('/', methods=['GET'])
def app_home():
  uplFlAry = os.listdir(uploadPath)
  convertFlAry = os.listdir(convertPath)
  return render_template('home.html', title='Main Page', uplFlAry=uplFlAry, convertFlAry=convertFlAry)



#-App Runner------------------------------------------------------
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)

#------------------------------------------------------------------