import { Navigate, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home";
import { Chapter1 } from "./pages/Chapter1";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/phan-1" element={<Chapter1 />} />
      <Route path="/phan-2" element={<Navigate to="/" replace />} />
      <Route path="/phan-3" element={<Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

