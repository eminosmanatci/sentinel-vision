import { create } from "zustand";

import { Video } from "../types";

interface VideoState {
  videos: Video[];
  selectedVideo: Video | null;
  isLoading: boolean;
  error: string | null;

  setVideos: (videos: Video[]) => void;
  addVideo: (video: Video) => void;
  updateVideo: (video: Video) => void;
  selectVideo: (video: Video | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useVideoStore = create<VideoState>((set) => ({
  videos: [],
  selectedVideo: null,
  isLoading: false,
  error: null,

  setVideos: (videos) => set({ videos }),
  addVideo: (video) =>
    set((state) => ({ videos: [video, ...state.videos] })),
  updateVideo: (video) =>
    set((state) => ({
      videos: state.videos.map((v) => (v.id === video.id ? video : v)),
    })),
  selectVideo: (video) => set({ selectedVideo: video }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));