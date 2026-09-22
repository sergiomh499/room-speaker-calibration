import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Compass, ZoomIn, ZoomOut, RotateCcw, Sparkles } from 'lucide-react';

export interface Spatial3DSpeaker {
  x: number;
  y: number;
  z: number;
  label: string;
  type: 'speaker' | 'subwoofer';
}

export interface Spatial3DPoint {
  point_id: number;
  x: number;
  y: number;
  z: number;
  color: string;
  distances: {
    Front_L?: number;
    Front_R?: number;
    Subwoofer?: number;
    [key: string]: number | undefined;
  };
}

export interface Spatial3DAveragedPosition {
  x: number;
  y: number;
  z: number;
  label: string;
  averaged_distances: {
    Front_L: number;
    Front_R: number;
    Subwoofer: number;
    [key: string]: number;
  };
}

export interface Spatial3DData {
  speakers: Record<string, Spatial3DSpeaker>;
  points: Record<string | number, Spatial3DPoint>;
  averaged_position?: Spatial3DAveragedPosition | null;
}

interface SpatialRoom3DProps {
  data?: Spatial3DData | null;
  className?: string;
  height?: number | string;
}

export const SpatialRoom3D: React.FC<SpatialRoom3DProps> = ({
  data,
  className = '',
  height = 480,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [selectedChannel, setSelectedChannel] = useState<'all' | 'Front_L' | 'Front_R' | 'Subwoofer'>('all');
  const [selectedPoint, setSelectedPoint] = useState<number | 'all' | 'avg'>('all');
  const [cameraPreset, setCameraPreset] = useState<'perspective' | 'top' | 'front'>('perspective');
  const [showRays, setShowRays] = useState<boolean>(true);
  const [showWavefronts, setShowWavefronts] = useState<boolean>(true);

  // References for Three.js animation loop & objects
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const dynamicGroupRef = useRef<THREE.Group | null>(null);
  const pulseRingsRef = useRef<THREE.Mesh[]>([]);

  // Orbit control state
  const isDragging = useRef(false);
  const prevMousePos = useRef({ x: 0, y: 0 });
  const cameraAngles = useRef({ sphericalTheta: 0.85, sphericalPhi: 1.15, radius: 6.2 });

  // 1. Initialize Three.js Scene
  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth || 800;
    const heightPx = typeof height === 'number' ? height : 480;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0d14);
    scene.fog = new THREE.FogExp2(0x0a0d14, 0.08);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / heightPx, 0.1, 50);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
      alpha: true,
    });
    renderer.setSize(width, heightPx);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Ambient & Directional Lighting
    const ambientLight = new THREE.AmbientLight(0x2a364f, 1.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(3, 7, 4);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const rimLight = new THREE.PointLight(0x6366f1, 2.5, 12);
    rimLight.position.set(-2, 3, -3);
    scene.add(rimLight);

    const subGlowLight = new THREE.PointLight(0x06b6d4, 1.8, 8);
    subGlowLight.position.set(1.35, 0.5, -3.3);
    scene.add(subGlowLight);

    // Floor Acoustic Distance Grid & Rings
    const gridHelper = new THREE.GridHelper(8, 32, 0x312e81, 0x1e293b);
    gridHelper.position.y = 0;
    scene.add(gridHelper);

    // Concentric Range Rings from Sweet Spot (1m, 2m, 3m, 4m)
    [1.0, 2.0, 3.0, 4.0].forEach(rad => {
      const ringGeo = new THREE.RingGeometry(rad - 0.015, rad + 0.015, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x4f46e5,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(0, 0.002, 0);
      scene.add(ring);
    });

    // Front Wall Plane (Acoustic Baffle Wall)
    const wallGeo = new THREE.PlaneGeometry(6.4, 3.2);
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.9,
    });
    const frontWall = new THREE.Mesh(wallGeo, wallMat);
    frontWall.position.set(0, 1.6, -3.8);
    scene.add(frontWall);

    // TV Representation on Front Wall
    const tvGeo = new THREE.BoxGeometry(2.2, 1.25, 0.06);
    const tvMat = new THREE.MeshStandardMaterial({
      color: 0x020617,
      metalness: 0.8,
      roughness: 0.2,
    });
    const tv = new THREE.Mesh(tvGeo, tvMat);
    tv.position.set(0, 1.6, -3.75);
    scene.add(tv);

    // Dynamic objects group (speakers, points, rays, wavefronts)
    const dynamicGroup = new THREE.Group();
    scene.add(dynamicGroup);
    dynamicGroupRef.current = dynamicGroup;

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const updateCameraPos = () => {
      if (!cameraRef.current) return;
      const theta = cameraAngles.current.sphericalTheta;
      const phi = cameraAngles.current.sphericalPhi;
      const r = cameraAngles.current.radius;
      cameraRef.current.position.x = r * Math.sin(phi) * Math.sin(theta);
      cameraRef.current.position.y = r * Math.cos(phi);
      cameraRef.current.position.z = r * Math.sin(phi) * Math.cos(theta);
      cameraRef.current.lookAt(0, 0.8, -0.6);
    };

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Pulse animation on rings
      pulseRingsRef.current.forEach((ring, i) => {
        const scale = 1.0 + 0.15 * Math.sin(elapsedTime * 3.0 + i);
        ring.scale.set(scale, scale, 1);
      });

      updateCameraPos();
      renderer.render(scene, camera);
    };

    updateCameraPos();
    animate();

    // Handle Resize
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      cameraRef.current.aspect = w / heightPx;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, heightPx);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [height]);

  // 2. Populate 3D Objects when data or filters change
  useEffect(() => {
    const dynamicGroup = dynamicGroupRef.current;
    if (!dynamicGroup) return;

    // Clear previous dynamic meshes
    while (dynamicGroup.children.length > 0) {
      dynamicGroup.remove(dynamicGroup.children[0]);
    }
    pulseRingsRef.current = [];

    // Fallback hardware speaker coordinates if not provided
    const speakers = data?.speakers || {
      Front_L: { x: -1.225, y: 1.0, z: -2.122, label: 'Frontal Izq (Q 3020i)', type: 'speaker' },
      Front_R: { x: 1.175, y: 1.0, z: -2.035, label: 'Frontal Der (Q 3020i)', type: 'speaker' },
      Subwoofer: { x: 1.35, y: 0.2, z: -3.295, label: 'Subwoofer (Focal Cub Evo)', type: 'subwoofer' },
    };

    // A. Render Speakers & Subwoofer
    Object.entries(speakers).forEach(([key, spk]) => {
      const isSub = spk.type === 'subwoofer';
      const spkGroup = new THREE.Group();
      spkGroup.position.set(spk.x, spk.y, spk.z);

      if (isSub) {
        // Subwoofer Cube (Focal Cub Evo)
        const subMat = new THREE.MeshStandardMaterial({
          color: 0x0891b2,
          metalness: 0.4,
          roughness: 0.3,
        });
        const subMesh = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.32, 0.32), subMat);
        subMesh.position.y = 0.16;
        spkGroup.add(subMesh);

        // Subwoofer Woofer Driver Cone
        const driverMat = new THREE.MeshStandardMaterial({ color: 0x164e63, roughness: 0.6 });
        const driver = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.06, 0.04, 32), driverMat);
        driver.rotation.x = Math.PI / 2;
        driver.position.set(0, 0.16, 0.17);
        spkGroup.add(driver);

        // Bass emission wave rings
        if (showWavefronts) {
          [0.6, 1.0, 1.4].forEach((rad, i) => {
            const waveGeo = new THREE.RingGeometry(rad, rad + 0.02, 32);
            const waveMat = new THREE.MeshBasicMaterial({
              color: 0x06b6d4,
              transparent: true,
              opacity: 0.35 - i * 0.1,
              side: THREE.DoubleSide,
            });
            const wave = new THREE.Mesh(waveGeo, waveMat);
            wave.rotation.x = -Math.PI / 2;
            wave.position.y = 0.01;
            spkGroup.add(wave);
            pulseRingsRef.current.push(wave);
          });
        }
      } else {
        // Bookshelf Speaker (Q Acoustics 3020i)
        const spkMat = new THREE.MeshStandardMaterial({
          color: 0x312e81,
          metalness: 0.3,
          roughness: 0.4,
        });
        const spkMesh = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.28, 0.26), spkMat);
        spkGroup.add(spkMesh);

        // Tweeter & Midbass Driver
        const twMat = new THREE.MeshStandardMaterial({ color: 0x818cf8, metalness: 0.9, roughness: 0.2 });
        const tw = new THREE.Mesh(new THREE.SphereGeometry(0.025, 16, 16), twMat);
        tw.position.set(0, 0.06, 0.135);
        spkGroup.add(tw);

        const wooferMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.5 });
        const woofer = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.03, 0.02, 24), wooferMat);
        woofer.rotation.x = Math.PI / 2;
        woofer.position.set(0, -0.05, 0.135);
        spkGroup.add(woofer);

        // Speaker Stand
        const standMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 });
        const standPole = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, spk.y - 0.14, 16), standMat);
        standPole.position.y = -(spk.y - 0.14) / 2;
        spkGroup.add(standPole);

        const standBase = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.02, 0.26), standMat);
        standBase.position.y = -spk.y + 0.01;
        spkGroup.add(standBase);
      }

      // Speaker Label Billboard Sprite
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = isSub ? '#0891b2' : '#4f46e5';
        ctx.fillRect(0, 0, 256, 64);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 24px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(isSub ? 'SUB (Focal Cub)' : key === 'Front_L' ? 'Front L (3020i)' : 'Front R (3020i)', 128, 42);
      }
      const labelTex = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: labelTex });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(0.7, 0.18, 1);
      sprite.position.set(0, isSub ? 0.55 : 0.26, 0);
      spkGroup.add(sprite);

      dynamicGroup.add(spkGroup);
    });

    // B. Render Measurement Points (P1 to P5)
    const rawPoints = data?.points || {};
    const pointEntries = Object.values(rawPoints);

    pointEntries.forEach(pt => {
      if (selectedPoint !== 'all' && selectedPoint !== 'avg' && selectedPoint !== pt.point_id) {
        return;
      }

      const ptGroup = new THREE.Group();
      ptGroup.position.set(pt.x, pt.y, pt.z);

      const colorHex = parseInt(pt.color.replace('#', '0x'), 16) || 0x6366f1;

      // Microphone Sphere Marker
      const sphereMat = new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.6,
        roughness: 0.2,
      });
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.055, 24, 24), sphereMat);
      ptGroup.add(sphere);

      // Floor Drop Line & Pulse Ring
      const dropLineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, -pt.y, 0),
      ]);
      const dropLineMat = new THREE.LineDashedMaterial({
        color: colorHex,
        dashSize: 0.05,
        gapSize: 0.05,
      });
      const dropLine = new THREE.Line(dropLineGeo, dropLineMat);
      dropLine.computeLineDistances();
      ptGroup.add(dropLine);

      const ringGeo = new THREE.RingGeometry(0.12, 0.15, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: colorHex,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.5,
      });
      const floorRing = new THREE.Mesh(ringGeo, ringMat);
      floorRing.rotation.x = -Math.PI / 2;
      floorRing.position.y = -pt.y + 0.005;
      ptGroup.add(floorRing);

      // Point Tag Sprite (e.g. "P1", "P4")
      const tagCanvas = document.createElement('canvas');
      tagCanvas.width = 128;
      tagCanvas.height = 128;
      const tagCtx = tagCanvas.getContext('2d');
      if (tagCtx) {
        tagCtx.beginPath();
        tagCtx.arc(64, 64, 56, 0, 2 * Math.PI);
        tagCtx.fillStyle = pt.color;
        tagCtx.fill();
        tagCtx.strokeStyle = '#ffffff';
        tagCtx.lineWidth = 6;
        tagCtx.stroke();
        tagCtx.fillStyle = '#ffffff';
        tagCtx.font = 'bold 50px sans-serif';
        tagCtx.textAlign = 'center';
        tagCtx.textBaseline = 'middle';
        tagCtx.fillText(`P${pt.point_id}`, 64, 64);
      }
      const tagTex = new THREE.CanvasTexture(tagCanvas);
      const tagSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tagTex }));
      tagSprite.scale.set(0.24, 0.24, 1);
      tagSprite.position.set(0, 0.12, 0);
      ptGroup.add(tagSprite);

      // Acoustic Rays to Speakers
      if (showRays) {
        Object.entries(speakers).forEach(([spkKey, spk]) => {
          if (selectedChannel !== 'all' && selectedChannel !== spkKey) return;

          const rayMat = new THREE.LineBasicMaterial({
            color: colorHex,
            transparent: true,
            opacity: 0.45,
          });
          const rayGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(spk.x - pt.x, spk.y - pt.y, spk.z - pt.z),
          ]);
          const ray = new THREE.Line(rayGeo, rayMat);
          ptGroup.add(ray);
        });
      }

      dynamicGroup.add(ptGroup);
    });

    // C. Render Final Averaged Position (Posicionamiento Promediado Master)
    if (data?.averaged_position && (selectedPoint === 'all' || selectedPoint === 'avg')) {
      const avg = data.averaged_position;
      const avgGroup = new THREE.Group();
      avgGroup.position.set(avg.x, avg.y, avg.z);

      // Glowing Gold / Diamond Master Beacon
      const beaconMat = new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        emissive: 0xfbbf24,
        emissiveIntensity: 0.9,
        metalness: 0.8,
        roughness: 0.1,
      });
      const beacon = new THREE.Mesh(new THREE.OctahedronGeometry(0.09, 0), beaconMat);
      beacon.rotation.y = Math.PI / 4;
      avgGroup.add(beacon);

      // Floor Drop Pillar
      const laserGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, -avg.y, 0),
      ]);
      const laserMat = new THREE.LineBasicMaterial({ color: 0xfbbf24, transparent: true, opacity: 0.85 });
      const laser = new THREE.Line(laserGeo, laserMat);
      avgGroup.add(laser);

      // Golden Halo Floor Rings
      [0.22, 0.35].forEach((rad, i) => {
        const haloGeo = new THREE.RingGeometry(rad, rad + 0.02, 32);
        const haloMat = new THREE.MeshBasicMaterial({
          color: 0xf59e0b,
          transparent: true,
          opacity: 0.6 - i * 0.25,
          side: THREE.DoubleSide,
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        halo.rotation.x = -Math.PI / 2;
        halo.position.y = -avg.y + 0.006;
        avgGroup.add(halo);
        pulseRingsRef.current.push(halo);
      });

      // Master Beacon Sprite Label
      const avgCanvas = document.createElement('canvas');
      avgCanvas.width = 320;
      avgCanvas.height = 72;
      const avgCtx = avgCanvas.getContext('2d');
      if (avgCtx) {
        avgCtx.fillStyle = '#f59e0b';
        avgCtx.roundRect?.(0, 0, 320, 72, 12);
        avgCtx.fill();
        avgCtx.fillStyle = '#0f172a';
        avgCtx.font = 'bold 26px sans-serif';
        avgCtx.textAlign = 'center';
        avgCtx.fillText('★ Posición Promedio Master', 160, 46);
      }
      const avgTex = new THREE.CanvasTexture(avgCanvas);
      const avgSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: avgTex }));
      avgSprite.scale.set(0.85, 0.2, 1);
      avgSprite.position.set(0, 0.22, 0);
      avgGroup.add(avgSprite);

      // Promediado Acoustic Rays to all 3 channels
      if (showRays) {
        Object.entries(speakers).forEach(([spkKey, spk]) => {
          if (selectedChannel !== 'all' && selectedChannel !== spkKey) return;

          const goldRayMat = new THREE.LineDashedMaterial({
            color: 0xf59e0b,
            dashSize: 0.08,
            gapSize: 0.04,
          });
          const goldRayGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(spk.x - avg.x, spk.y - avg.y, spk.z - avg.z),
          ]);
          const goldRay = new THREE.Line(goldRayGeo, goldRayMat);
          goldRay.computeLineDistances();
          avgGroup.add(goldRay);
        });
      }

      dynamicGroup.add(avgGroup);
    }
  }, [data, selectedChannel, selectedPoint, showRays, showWavefronts]);

  // 3. Camera Preset transitions
  const applyCameraPreset = (preset: 'perspective' | 'top' | 'front') => {
    setCameraPreset(preset);
    if (preset === 'perspective') {
      cameraAngles.current = { sphericalTheta: 0.85, sphericalPhi: 1.15, radius: 6.2 };
    } else if (preset === 'top') {
      cameraAngles.current = { sphericalTheta: 0.0, sphericalPhi: 0.05, radius: 6.0 };
    } else if (preset === 'front') {
      cameraAngles.current = { sphericalTheta: 0.0, sphericalPhi: Math.PI / 2, radius: 5.5 };
    }
  };

  // Mouse drag handlers for custom orbit rotation
  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    prevMousePos.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;
    const dx = e.clientX - prevMousePos.current.x;
    const dy = e.clientY - prevMousePos.current.y;
    prevMousePos.current = { x: e.clientX, y: e.clientY };

    cameraAngles.current.sphericalTheta -= dx * 0.008;
    cameraAngles.current.sphericalPhi = Math.max(
      0.05,
      Math.min(Math.PI / 2 - 0.02, cameraAngles.current.sphericalPhi - dy * 0.008)
    );
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    cameraAngles.current.radius = Math.max(2.5, Math.min(10.0, cameraAngles.current.radius + e.deltaY * 0.005));
  };

  const avgDistances = data?.averaged_position?.averaged_distances;

  return (
    <div className={`flex flex-col bg-surface-1 border border-border-subtle rounded-xl overflow-hidden shadow-2xl ${className}`}>
      {/* Topbar Controls */}
      <div className="p-3 bg-surface-2/60 border-b border-border-subtle flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
          <span className="font-semibold text-white tracking-wide flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
            Visualización 3D Sala & Posicionamiento Acústico
          </span>
        </div>

        {/* Camera Views */}
        <div className="flex items-center gap-1 bg-surface-1 p-1 rounded-lg border border-border-subtle">
          <button
            className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
              cameraPreset === 'perspective' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
            onClick={() => applyCameraPreset('perspective')}
          >
            3D Libre
          </button>
          <button
            className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
              cameraPreset === 'top' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
            onClick={() => applyCameraPreset('top')}
          >
            Planta (Superior)
          </button>
          <button
            className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
              cameraPreset === 'front' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
            onClick={() => applyCameraPreset('front')}
          >
            Frontal
          </button>
        </div>

        {/* Channels Filter */}
        <div className="flex items-center gap-1 bg-surface-1 p-1 rounded-lg border border-border-subtle">
          {(['all', 'Front_L', 'Front_R', 'Subwoofer'] as const).map(ch => (
            <button
              key={ch}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
                selectedChannel === ch ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              onClick={() => setSelectedChannel(ch)}
            >
              {ch === 'all' ? 'Todos' : ch === 'Subwoofer' ? 'SUB' : ch.replace('Front_', '')}
            </button>
          ))}
        </div>

        {/* Points Filter */}
        <div className="flex items-center gap-1 bg-surface-1 p-1 rounded-lg border border-border-subtle">
          {(['all', 'avg', 1, 2, 3, 4, 5] as const).map(ptKey => (
            <button
              key={String(ptKey)}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
                selectedPoint === ptKey ? 'bg-amber-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
              onClick={() => setSelectedPoint(ptKey)}
            >
              {ptKey === 'all' ? 'Todos' : ptKey === 'avg' ? '★ Promedio' : `P${ptKey}`}
            </button>
          ))}
        </div>

        {/* Toggles */}
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-[11px] text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showRays}
              onChange={e => setShowRays(e.target.checked)}
              className="rounded bg-surface-3 border-border-subtle text-indigo-600"
            />
            <span>Rayos</span>
          </label>
          <label className="flex items-center gap-1 text-[11px] text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showWavefronts}
              onChange={e => setShowWavefronts(e.target.checked)}
              className="rounded bg-surface-3 border-border-subtle text-cyan-600"
            />
            <span>Ondas Sub</span>
          </label>
        </div>
      </div>

      {/* 3D Canvas Area */}
      <div
        ref={containerRef}
        className="relative w-full overflow-hidden cursor-grab active:cursor-grabbing select-none"
        style={{ height }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Floating Controls Overlay */}
        <div className="absolute top-3 left-3 flex flex-col gap-1.5 pointer-events-auto">
          <div className="p-2 rounded-lg bg-surface-1/85 backdrop-blur-md border border-border-subtle text-[11px] text-slate-300 flex flex-col gap-1 shadow-lg">
            <div className="font-semibold text-white flex items-center gap-1 border-b border-border-subtle/50 pb-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Posicionamiento Promediado (Master)
            </div>
            {avgDistances ? (
              <div className="grid grid-cols-3 gap-2 font-mono text-[10px] mt-0.5">
                <div className="bg-surface-2/60 px-2 py-1 rounded border border-indigo-500/20">
                  <span className="text-slate-400 block">Front L:</span>
                  <span className="font-semibold text-indigo-300">{avgDistances.Front_L} m</span>
                </div>
                <div className="bg-surface-2/60 px-2 py-1 rounded border border-indigo-500/20">
                  <span className="text-slate-400 block">Front R:</span>
                  <span className="font-semibold text-indigo-300">{avgDistances.Front_R} m</span>
                </div>
                <div className="bg-surface-2/60 px-2 py-1 rounded border border-cyan-500/20">
                  <span className="text-slate-400 block">SUB Focal:</span>
                  <span className="font-semibold text-cyan-300">{avgDistances.Subwoofer} m</span>
                </div>
              </div>
            ) : (
              <span className="text-slate-400 italic">Pendiente de mediciones</span>
            )}
          </div>
        </div>

        {/* Zoom & Reset Buttons */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 bg-surface-1/80 backdrop-blur-md p-1.5 rounded-lg border border-border-subtle shadow-md">
          <button
            className="p-1 text-slate-300 hover:text-white rounded hover:bg-surface-2 transition-colors"
            title="Acercar"
            onClick={() => (cameraAngles.current.radius = Math.max(2.5, cameraAngles.current.radius - 0.5))}
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            className="p-1 text-slate-300 hover:text-white rounded hover:bg-surface-2 transition-colors"
            title="Alejar"
            onClick={() => (cameraAngles.current.radius = Math.min(10.0, cameraAngles.current.radius + 0.5))}
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            className="p-1 text-slate-300 hover:text-white rounded hover:bg-surface-2 transition-colors"
            title="Restablecer Cámara"
            onClick={() => applyCameraPreset('perspective')}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 bg-surface-1/80 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-border-subtle text-[10px] font-mono flex items-center gap-3 text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-indigo-500" /> P1
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> P2
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500" /> P3
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400" /> P4
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-pink-500" /> P5
          </span>
          <span className="flex items-center gap-1 border-l border-border-subtle pl-2 font-semibold text-amber-400">
            ★ Promedio
          </span>
        </div>
      </div>
    </div>
  );
};
