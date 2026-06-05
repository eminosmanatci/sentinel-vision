import { Link } from "react-router-dom";

import { AlertTriangle, CheckCircle, Clock, Loader } from "lucide-react";

import type { Video } from "../types";

interface VideoCardProps {
  video: Video;
}

const statusConfig = {
  pending: { icon: Clock, color: "text-sentinel-400", bg: "bg-sentinel-700" },
  processing: { icon: Loader, color: "text-warning-500", bg: "bg-warning-500/10" },
  completed: { icon: CheckCircle, color: "text-success-500", bg: "bg-success-500/10" },
  failed: { icon: AlertTriangle, color: "text-danger-500", bg: "bg-danger-500/10" },
};

export function VideoCard({ video }: VideoCardProps) {
  const StatusIcon = statusConfig[video.status].icon;

  return (
    <Link
      to={`/videos/${video.id}`}
      className="block bg-sentinel-800 rounded-xl border border-sentinel-700 hover:border-accent-500 transition-all group"
    >
      <div className="aspect-video bg-sentinel-900 rounded-t-xl flex items-center justify-center relative overflow-hidden">
        <div className="text-sentinel-600">
          <Video size={48} />
        </div>
        <div className={`absolute top-3 right-3 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${statusConfig[video.status].bg}`}>
          <StatusIcon size={12} className={statusConfig[video.status].color} />
          <span className={statusConfig[video.status].color}>{video.status}</span>
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-medium text-sentinel-100 truncate group-hover:text-accent-500 transition-colors">
          {video.filename}
        </h3>
        <div className="flex items-center gap-4 mt-2 text-xs text-sentinel-400">
          <span>{video.resolution || "Unknown"}</span>
          <span>{video.duration_seconds ? `${video.duration_seconds.toFixed(1)}s` : "Processing..."}</span>
        </div>
      </div>
    </Link>
  );
}

function Video(props: { size: number }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={props.size}
      height={props.size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m22 8-6 4 6 4V8Z" />
      <rect width="14" height="12" x="2" y="6" rx="2" ry="2" />
    </svg>
  );
}