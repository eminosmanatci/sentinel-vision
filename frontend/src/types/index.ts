export interface Video {
  id: string;
  filename: string;
  duration_seconds: number;
  fps: number;
  resolution: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  processed_at: string | null;
}

export interface Detection {
  id: string;
  timestamp: number;
  frame_number: number;
  object_class: string;
  confidence: number;
  description: string;
  is_anomaly: boolean;
  anomaly_type: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{
    id: string;
    timestamp: number;
    description: string;
  }>;
}

export interface UploadProgress {
  file: File;
  progress: number;
  status: "uploading" | "processing" | "completed" | "error";
  videoId?: string;
}