import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";

export function Home() {
  const chapters = [
    {
      title: "Phần 1: Khái niệm Acid",
      path: "/phan-1",
      description: "Tìm hiểu về khái niệm và định nghĩa Acid",
    },
    {
      title: "Phần 2: Tính chất hóa học",
      path: "/phan-2",
      description: "Nghiên cứu các tính chất hóa học của Acid",
    },
    {
      title: "Phần 3: Một số Acid thông dụng",
      path: "/phan-3",
      description: "Tìm hiểu về các loại Acid phổ biến trong thực tế",
    },
  ];

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 border border-[rgba(120,220,220,0.35)] bg-[rgba(20,10,40,0.55)]">
            <BookOpen className="w-10 h-10 text-[var(--accent)]" />
          </div>
          <h1 className="text-5xl font-bold text-[var(--text)] mb-4 drop-shadow-sm">Bài 8: Acid</h1>
        </div>

        <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-6">
          {chapters.map((chapter, index) => (
            <Link
              key={index}
              to={chapter.path}
              className="group rounded-xl transition-all duration-300 p-6 border border-[var(--border)] bg-[var(--card)] hover:border-[var(--border-strong)]"
            >
              <div className="flex flex-col h-full">
                <div className="flex items-center justify-center w-12 h-12 rounded-lg mb-4 transition-colors border border-[var(--border)] bg-[rgba(120,220,220,0.10)] text-[var(--accent)] group-hover:bg-[rgba(120,220,220,0.16)]">
                  <span className="text-2xl font-bold">{index + 1}</span>
                </div>
                <h2 className="text-xl font-bold text-[var(--text)] mb-3 transition-colors">
                  {chapter.title}
                </h2>
                <p className="text-[var(--muted)] text-sm flex-grow">{chapter.description}</p>
                <div className="mt-4 text-[var(--accent)] font-semibold group-hover:translate-x-2 transition-transform">
                  Xem chi tiết →
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

