from faster_whisper import WhisperModel
import os
import subprocess
import threading
import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import UploadedVideo
from .serializers import UploadedVideoSerializer

# Configure logging
logger = logging.getLogger(__name__)

# Load Whisper model globally
whisper_model = WhisperModel("base")  # Use "small", "medium", or "large" if needed


def enhance_audio(input_audio_path, output_audio_path):
    """
    Optional audio enhancement function, e.g., noise reduction or volume normalization.
    """
    try:
        command = [
            "ffmpeg", "-y",
            "-i", input_audio_path,
            "-af", "afftdn",  # FFT noise reduction filter
            output_audio_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        logger.info("Audio enhanced successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Audio enhancement failed: {e}")
        raise RuntimeError("Audio enhancement failed.") from e


def extract_audio(video_path, output_audio_path):
    """
    Extracts audio from the video using FFmpeg.
    """
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-q:a", "0", "-ar", "16000", "-ac", "1", output_audio_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        logger.info("Audio extracted successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio: {e}")
        raise RuntimeError("Audio extraction failed.") from e


def detect_speech_with_faster_whisper(audio_path):
    """
    Detects speech segments using faster-whisper.
    """
    try:
        segments, _ = whisper_model.transcribe(audio_path, beam_size=2, word_timestamps=True)
        return [
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text
            }
            for segment in segments
        ]
    except Exception as e:
        logger.error(f"Speech detection failed: {e}")
        raise RuntimeError("Speech detection failed.") from e


def generate_ffmpeg_trim_commands(input_path, trim_intervals, output_path):
    """
    Generate FFmpeg commands to trim a video based on speech segments.
    """
    try:
        filter_complex = ""
        for idx, segment in enumerate(trim_intervals):
            start, end = segment["start"], segment["end"]
            filter_complex += (
                f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}];"
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}];"
            )

        concat_parts = "".join(f"[v{i}][a{i}]" for i in range(len(trim_intervals)))
        filter_complex += f"{concat_parts}concat=n={len(trim_intervals)}:v=1:a=1[outv][outa]"

        command = [
            "ffmpeg", "-y", "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]", output_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        logger.info("Video trimming completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Video trimming failed: {e}")
        raise RuntimeError("Video trimming failed.") from e


def filter_segments(segments):
    """
    Filters out unwanted segments based on filler words, mumbling, or pauses.
    """
    filler_words = {"um", "uh", "eh", "so", "like", "you know"}
    filtered_segments = []

    for segment in segments:
        text = segment["text"]
        if not text.strip():
            continue  # Skip empty text

        words = text.split()
        if all(word.lower() in filler_words for word in words):
            continue  # Skip if all words are fillers

        filtered_segments.append(segment)
    return filtered_segments


def process_video(video_path, output_path, video_instance):
    """
    Processes the video by enhancing audio, detecting speech, and trimming video.
    """
    temp_audio_path = "temp_audio.wav"
    enhanced_audio_path = "enhanced_audio.wav"

    try:
        # Extract audio
        video_instance.current_stage = "Extracting audio"
        video_instance.progress = 10
        video_instance.save()
        extract_audio(video_path, temp_audio_path)

        # Enhance audio
        video_instance.current_stage = "Enhancing audio"
        video_instance.progress = 25
        video_instance.save()
        enhance_audio(temp_audio_path, enhanced_audio_path)

        # Detect speech
        video_instance.current_stage = "Detecting speech"
        video_instance.progress = 50
        video_instance.save()
        transcription = detect_speech_with_faster_whisper(enhanced_audio_path)

        # Filter segments
        video_instance.current_stage = "Filtering segments"
        video_instance.progress = 75
        video_instance.save()
        filtered_segments = filter_segments(transcription)

        if not filtered_segments:
            raise ValueError("No valid segments found after filtering.")

        # Trim video
        video_instance.current_stage = "Trimming video"
        video_instance.progress = 90
        video_instance.save()
        generate_ffmpeg_trim_commands(video_path, filtered_segments, output_path)

        # Finalize
        video_instance.processed_file.name = output_path
        video_instance.processing_status = "completed"
        video_instance.current_stage = "Completed"
        video_instance.progress = 100
        video_instance.save()
        logger.info("Video processing completed.")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        video_instance.processing_status = "failed"
        video_instance.current_stage = str(e)
        video_instance.save()
    finally:
        # Clean up temp files
        for temp_path in [temp_audio_path, enhanced_audio_path]:
            if os.path.exists(temp_path):
                os.remove(temp_path)



class VideoUploadView(APIView):
    """
    Handles video uploads and initiates processing.
    """
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        serializer = UploadedVideoSerializer(data=request.data)
        if serializer.is_valid():
            video_instance = serializer.save()

            input_path = video_instance.file.path
            output_dir = os.path.join("media", "processed_videos")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"processed_{video_instance.id}.mp4")

            # Update processing status
            video_instance.processing_status = "in_progress"
            video_instance.save()

            def background_processing():
                try:
                    process_video(input_path, output_path, video_instance)
                except Exception as e:
                    logger.error(f"Processing failed: {e}")
                    video_instance.processing_status = "failed"
                    video_instance.save()

            # Start background processing
            threading.Thread(target=background_processing).start()

            return Response({'message': 'Video uploaded and processing started.', 'id': video_instance.id})

        return Response(serializer.errors, status=400)


def video_status(request, video_id):
    """
    Check video processing status.
    """
    try:
        video = UploadedVideo.objects.get(id=video_id)

        # Check if the processed_file exists
        video_url = video.processed_file.url if video.processed_file else None

        return JsonResponse({
            "status": video.processing_status,
            "current_stage": video.current_stage,
            "progress": video.progress,  # Include progress
            "video_url": video_url if video.processing_status == "completed" else None,
        })
    except UploadedVideo.DoesNotExist:
        return JsonResponse({"error": "Video not found."}, status=404)
    except Exception as e:
        # Log and return the error
        return JsonResponse({"error": str(e)}, status=500)
