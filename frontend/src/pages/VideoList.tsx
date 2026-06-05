import { useEffect } from "react";

import { fetchVideos } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { useVideoStore } from "../stores/videoStore";

export function VideoList() {
  const { videos, setVideos, isLoading, setLoading } = useVideoStore();

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const data = await fetchVideos();
      setVideos(data.items);
    } catch (error) {
      console.error("Failed to load videos:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-white">All Videos</h2>
        <p className="text-sentinel-400 mt-1">{videos.length} total recordings</p>
      </header>

      {isLoading ? (
        <div className="text-center py-12 text-sentinel-400">Loading...</div>
      ) : videos.length === 0 ? (
        <div className="text-center py-12 text-sentinel-400">
          No videos uploaded yet.
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-6">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </div>
  );
}