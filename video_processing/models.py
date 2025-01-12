from django.db import models

class UploadedVideo(models.Model):
    file = models.FileField(upload_to='uploaded_videos/')
    transcription = models.TextField(blank=True, null=True)
    processing_status = models.CharField(max_length=20, default='pending')
    current_stage = models.CharField(max_length=50, blank=True, null=True)
    progress = models.IntegerField(default=0)
    processed_file = models.FileField(upload_to='processed_videos/', blank=True, null=True)

    def update_progress(self, stage, progress):
        """Update current stage and progress during processing."""
        self.current_stage = stage
        self.progress = progress
        self.save()

    def fail_processing(self, error_message):
        """Set the processing status to 'failed' and log the error."""
        self.processing_status = 'failed'
        self.current_stage = 'Error'
        self.transcription = error_message
        self.progress = 0  # Reset progress to 0
        self.save()

    def complete_processing(self, processed_file_path):
        """Complete the processing and update the status."""
        self.processing_status = 'completed'
        self.current_stage = 'Completed'
        self.processed_file = processed_file_path
        self.progress = 100  # Set progress to 100% once completed
        self.save()
