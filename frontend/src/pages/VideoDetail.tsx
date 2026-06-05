import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, SkipForward } from "lucide-react";

import { fetchDetections, fetchVideo } from "../api/client";
import { Detection } from "../types";
import { useVideoStore } from "../stores/videoStore";

export function VideoDetail() {
  const { id } = useParams<{ id: string }>();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [, setCurrentTime] = useState(0); 
  const { selectedVideo, selectVideo } = useVideoStore();

  useEffect(() => {
    if (id) {
      loadVideo(id);
      loadDetections(id);
    }
  }, [id]);

  const loadVideo = async (videoId: string) => {
    try {
      const data = await fetchVideo(videoId);
      selectVideo(data);
    } catch (error) {
      console.error("Failed to load video:", error);
    }
  };

  const loadDetections = async (videoId: string) => {
    try {
      const data = await fetchDetections(videoId);
      setDetections(data.items);
    } catch (error) {
      console.error("Failed to load detections:", error);
    }
  };

  const jumpToTimestamp = (timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      videoRef.current.play();
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => window.history.back()}
          className="p-2 rounded-lg bg-sentinel-800 hover:bg-sentinel-700 transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-xl font-bold text-white">
            {selectedVideo?.filename || "Loading..."}
          </h2>
          <p className="text-sm text-sentinel-400">
            {selectedVideo?.resolution} • {selectedVideo?.duration_seconds?.toFixed(1)}s
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Video Player */}
        <div className="col-span-2">
          <div className="bg-sentinel-900 rounded-xl overflow-hidden aspect-video flex items-center justify-center">
            {selectedVideo ? (
              <video
                ref={videoRef}
                src={`http://localhost:8000/uploads/${selectedVideo.id}/video.mp4`}
                className="w-full h-full"
                controls
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
              />
            ) : (
              <div className="text-sentinel-600">Loading video...</div>
            )}
          </div>

          {/* Timeline Markers */}
          {detections.length > 0 && (
            <div className="mt-4 bg-sentinel-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-sentinel-200 mb-3">Detection Timeline</h3>
              <div className="relative h-8 bg-sentinel-700 rounded-full overflow-hidden">
                {detections.map((det) => {
                  const position = selectedVideo
                    ? (det.timestamp / selectedVideo.duration_seconds) * 100
                    : 0;

                  return (
                    <button
                      key={det.id}
                      onClick={() => jumpToTimestamp(det.timestamp)}
                      className={`absolute top-0 h-full w-1 hover:w-2 transition-all ${
                        det.is_anomaly ? "bg-danger-500" : "bg-accent-500"
                      }`}
                      style={{ left: `${Math.min(position, 99)}%` }}
                      title={`${det.timestamp.toFixed(1)}s: ${det.description}`}
                    />
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Detection List */}
        <div className="bg-sentinel-800 rounded-xl border border-sentinel-700 overflow-hidden">
          <div className="p-4 border-b border-sentinel-700">
            <h3 className="font-semibold text-white">Detections</h3>
            <p className="text-xs text-sentinel-400">{detections.length} events</p>
          </div>

          <div className="max-h-[500px] overflow-y-auto">
            {detections.length === 0 ? (
              <div className="p-4 text-center text-sentinel-400 text-sm">
                No detections yet. Processing...
              </div>
            ) : (
              detections.map((det) => (
                <div
                  key={det.id}
                  onClick={() => jumpToTimestamp(det.timestamp)}
                  className="p-4 border-b border-sentinel-700 hover:bg-sentinel-700 cursor-pointer transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {det.is_anomaly && (
                      <AlertTriangle size={16} className="text-danger-500 mt-0.5 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-sentinel-200 line-clamp-2">
                        {det.description}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-accent-500 font-mono">
                          {det.timestamp.toFixed(1)}s
                        </span>
                        <span className="text-xs text-sentinel-500 capitalize">
                          {det.object_class}
                        </span>
                        <span className="text-xs text-sentinel-500">
                          {(det.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {det.is_anomaly && (
                        <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-xs bg-danger-500/10 text-danger-500">
                          {det.anomaly_type}
                        </span>
                      )}
                    </div>
                    <SkipForward size={14} className="text-sentinel-500 shrink-0" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}