import React, { useState, useRef } from "react";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";

const App = () => {
  const [video, setVideo] = useState(null);
  const [processedVideo, setProcessedVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState("");
  const [cancelTokenSource, setCancelTokenSource] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const videoRef = useRef(null);

  const handleFileChange = (file) => {
    setVideo(file);
    toast.success("Video selected!");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) {
      handleFileChange(file);
    } else {
      toast.error("Please drop a valid video file!");
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleUpload = async () => {
    if (!video) {
      toast.error("Please upload a video!");
      return;
    }

    const formData = new FormData();
    formData.append("file", video);

    const source = axios.CancelToken.source();
    setCancelTokenSource(source);

    setLoading(true);
    setProgress(0);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/videos/upload/",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          cancelToken: source.token,
        }
      );

      toast.success("Video uploaded successfully! Processing started.");
      const videoId = response.data.id;

      // Start polling for processing status
      pollProcessingStatus(videoId, source);
    } catch (error) {
      if (axios.isCancel(error)) {
        toast.info("Upload canceled.");
      } else {
        toast.error("Error uploading video!");
        console.error(error.response?.data || error.message);
      }
      setLoading(false);
    }
  };

  const pollProcessingStatus = async (videoId, source) => {
    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/api/videos/status/${videoId}/`,
        { cancelToken: source.token }
      );

      const { progress: backendProgress, video_url, status, current_stage } =
        response.data;

      setCurrentStage(current_stage);
      setProgress(backendProgress);

      if (status === "completed") {
        toast.success("Processing completed!");
        setProcessedVideo(video_url);
        setLoading(false);
      } else if (status === "failed") {
        toast.error("Processing failed!");
        setLoading(false);
      } else {
        // Continue polling every 3 seconds
        setTimeout(() => pollProcessingStatus(videoId, source), 3000);
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        toast.info("Processing canceled.");
      } else {
        toast.error("Error fetching processing status.");
        console.error(error.message);
      }
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (cancelTokenSource) {
      cancelTokenSource.cancel("Operation canceled by the user.");
    }
    setLoading(false);
    setProgress(0);
    setCurrentStage("");
    setProcessedVideo(null);
    toast.info("Operation canceled.");
  };

  const handleDownload = () => {
    if (processedVideo) {
      const downloadUrl = `http://127.0.0.1:8000${processedVideo.replace(
        "/media",
        ""
      )}`;
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = "processed_video.mp4";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="app-container">
      <h1>Video Processing App</h1>

      <div
        className={`dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <p>{video ? "Video ready for upload!" : "Drag and drop your video here"}</p>
        <p>or</p>
        <input
          type="file"
          onChange={(e) => handleFileChange(e.target.files[0])}
          accept="video/*"
        />
      </div>

      <div className="upload-section">
        <button onClick={handleUpload} disabled={loading || !video}>
          {loading ? "Processing..." : "Upload and Process"}
        </button>
        {loading && (
          <button onClick={handleCancel} className="cancel-btn">
            Cancel
          </button>
        )}
      </div>

      {loading && (
        <div className="progress-bar">
          <p>Progress: {Math.round(progress)}%</p>
          <div style={{ width: "100%", background: "#ddd", height: "20px" }}>
            <div
              style={{
                width: `${progress}%`,
                background: "green",
                height: "100%",
              }}
            ></div>
          </div>
          <p>Processing Stage: {currentStage}</p>
        </div>
      )}

      <div className="video-container">
        {processedVideo && (
          <div className="video-section">
            <h2>Processed Video</h2>
            <video
              src={`http://127.0.0.1:8000${processedVideo.replace(
                "/media",
                ""
              )}`}
              controls
              style={{ width: "100%", maxWidth: "600px" }}
            />
            <button onClick={handleDownload} className="download-btn">
              Download Processed Video
            </button>
          </div>
        )}
        {video && (
          <div className="video-section">
            <h2>Original Video</h2>
            <video
              ref={videoRef}
              src={URL.createObjectURL(video)}
              controls
              style={{ width: "100%", maxWidth: "600px" }}
            />
          </div>
        )}
      </div>

      <ToastContainer />
    </div>
  );
};

export default App;
