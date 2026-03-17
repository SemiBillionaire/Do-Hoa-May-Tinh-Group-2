import { Link } from "react-router-dom";
import { ArrowLeft, Beaker } from "lucide-react";
import { MoleculeViewer } from "../components/MoleculeViewer";

export function Chapter1() {
  const acids = [
    {
      name: "HCl",
      fullName: "Hydrochloric Acid",
      vietnameseName: "Axit Clohidric",
      modelUrl: "/models/HCl.glb",
    },
    {
      name: "HNO₃",
      fullName: "Nitric Acid",
      vietnameseName: "Axit Nitric",
      modelUrl: "/models/HNO3.glb",
    },
    {
      name: "H₂SO₄",
      fullName: "Sulfuric Acid",
      vietnameseName: "Axit Sulfuric",
      modelUrl: "/models/H2SO4.glb",
    },
  ];

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-12">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-[var(--accent)] hover:text-[var(--text)] mb-8 font-semibold transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Quay lại
        </Link>

        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 border border-[rgba(120,220,220,0.35)] bg-[rgba(20,10,40,0.55)]">
            <Beaker className="w-8 h-8 text-[var(--accent)]" />
          </div>
          <h1 className="text-4xl font-bold text-[var(--text)] mb-2 drop-shadow-sm">Phần 1: Khái niệm Acid</h1>
          <p className="max-w-4xl mx-auto mt-4 text-lg text-[var(--muted)] leading-relaxed">
            Acid ban đầu được biết đến là những chất có vị chua như acetic acid có trong giấm ăn, citric acid có trong
            quả chanh, maleic acid có trong quả táo. Từ acid xuất phát từ tiếng Latin là acidus - nghĩa là vị chua.
          </p>
        </div>

        <div className="max-w-6xl mx-auto grid grid-cols-1 gap-8">
          {acids.map((acid, index) => (
            <div
              key={index}
              className={`rounded-xl overflow-hidden transition-colors duration-300 border border-[var(--border)] bg-[var(--card-2)] flex ${
                index === 1 ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`relative w-[65%] h-80 bg-[linear-gradient(135deg,rgba(120,220,220,0.18)_0%,rgba(246,241,236,0.16)_45%,rgba(120,220,220,0.10)_100%)] flex items-center justify-center overflow-hidden ${
                  index === 1
                    ? "border-l border-[rgba(120,220,220,0.20)]"
                    : "border-r border-[rgba(120,220,220,0.20)]"
                }`}
              >
                <MoleculeViewer url={acid.modelUrl} className="absolute inset-0" />
                <div className="absolute inset-0 pointer-events-none"></div>
              </div>

              <div className="w-[35%] p-8 flex flex-col justify-center items-center text-center">
                <h2 className="text-5xl font-bold text-[var(--accent)] mb-4">{acid.name}</h2>
                <p className="text-xl font-semibold text-[var(--text)] mb-2">{acid.vietnameseName}</p>
                <p className="text-base text-[var(--muted-2)]">{acid.fullName}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="max-w-4xl mx-auto mt-12 rounded-xl p-8 border border-[var(--border)] bg-[var(--card)]">
          <h3 className="text-3xl font-bold text-[var(--text)] mb-4">Định nghĩa Acid</h3>
          <p className="text-lg text-[var(--muted)] leading-relaxed">
          Acid là những hợp chất trong phân tử có nguyên tử hydrogen liên kết với gốc acid. Khi tan trong nước, acid tạo ra ion H+.
          </p>
        </div>
      </div>
    </div>
  );
}

