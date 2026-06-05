import { create } from "zustand";

import { UploadProgress } from "../types";

interface UploadState {
  uploads: UploadProgress[];
  addUpload: (upload: UploadProgress) => void;
  updateUpload: (file: File, updates: Partial<UploadProgress>) => void;
  removeUpload: (file: File) => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  uploads: [],

  addUpload: (upload) =>
    set((state) => ({ uploads: [...state.uploads, upload] })),

  updateUpload: (file, updates) =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.file === file ? { ...u, ...updates } : u
      ),
    })),

  removeUpload: (file) =>
    set((state) => ({
      uploads: state.uploads.filter((u) => u.file !== file),
    })),
}));