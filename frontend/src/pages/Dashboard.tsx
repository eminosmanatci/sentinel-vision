import { useEffect } from "react";

import { AlertTriangle, FileUp, Video } from "lucide-react";

import { fetchVideos } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { useVideoStore } from "../stores/videoStore";

export function Dashboard() {
  const { videos, setVideos, isLoading, setLoading } = useVideoStore();

  useEffect(() => {
    loadVideos();
    const interval = setInterval(loadVideos, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const data = await fetchVideos(6);
      setVideos(data.items);
    } catch (error) {
      console.error("Failed to load videos:", error);
    } finally {
      setLoading(false);
    }
  };

  const processingVideos = videos.filter((v) => v.status === "processing");
  const anomalyCount = 0; // Will be implemented with real data

  return (
    <div className="p-8">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-sentinel-400 mt-1">Overview of your security footage</p>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <StatCard
          icon={Video}
          label="Total Videos"
          value={videos.length}
          color="text-accent-500"
        />
        <StatCard
          icon={FileUp}
          label="Processing"
          value={processingVideos.length}
          color="text-warning-500"
        />
        <StatCard
          icon={AlertTriangle}
          label="Anomalies"
          value={anomalyCount}
          color="text-danger-500"
        />
      </div>

      {/* Recent Videos */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Recent Videos</h3>
        </div>

        {isLoading && videos.length === 0 ? (
          <div className="text-center py-12 text-sentinel-400">Loading...</div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12 text-sentinel-400">
            No videos yet. Upload your first security footage.
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-6">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Video;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-sentinel-800 rounded-xl border border-sentinel-700 p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg bg-sentinel-700 ${color}`}>
          <Icon size={24} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-sentinel-400">{label}</p>
        </div>
      </div>
    </div>
  );
}