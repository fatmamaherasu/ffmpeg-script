import os
import ffmpeg
from PIL import Image 


def round_edges(input_file, output_file, image, corner_radius):
    if os.path.exists(output_file):
        os.remove(output_file)

    if os.path.exists(image):
        os.remove(image)

    probe_result = ffmpeg.probe(input_file)
    video_stream = next((stream for stream in probe_result['streams']
                             if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])

    image = Image.new("RGB", (width, height)) 
    image.save("blank.jpg") 

    input_stream = ffmpeg.input(input_file)
    audio = input_stream.audio

    rounded_video = input_stream.filter_("geq", lum='p(X,Y)', a=f'if(gt(abs(W/2-X),W/2-{corner_radius})*gt(abs(H/2-Y),H/2-{corner_radius}),if(lte(hypot({corner_radius}-(W/2-abs(W/2-X)),{corner_radius}-(H/2-abs(H/2-Y))),{corner_radius}),255,0),255)')
    video = ffmpeg.overlay(ffmpeg.input("blank.jpg"), rounded_video)
    video_audio = ffmpeg.concat(video, audio, v=1, a=1)
    output = ffmpeg.output(video_audio, output_file, format="mp4")
    output.run()



def fade_and_merge(first_file, second_file, output_file, fade_out, fade_in):
    if os.path.exists(output_file):
        os.remove(output_file)

    pts = "PTS-STARTPTS"
    probe_first = ffmpeg.probe(first_file)
    first_duration = float(probe_first.get("format", {}).get("duration", None))
    first_stream = ffmpeg.input(first_file)
    first_video = first_stream.filter_("fade", t='out', st=first_duration-fade_out, d=fade_out).setpts(pts)
    first_audio = first_stream.filter_("asetpts", pts)
    second_stream = ffmpeg.input(second_file)
    second_video = second_stream.filter_("fade", t='in', st=0, d=fade_in).setpts(pts)
    second_audio = second_stream.filter_("asetpts", pts)
    video = ffmpeg.concat(first_video, second_video, n=2, v=1, a=0)
    audio = ffmpeg.concat(first_audio, second_audio, n=2, v=0, a=1)
    video_audio = ffmpeg.concat(video, audio, n=2, v=1, a=1)
    output = ffmpeg.output(video_audio, output_file, format="mp4")
    output.run()
    



def modify_audio(input_file, output_file, duration):
    if os.path.exists(output_file):
        os.remove(output_file)
    
    probe_result = ffmpeg.probe(input_file)
    input_duration = probe_result.get("format", {}).get("duration", None)
    input_stream = ffmpeg.input(input_file)
    pts = "PTS-STARTPTS"
    video = input_stream.setpts(pts)
    audio = input_stream.filter_("atrim", start=duration, end=input_duration).filter_("asetpts", pts)
    muted_audio = input_stream.filter_("atrim", start=0, end=duration).filter_("volume", volume=0).filter_("asetpts", pts)
    full_audio = ffmpeg.concat(muted_audio, audio, n=2, v=0, a=1)
    video_audio = ffmpeg.concat(video, full_audio, n=2, v=1, a=1)
    output = ffmpeg.output(video_audio, output_file, format="mp4")
    output.run()



modify_audio("video.mp4", "modified_audio.mp4", 3)
round_edges("modified_audio.mp4", "rounded_video.mp4", "blank.jpg", 4)
fade_and_merge("video.mp4", "rounded_video.mp4", "output.mp4", 3, 3)