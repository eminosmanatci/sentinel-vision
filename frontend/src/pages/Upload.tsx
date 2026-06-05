import { useCallback } from "react";

import { useDropzone } from "react-dropzone";
import { FileUp, Loader, CheckCircle, XCircle } from "lucide-react";

import { uploadVideo } from "../api/client";
import { useUploadStore } from "../stores/uploadStore";
import { useVideoStore } from "../stores/videoStore";

export function Upload() {
  const { uploads, addUpload, updateUpload, removeUpload } = useUploadStore();
  const { addVideo } = useVideoStore();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        addUpload({
          file,
          progress: 0,
          status: "uploading",
        });

        try {
          const data = await uploadVideo(file, (progress) => {
            updateUpload(file, { progress });
          });

          updateUpload(file, {
            status: "processing",
            videoId: data.id,
            progress: 100,
          });

          addVideo({
            id: data.id,
            filename: data.filename,
            duration_seconds: 0,
            fps: 0,
            resolution: "",
            status: "pending",
            created_at: new Date().toISOString(),
            processed_at: null,
          });

          // Simulate processing completion check
          setTimeout(() => {
            updateUpload(file, { status: "completed" });
          }, 3000);

        } catch (error) {
          updateUpload(file, { status: "error" });
          console.error("Upload failed:", error);
        }
      }
    },
    [addUpload, updateUpload, removeUpload, addVideo]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/*": [".mp4", ".avi", ".mov"],
    },
    maxSize: 500 * 1024 * 1024,
  });

  return (
    <div className="p-8 max-w-4xl">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-white">Upload Video</h2>
        <p className="text-sentinel-400 mt-1">Drag and drop security footage</p>
      </header>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-accent-500 bg-accent-500/10"
            : "border-sentinel-600 hover:border-sentinel-500"
        }`}
      >
        <input {...getInputProps()} />
        <FileUp size={48} className="mx-auto mb-4 text-sentinel-400" />
        <p className="text-lg font-medium text-sentinel-200">
          {isDragActive ? "Drop files here..." : "Drag & drop videos here"}
        </p>
        <p className="text-sm text-sentinel-500 mt-2">
          MP4, AVI, MOV up to 500MB
        </p>
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-semibold text-white">Uploads</h3>
          {uploads.map((upload, index) => (
            <UploadProgress key={index} upload={upload} onRemove={() => removeUpload(upload.file)} />
          ))}
        </div>
      )}
    </div>
  );
}

function UploadProgress({
  upload,
  onRemove,
}: {
  upload: import("../types").UploadProgress;
  onRemove: () => void;
}) {
  const statusIcons = {
    uploading: Loader,
    processing: Loader,
    completed: CheckCircle,
    error: XCircle,
  };

  const statusColors = {
    uploading: "text-accent-500",
    processing: "text-warning-500",
    completed: "text-success-500",
    error: "text-danger-500",
  };

  const StatusIcon = statusIcons[upload.status];

  return (
    <div className="bg-sentinel-800 rounded-lg border border-sentinel-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <StatusIcon size={18} className={`${statusColors[upload.status]} ${upload.status === "uploading" || upload.status === "processing" ? "animate-spin" : ""}`} />
          <span className="text-sm font-medium text-sentinel-200 truncate max-w-md">
            {upload.file.name}
          </span>
        </div>
        <button
          onClick={onRemove}
          className="text-sentinel-500 hover:text-sentinel-300"
        >
          <XCircle size={16} />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-sentinel-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${
            upload.status === "error"
              ? "bg-danger-500"
              : upload.status === "completed"
              ? "bg-success-500"
              : "bg-accent-500"
          }`}
          style={{ width: `${upload.progress}%` }}
        />
      </div>

      <p className="text-xs text-sentinel-400 mt-1 capitalize">
        {upload.status} • {upload.progress}%
      </p>
    </div>
  );
}