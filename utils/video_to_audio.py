import os
from flask import request, send_from_directory, current_app as app
from moviepy.editor import VideoFileClip

def convert_video_to_audio(user_id,video_file, audio_file_name, output_ext="mp3"):
    print('convert func userId : ',user_id)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../uploads",f"{user_id}")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Ensure the uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    out = f"{app.config['UPLOAD_FOLDER']}/{audio_file_name}.{output_ext}"
    
    local_audio_path = f"/{user_id}/{audio_file_name}.{output_ext}"
    
    clip = VideoFileClip(video_file)
    clip = clip.set_end(150)
    clip.audio.write_audiofile(out)

    return {
        "local_audio_path": local_audio_path,
        "absolute_audio_path": out
    }