import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

export const uploadVideo = async (file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });

  return response.data;
};

export const fetchVideos = async (limit = 50, offset = 0) => {
  const response = await api.get(`/videos?limit=${limit}&offset=${offset}`);
  return response.data;
};

export const fetchVideo = async (id: string) => {
  const response = await api.get(`/videos/${id}`);
  return response.data;
};

export const fetchDetections = async (videoId: string) => {
  const response = await api.get(`/videos/${videoId}/detections`);
  return response.data;
};

export const sendChatQuery = async (query: string, videoId?: string) => {
  const response = await api.post("/chat", {
    query,
    video_id: videoId,
  });
  return response.data;
};