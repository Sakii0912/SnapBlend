import base64
from flask import Flask, render_template, request, make_response, send_file , jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, set_access_cookies,
    unset_jwt_cookies, get_jwt
)
from datetime import timedelta, datetime, timezone
import secrets
import hashlib
import cv2
import numpy as np
from io import BytesIO
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips
from sqlalchemy import create_engine, Column, Integer, LargeBinary, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import tempfile
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(64)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=7)
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)

class Image(Base):
    __tablename__ = 'Images'
    S_no = Column(Integer, primary_key=True)
    userid = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size_in_bytes = Column(Integer, nullable=False)
    data = Column(LargeBinary(length=(2**32)-1), nullable=False)

class AudioFile(Base):
    __tablename__ = 'Audios'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    audio_data = Column(LargeBinary(length=(2**32)-1))

engine = create_engine("cockroachdb://Saketh:nMrGR4cAKnEmZxvbc60Yig@crewsk3s-14103.8nj.gcp-europe-west1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

jwt = JWTManager(app)

@app.after_request
def refresh(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        current = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(current + timedelta(hours=72))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response

@app.route('/')
def welcome():
    return render_template('Welcome_Page.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('Signup.html')
    if request.method == 'POST':
        em = request.form["email"]
        u_name = request.form["username"]
        check_pas = request.form["passcheck"]
        pas_org = request.form["password"]
        if check_pas != pas_org:
            err_str = "*Please Retype your password correctly!"
            return render_template("Signup.html", error=err_str)

        session = Session()
        user = session.query(User).filter_by(email=em).first()
        if user:
            session.close()
            return render_template('Signup.html', error="User already exists!")

        hashed_password = hashlib.sha256(pas_org.encode()).hexdigest()
        new_user = User(email=em, username=u_name, password=hashed_password)
        session.add(new_user)
        session.commit()
        session.close()
        return render_template('Signin.html')

@app.route('/sign_in', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('Signin.html')
    else:
        em = request.form["email"]
        pasw = request.form["password"]
        hashed_password = hashlib.sha256(pasw.encode()).hexdigest()
        if em != 'admin@gmail.com':
            session = Session()
            user = session.query(User).filter_by(email=em, password=hashed_password).first()
            if not user:
                session.close()
                return render_template('Signin.html', error="User not found or incorrect password!")
            session.close()
        if em != 'admin@gmail.com':
            additional_data = {'email': user.email, 'username': user.username, 'password': user.password}
            access_token = create_access_token(identity=user.id , additional_claims=additional_data)
            response = make_response(render_template('Welcome_Page.html', uid=user.id))
            set_access_cookies(response, access_token)
        else:
            additional_data = {'email': 'admin@gmail.com' , 'username':'admin'}
            access_token = create_access_token(identity=1, additional_claims=additional_data)
            response = make_response(render_template('Welcome_Page.html', uid=1))
            set_access_cookies(response, access_token)
        return response

@app.route('/up_load', methods=['POST', 'GET'])
@jwt_required()
def upload():
    if request.method == 'GET':
        user_id = get_jwt_identity()
        return render_template('UploadImage.html', uid=user_id)
    
    if request.method == 'POST':
        string = "Files Couldn't be uploaded, please try again!"
        user_id = request.form.get('user_id')
        if 'Images[]' in request.files:
            image_list = request.files.getlist('Images[]')
            session = Session()
            for image in image_list:
                file_data = image.read()
                blob_data = base64.b64encode(file_data)
                name = image.filename
                temp = name.split('.')
                name = temp[0]
                type = temp[1]
                size = len(file_data)
                nparray = np.frombuffer(file_data, np.uint8)
                img_temp = cv2.imdecode(nparray, cv2.IMREAD_UNCHANGED)
                height, width = img_temp.shape[:2]
                new_image = Image(userid=user_id, name=name, type=type, width=width, height=height, size_in_bytes=size, data=blob_data)
                session.add(new_image)
                session.commit()
            session.close()
            string = "Files have been saved successfully!!"
        return render_template('UploadImage.html', success=string, uid=user_id)

@app.route('/create_video', methods=['POST', 'GET'])
@jwt_required()
def create():
    if request.method == 'GET':
        user_id = get_jwt_identity()
        session = Session()
        image_data = session.query(Image).filter_by(userid=user_id).all()
        audio_info = session.query(AudioFile).all()
        session.close()
        base64_audio = [base64.b64encode(audio.audio_data).decode('utf-8') for audio in audio_info]
        audio_name = [audio.name for audio in audio_info]
        image_data_new = [base64.b64decode(image.data) for image in image_data]
        Image_list = [np.frombuffer(image, np.uint8).tolist() for image in image_data_new]
        Type_list = [image.type for image in image_data]
        Name_List = [image.name for image in image_data]
        image_dict = {'Name': Name_List, 'Type': Type_list, 'Data': Image_list}
        audio_dict = {'Name': audio_name, 'Data': base64_audio}
        return render_template('CreateVideoPage.html', images_info=image_dict, uid=user_id , audio_in = audio_dict)
    if request.method == 'POST':
        def add_animation(clip):
            return clip.set_duration(4).fadein(1).fadeout(1)
        image_clips = []
        audio_binary_data = []
        target_size = (400 , 400)
        userid = request.form.get('userid')
        session = Session()
        if 'Audionames[]' in request.form:
            audio_names = request.form.getlist('Audionames[]')
            for audio_name in audio_names:
                audio = session.query(AudioFile).filter_by(name = audio_name).first()
                audio_binary_data.append(audio.audio_data)
        if 'Image_URL[]' in request.form:
         images = request.form.getlist('Image_URL[]')
         for image_name in images:
            print(image_name)
            image_enc = session.query(Image).filter_by(name = image_name).first()
            bin_data = base64.b64decode(image_enc.data)
            img_data = np.frombuffer(bin_data, dtype=np.uint8)
            img_temp = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img_temp, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img , target_size)
            image_clip = ImageClip(img_resized , duration = 4)
            image_clip = add_animation(image_clip)
            image_clips.append(image_clip)
        session.close()
        video_clip = concatenate_videoclips(image_clips , method="compose")
        audio_clips = []
        if(video_clip):
            print("Yes!!")
        temp_audio_files = []
        for data in audio_binary_data:
            temp_audio_file = tempfile.NamedTemporaryFile(suffix=".mp3" , delete=False)
            temp_audio_file.write(data)
            temp_audio_file.close()
            temp_audio_files.append(temp_audio_file.name)
        audio_clips = [AudioFileClip(audio_file) for audio_file in temp_audio_files]
        audio_clip = concatenate_audioclips(audio_clips)
        if(audio_clip.duration > video_clip.duration):
                audio_clip = audio_clip.subclip(0 , video_clip.duration)
                video_clip = video_clip.set_audio(audio_clip)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            video_clip.write_videofile(temp_file.name, codec='libx264', fps=24)
            temp_file.seek(0)  # Reset file pointer to the beginning
            video_data = temp_file.read()
        for files in temp_audio_files:
            os.unlink(files)
        #temp_data = video_data[4:]
        filename = 'videotemp.mp4'
        curr_dir = os.getcwd()
        fullpath = os.path.join(curr_dir , filename)
        with open(fullpath , 'wb') as f:
            f.write(video_data)
        final_video_data = base64.b64encode(video_data).decode('utf-8')
        response_data = {'video_data':final_video_data}
        return jsonify(response_data)
@app.route('/loggedout', methods=['GET'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    response = make_response(render_template('Logged_out.html', uid=user_id))
    unset_jwt_cookies(response)
    return response
@app.route('/admin')
@jwt_required()
def user_display():
    session = Session()
    user_list = session.query(User).all()
    session.close()
    return render_template("AdminPage.html", userlist=user_list)

if __name__ == '__main__':
    app.run(debug=True)
