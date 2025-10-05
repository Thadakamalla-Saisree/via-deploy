from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    AudioFileClip
)

def trim_video(path, start, end):
    clip = VideoFileClip(path).subclip(start, end)
    output = "static/previews/trimmed.mp4"
    clip.write_videofile(output)
    return output

def split_video(path, time):
    clip = VideoFileClip(path)
    part1 = clip.subclip(0, time)
    part2 = clip.subclip(time)
    out1 = "static/previews/split_part1.mp4"
    out2 = "static/previews/split_part2.mp4"
    part1.write_videofile(out1)
    part2.write_videofile(out2)
    return [out1, out2]

def add_captions(path, text):
    clip = VideoFileClip(path)
    txt = TextClip(text, fontsize=40, color='white').set_duration(clip.duration).set_position('bottom')
    final = CompositeVideoClip([clip, txt])
    output = "static/previews/captioned.mp4"
    final.write_videofile(output)
    return output

def mute_audio(path):
    clip = VideoFileClip(path).without_audio()
    output = "static/previews/muted.mp4"
    clip.write_videofile(output)
    return output

def add_background_music(video_path, music_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(music_path).set_duration(video.duration)
    final = video.set_audio(audio)
    output = "static/previews/music_added.mp4"
    final.write_videofile(output)
    return output