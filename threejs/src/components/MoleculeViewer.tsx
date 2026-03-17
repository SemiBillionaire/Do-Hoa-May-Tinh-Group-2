import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

type Props = {
  url: string;
  className?: string;
};

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

    const canvas = document.createElement("canvas");
    canvas.style.display = "block";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    host.appendChild(canvas);

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

    const loader = new GLTFLoader();
    loader.load(
      url,
      (gltf) => {
        if (disposed) return;
        const model = gltf.scene;
        stripBlenderLabels(model);
        root.clear();
        root.add(model);
        frameCameraToObject(camera, controls, model);
        dirty = true;
      },
      undefined,
      () => {
        // keep empty; host still shows background overlay
      }
    );

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
      cancelAnimationFrame(raf);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      host.innerHTML = "";
    };
  }, [url]);

  return <div ref={hostRef} className={className} />;
}

