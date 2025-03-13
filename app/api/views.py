import os
import json

from . import api
from flask import jsonify, request
from flask import request, send_from_directory, current_app as app
from openai import OpenAI
from flask_cors import CORS, cross_origin

from utils.video_to_audio import convert_video_to_audio
from utils.audio_to_segments import audio_to_segments
from utils.segments_to_candidates import segments_to_candidates
from utils.candidates_to_video import segment_candidates
from utils.create_unique_id import create_unique_id;
from utils.firebase import upload_video_to_db

client = OpenAI(
    api_key=('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'),
)



@api.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Define the upload folder path
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../uploads")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
   
    # Ensure the uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@api.route('/video/upload', methods=['POST'])
def upload_video():

    if not 'file' in request.files:
        return jsonify({"message": "No file part in the request", "success": False}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id');
    print("request.files: ",request.files)
    print('userid : ', user_id)
    
    # Define the upload folder path
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../uploads", f"{user_id}")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Ensure the uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if file.filename == '':
        return jsonify({"message": "No selected file", "success": False}), 400
    
    if not file:
        return jsonify({"message": f"File not found", "success": False}), 400

    filename = create_unique_id("mp4");
    
    
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    audiopaths = convert_video_to_audio(user_id, filepath, filename)
    # locations = upload_video_to_db(filepath, audiopaths["absolute_audio_path"])

    local_video_filepath = f"/{user_id}/{filename}"
    print("local_video_path : ", local_video_filepath);
    
    return jsonify({
        "message": "File uploaded successfully!",
        "success": True,
        "details": {
            # "firebase_paths": locations,
            "local_audio_filepath" : audiopaths["local_audio_path"],
            "local_video_filepath" : local_video_filepath
        }
    }), 200

@api.route('/video/segmentation', methods=['POST'])
def video_segmentation():
    filepath = request.form.get('video_filepath')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../uploads")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
   
    
    # print(f"Received filepath: {filepath}") 
    
    if not filepath:
        return jsonify({"message": "No video filepath provided", "success": False}), 400

    transcription = audio_to_segments(client, f"{app.config['UPLOAD_FOLDER']}{filepath}")
    # print('transcription : ',transcription);
    # segments = jsonify(transcription.segments)
    return transcription.model_dump_json()


@api.route('/video/segment_candidates', methods=['POST'])
def video_segment_candidates():    
    segments = request.form.get('segments')
    print('received segments : ', segments);
    transcription = segments_to_candidates(client, segments)
    candidates = jsonify(transcription)

    return candidates

@api.route('/video/export', methods=['POST'])
def video_export():
    filepath = request.form.get('video_filepath')
    candidates = request.form.get('candidates')
    user_id = request.form.get('user_id')
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../uploads")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    print('video_filepath : ', filepath);
    print('candidates : ', candidates);
    
    candidates = json.loads(candidates)
    filename = create_unique_id();
    video_candidates_path = segment_candidates(user_id, candidates, f"{app.config['UPLOAD_FOLDER']}{filepath}", filename)

    return jsonify({
        "message": "File exported successfully",
        "success": True,
        "details": {
            "paths": video_candidates_path
        }
    })