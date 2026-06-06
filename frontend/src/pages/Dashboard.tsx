import { useEffect } from "react";
import { AlertTriangle, FileUp, Video } from "lucide-react";
import { fetchVideos } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { useVideoStore } from "../stores/videoStore";

export function Dashboard() {
  const { videos, setVideos, isLoading, setLoading } = useVideoStore();

  useEffect(() => {
    // Initial fetch
    const loadInitial = async () => {
      setLoading(true);
      try {
        const data = await fetchVideos(6);
        setVideos(data.items);
      } finally {
        setLoading(false);
      }
    };
    loadInitial();

    // Silent polling for status updates
    const interval = setInterval(async () => {
      const hasProcessing = videos.some((v) => v.status === "processing");
      if (hasProcessing) {
        try {
          const data = await fetchVideos(6);
          setVideos(data.items);
        } catch (error) {
          console.error("Polling failed:", error);
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []); 

  const processingVideos = videos.filter((v) => v.status === "processing");
  const anomalyCount = videos.filter((v) => v.status === "completed").length; 

  return (
    <div className="p-8">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-sentinel-400 mt-1">AI-powered security analytics control panel</p>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <StatCard icon={Video} label="Total Videos" value={videos.length} color="text-accent-500" />
        <StatCard icon={FileUp} label="Processing" value={processingVideos.length} color="text-warning-500" />
        <StatCard icon={AlertTriangle} label="Anomalies" value={anomalyCount} color="text-danger-500" />
      </div>

      <section>
        <h3 className="text-lg font-semibold text-white mb-4">Recent Recordings</h3>

        {isLoading && videos.length === 0 ? (
          <div className="text-center py-12 text-sentinel-400 animate-pulse">Loading footage...</div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12 text-sentinel-400">No videos found. Upload your first footage.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-sentinel-800 rounded-xl border border-sentinel-700 p-6 shadow-sm">
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