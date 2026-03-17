import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

type Props = {
  url: string;
  className?: string;
};

function ionFromObjectName(name: string): string | null {
  const n = name.trim();

  // Prefer exact element symbols first
  if (/cl/i.test(n)) return "Cl⁻";

  const first = n[0]?.toUpperCase();
  switch (first) {
    case "H":
      return "H⁺";
    case "O":
      return "O²⁻";
    case "N":
      return "N⁵⁺";
    case "S":
      return "S⁶⁺";
    default:
      return null;
  }
}

function stripBlenderLabels(object3d: THREE.Object3D) {
  const toRemove: THREE.Object3D[] = [];
  object3d.traverse((o) => {
    if (typeof o.name === "string" && o.name.startsWith("Label_")) toRemove.push(o);
  });
  for (const o of toRemove) o.parent?.remove(o);
}

function frameCameraToObject(
  camera: THREE.PerspectiveCamera,
  controls: OrbitControls,
  object3d: THREE.Object3D
) {
  const box = new THREE.Box3().setFromObject(object3d);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  controls.target.copy(center);
  controls.update();

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = (camera.fov * Math.PI) / 180;
  let dist = maxDim / (2 * Math.tan(fov / 2));
  // Smaller factor => closer camera => model looks bigger at first render.
  dist *= 1.45;

  camera.position.set(center.x, center.y + maxDim * 0.25, center.z + dist);
  camera.near = Math.max(0.01, dist / 100);
  camera.far = dist * 50;
  camera.updateProjectionMatrix();
}

export function MoleculeViewer({ url, className }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    // Don't override layout (host can be `absolute inset-0`).
    // Only ensure a positioning context for the tooltip if it's currently `static`.
    if (getComputedStyle(host).position === "static") {
      host.style.position = "relative";
    }

    const canvas = document.createElement("canvas");
    canvas.style.display = "block";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    host.appendChild(canvas);

    // Tooltip
    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.left = "0px";
    tooltip.style.top = "0px";
    tooltip.style.transform = "translate(-9999px, -9999px)";
    tooltip.style.padding = "10px 12px";
    tooltip.style.borderRadius = "10px";
    // ~70% transparency
    tooltip.style.background = "rgba(10, 4, 18, 0.30)";
    tooltip.style.border = "1px solid rgba(120, 220, 220, 0.25)";
    tooltip.style.color = "rgba(246, 241, 236, 0.92)";
    tooltip.style.fontSize = "16px";
    tooltip.style.fontWeight = "800";
    tooltip.style.lineHeight = "1.15";
    tooltip.style.pointerEvents = "none";
    tooltip.style.whiteSpace = "nowrap";
    tooltip.style.backdropFilter = "blur(6px)";
    host.appendChild(tooltip);

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100);
    camera.position.set(0, 1.8, 4.5);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.8;
    controls.enablePan = true;
    controls.minDistance = 2.0;
    controls.maxDistance = 12.0;

    // Brighter lights for dark UI.
    scene.add(new THREE.AmbientLight(0xffffff, 1.15));
    const key = new THREE.DirectionalLight(0xffffff, 1.05);
    key.position.set(2.5, 4.5, 2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xdbeafe, 0.6);
    fill.position.set(-2.5, 1.0, 2.5);
    scene.add(fill);
    const rim = new THREE.DirectionalLight(0x93c5fd, 0.7);
    rim.position.set(-3, 2, -3);
    scene.add(rim);

    const root = new THREE.Group();
    scene.add(root);

    let disposed = false;
    let dirty = true;
    controls.addEventListener("change", () => (dirty = true));

    const raycaster = new THREE.Raycaster();
    const mouseNdc = new THREE.Vector2();
    /** @type {THREE.Object3D | null} */
    let modelRoot: THREE.Object3D | null = null;

    const loader = new GLTFLoader();
    loader.load(
      url,
      (gltf) => {
        if (disposed) return;
        const model = gltf.scene;
        stripBlenderLabels(model);
        root.clear();
        root.add(model);
        modelRoot = model;
        frameCameraToObject(camera, controls, model);
        dirty = true;
      },
      undefined,
      () => {
        // keep empty; host still shows background overlay
      }
    );

    const onPointerMove = (ev: PointerEvent) => {
      if (!modelRoot) return;
      const rect = host.getBoundingClientRect();
      const x = ev.clientX - rect.left;
      const y = ev.clientY - rect.top;

      mouseNdc.x = (x / rect.width) * 2 - 1;
      mouseNdc.y = -(y / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouseNdc, camera);

      const hits = raycaster.intersectObject(modelRoot, true);
      const hit = hits.find((h) => (h.object as any)?.isMesh);
      const name = hit?.object?.name || "";
      const ion = name ? ionFromObjectName(name) : null;

      if (!ion) {
        tooltip.style.transform = "translate(-9999px, -9999px)";
        return;
      }

      tooltip.textContent = ion;
      // Offset from cursor, clamp inside host
      const ox = 14;
      const oy = 14;
      const tx = Math.min(Math.max(8, x + ox), rect.width - 8);
      const ty = Math.min(Math.max(8, y + oy), rect.height - 8);
      tooltip.style.transform = `translate(${tx}px, ${ty}px)`;
    };

    const onPointerLeave = () => {
      tooltip.style.transform = "translate(-9999px, -9999px)";
    };

    host.addEventListener("pointermove", onPointerMove);
    host.addEventListener("pointerleave", onPointerLeave);

    const ro = new ResizeObserver(() => {
      const w = host.clientWidth;
      const h = host.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      dirty = true;
    });
    ro.observe(host);

    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      if (!dirty) return;
      controls.update();
      renderer.render(scene, camera);
      dirty = false;
    };
    tick();

    return () => {
      disposed = true;
      host.removeEventListener("pointermove", onPointerMove);
      host.removeEventListener("pointerleave", onPointerLeave);
      cancelAnimationFrame(raf);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      host.innerHTML = "";
    };
  }, [url]);

  return <div ref={hostRef} className={className} />;
}

