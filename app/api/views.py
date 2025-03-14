import os
import re
import json
import cloudinary
import cloudinary.uploader
import requests
import instaloader
import io

from . import api
from flask import jsonify, request
from flask import request, send_from_directory, current_app as app
from openai import OpenAI
from flask_cors import CORS, cross_origin
from pytube import YouTube
from tiktok_downloader import snaptik

from utils.video_to_audio import convert_video_to_audio
from utils.audio_to_segments import audio_to_segments
from utils.segments_to_candidates import segments_to_candidates
from utils.candidates_to_video import segment_candidates
from utils.create_unique_id import create_unique_id;
from utils.firebase import upload_video_to_db


client = OpenAI(
    api_key=('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'),
)

# Configure Cloudinary
cloudinary.config( 
    cloud_name = "dip1gweqn",
    api_key = "565723559848231", 
    api_secret = "3TQwPf7eyJR6JBTCjF92hcNZtOY"
)

def download_tiktok_video(url):
    try:
        # TikMate API endpoint
        tikmate_url = "https://api.tikmate.app/api/lookup"
        
        # Extract TikTok video ID
        video_id = re.findall(r'video/(\d+)', url)[0]
        
        # Prepare the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        data = {
            'url': url
        }
        
        # Get download link
        response = requests.post(tikmate_url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Failed to get video download link")
            
        # Download video content
        video_content = requests.get(response.json()[url]).content
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            video_content,
            resource_type="video",
            folder="tiktok_downloads"
        )
        
        return {
            "success": True,
            "url": upload_result['secure_url'],
            "public_id": upload_result['public_id']
        }
        
    except Exception as e:
        raise Exception(f"Failed to download TikTok video: {str(e)}")


def download_youtube_video(url):
    try:
        # For TikTok videos, you might need to extract the actual video URL
        # This is a simplified version - you might need to adjust based on TikTok's current structure
        response = requests.get(url)
        video_url = response.url  # or extract from response.text

        # Download video
        yt = YouTube(video_url)
        stream = yt.streams.get_highest_resolution()
        video_data = stream.download()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            video_data,
            resource_type = "video",
            folder = "youtube_downloads"
        )
        
        return {
            "success": True,
            "url": upload_result['secure_url'],
            "public_id": upload_result['public_id']
        }
    except Exception as e:
        raise Exception(f"Failed to process video: {str(e)}")

def download_instagram_video(url):
    try:
        # Create an instance of Instaloader
        L = instaloader.Instaloader()

        # Extract the shortcode from the URL
        shortcode = url.split("/")[-2]

        # Download the post using the shortcode
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Get the video URL
        video_url = post.video_url

        # Download the video content directly into memory
        video_content = requests.get(video_url).content

        # Upload the video to Cloudinary
        upload_result = cloudinary.uploader.upload(
            io.BytesIO(video_content),  # Use BytesIO to upload from memory
            resource_type="video",
            folder="instagram_downloads"
        )

        # Return success message with the Cloudinary URL
        return {
            "success": True,
            "url": upload_result['secure_url'],
            "public_id": upload_result['public_id']
        }

    except Exception as e:
        raise Exception(f"Failed to download Instagram video: {str(e)}")

@api.route('/video/import-tiktok-video', methods=['POST'])
def import_tiktok_video():
    url = request.form.get('url')
    user_id = request.form.get('user_id')
    
    if not url:
        return jsonify({"message": "No url provided", "success": False}), 400
    
    if not user_id:
        return jsonify({"message": "No user id provided", "success": False}), 400
    
    # download the video from tiktok
    video_path = download_tiktok_video(url)

    return jsonify({
        "message": "Video imported successfully",
        "success": True,
        "details": {
            "video_path": video_path
        }
    })

@api.route('/video/import-youtube-video', methods=['POST'])
def import_youtube_video():
    url = request.form.get('url')
    user_id = request.form.get('user_id')
    
    if not url:
        return jsonify({"message": "No url provided", "success": False}), 400
    
    if not user_id:
        return jsonify({"message": "No user id provided", "success": False}), 400
    
    # download the video from youtube
    video_path = download_youtube_video(url)

    return jsonify({
        "message": "Video imported successfully",
        "success": True,
        "details": {
            "video_path": video_path
        }
    })

@api.route('/video/import-instagram-video', methods=['POST'])
def import_instagram_video():
    url = request.form.get('url')
    user_id = request.form.get('user_id')
    
    if not url:
        return jsonify({"message": "No url provided", "success": False}), 400
    
    if not user_id:
        return jsonify({"message": "No user id provided", "success": False}), 400
    
    video_path = download_instagram_video(url)

    return jsonify({
        "message": "Video imported successfully",
        "success": True,
        "details": {
            "video_path": video_path
        }
    })

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