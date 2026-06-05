import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Chat } from "./pages/Chat";
import { Dashboard } from "./pages/Dashboard";
import { Upload } from "./pages/Upload";
import { VideoDetail } from "./pages/VideoDetail";
import { VideoList } from "./pages/VideoList";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/videos" element={<VideoList />} />
          <Route path="/videos/:id" element={<VideoDetail />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;