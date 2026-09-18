/**
 * OCTAVE — 3D Acoustic Room & Measurement Cluster Visualizer
 * Nivel: Luxury Organic Archviz & Pro Calibration Studio (V4)
 * 
 * Correcciones fundamentales:
 * 1. TV apoyada físicamente: Peana Alpine metálica de la LG C5 apoyada directamente sobre la superficie del aparador (cero flotación).
 * 2. Puntos de calibración a escala real (40 cm de separación): P1 Centro, P2/P3 a ±40 cm (ancho de hombros/escucha), P4/P5 a ±35 cm (área corporal/reclinación).
 * 3. Geometrías redondeadas y orgánicas (anti-Minecraft):
 *    - Aparador con cantos redondeados y curvas suaves.
 *    - Altavoces Q Acoustics 3020i con radio de curvatura suave característico en esquinas y baffle.
 *    - Palillería semicilíndrica suave con iluminación indirecta.
 *    - Butaca de diseño con cojines ergonómicos de bordes acolchados y redondeados.
 *    - Trípode telescópico con micrófono calibrado UMIK-1 a 1.00m.
 */

(function() {
  'use strict';

  let scene, camera, renderer, controls, pmremGenerator;
  let container, canvas;
  let animId = null;
  let pointsGroup;
  let pointMeshes = {};
  let pointRings = {};
  let pointNumberSprites = {};
  let activeTagSprite = null;
  let activePointId = 1;
  let pointsStatus = { 1: false, 2: false, 3: false, 4: false, 5: false };
  let acousticWaveGroup;
  let raycaster, mouse;
  let targetCamPos = null;
  let targetControlsTarget = null;
  let clock;
  let envMap = null;

  // 5 Puntos de Medición Realistas (40 cm de separación acústica)
  const CLUSTER_POINTS = {
    1: { num: '1', name: 'P1 Centro (Sweet Spot)', label: 'P1 · Sweet Spot', offset: 'Posición de oído central (1.00m)', x: 0.0, y: 1.0, z: 0.5, color: 0xf59e0b, hex: '#f59e0b' },
    2: { num: '2', name: 'P2 Izquierda', label: 'P2 · Izquierda (−40cm)', offset: '−40 cm a la izquierda (hombro izq)', x: -0.40, y: 1.0, z: 0.5, color: 0x38bdf8, hex: '#38bdf8' },
    3: { num: '3', name: 'P3 Derecha', label: 'P3 · Derecha (+40cm)', offset: '+40 cm a la derecha (hombro der)', x: 0.40, y: 1.0, z: 0.5, color: 0x10b981, hex: '#10b981' },
    4: { num: '4', name: 'P4 Frontal', label: 'P4 · Frontal (−35cm)', offset: '−35 cm hacia pantalla (inclinación)', x: 0.0, y: 1.0, z: 0.15, color: 0xf97316, hex: '#f97316' },
    5: { num: '5', name: 'P5 Trasero', label: 'P5 · Trasero (+35cm)', offset: '+35 cm hacia respaldo (reclinación)', x: 0.0, y: 1.0, z: 0.85, color: 0xeab308, hex: '#eab308' }
  };

  // =========================================================================
  // 1. HELPER DE GEOMETRÍA ORGÁNICA REDONDEADA (Anti-Minecraft)
  // =========================================================================

  function createRoundedBoxGeometry(w, h, d, r, bevelSegments = 6) {
    const shape = new THREE.Shape();
    const hw = Math.max(0.001, w / 2 - r);
    const hh = Math.max(0.001, h / 2 - r);
    
    shape.moveTo(-hw, -hh - r);
    shape.lineTo(hw, -hh - r);
    shape.quadraticCurveTo(hw + r, -hh - r, hw + r, -hh);
    shape.lineTo(hw + r, hh);
    shape.quadraticCurveTo(hw + r, hh + r, hw, hh + r);
    shape.lineTo(-hw, hh + r);
    shape.quadraticCurveTo(-hw - r, hh + r, -hw - r, hh);
    shape.lineTo(-hw - r, -hh);
    shape.quadraticCurveTo(-hw - r, -hh - r, -hw, -hh - r);

    const extrudeSettings = {
      depth: Math.max(0.001, d - r * 2),
      bevelEnabled: true,
      bevelSegments: bevelSegments,
      steps: 1,
      bevelSize: r,
      bevelThickness: r,
      curveSegments: 16
    };
    const geo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    geo.center();
    return geo;
  }

  // =========================================================================
  // 2. GENERADORES DE TEXTURAS PROCEDURALES PBR & ENTORNO IBL
  // =========================================================================

  function generateStudioEnvMap(glRenderer) {
    const cv = document.createElement('canvas');
    cv.width = 1024;
    cv.height = 512;
    const ctx = cv.getContext('2d');

    const bgGrad = ctx.createLinearGradient(0, 0, 0, 512);
    bgGrad.addColorStop(0, '#0b0f17');
    bgGrad.addColorStop(0.35, '#161d2b');
    bgGrad.addColorStop(0.65, '#131924');
    bgGrad.addColorStop(1, '#080b10');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1024, 512);

    const softboxKey = ctx.createRadialGradient(720, 110, 10, 720, 110, 180);
    softboxKey.addColorStop(0, '#ffffff');
    softboxKey.addColorStop(0.3, '#fff4de');
    softboxKey.addColorStop(0.7, '#e2a455');
    softboxKey.addColorStop(1, 'transparent');
    ctx.fillStyle = softboxKey;
    ctx.fillRect(520, 0, 400, 240);

    const softboxFill = ctx.createRadialGradient(250, 180, 10, 250, 180, 200);
    softboxFill.addColorStop(0, '#e8f0ff');
    softboxFill.addColorStop(0.4, '#9cbde8');
    softboxFill.addColorStop(1, 'transparent');
    ctx.fillStyle = softboxFill;
    ctx.fillRect(50, 20, 400, 320);

    const cove = ctx.createLinearGradient(0, 230, 0, 310);
    cove.addColorStop(0, 'transparent');
    cove.addColorStop(0.5, '#f59e0b');
    cove.addColorStop(1, 'transparent');
    ctx.fillStyle = cove;
    ctx.fillRect(0, 230, 1024, 80);

    const texture = new THREE.CanvasTexture(cv);
    pmremGenerator = new THREE.PMREMGenerator(glRenderer);
    pmremGenerator.compileEquirectangularShader();
    const renderTarget = pmremGenerator.fromEquirectangular(texture);
    texture.dispose();
    return renderTarget.texture;
  }

  function generateParquetTextures() {
    const size = 1024;
    const cvDiff = document.createElement('canvas');
    cvDiff.width = size;
    cvDiff.height = size;
    const ctx = cvDiff.getContext('2d');

    const cvRough = document.createElement('canvas');
    cvRough.width = size;
    cvRough.height = size;
    const ctxRough = cvRough.getContext('2d');

    ctx.fillStyle = '#181e2b';
    ctx.fillRect(0, 0, size, size);

    ctxRough.fillStyle = '#505050';
    ctxRough.fillRect(0, 0, size, size);

    const plankW = 128;
    const plankH = 512;

    for (let x = 0; x < size; x += plankW) {
      for (let y = 0; y < size; y += plankH) {
        const offset = ((x / plankW) % 2) * 160;
        const py = (y + offset) % size;

        const shade = Math.floor(Math.random() * 14) - 7;
        ctx.fillStyle = `rgb(${24 + shade},${30 + shade},${42 + shade})`;
        ctx.fillRect(x + 2, py + 2, plankW - 4, plankH - 4);

        ctx.fillStyle = 'rgba(255,255,255,0.03)';
        for (let i = 0; i < 20; i++) {
          const gy = py + Math.random() * (plankH - 4);
          ctx.fillRect(x + 2, gy, plankW - 4, 1.5);
        }

        const roughVal = Math.floor(55 + Math.random() * 20);
        ctxRough.fillStyle = `rgb(${roughVal},${roughVal},${roughVal})`;
        ctxRough.fillRect(x + 2, py + 2, plankW - 4, plankH - 4);

        ctx.fillStyle = '#090c12';
        ctx.fillRect(x, py, plankW, 2);
        ctx.fillRect(x, py, 2, plankH);

        ctxRough.fillStyle = '#b0b0b0';
        ctxRough.fillRect(x, py, plankW, 2);
        ctxRough.fillRect(x, py, 2, plankH);
      }
    }

    const diffTex = new THREE.CanvasTexture(cvDiff);
    diffTex.wrapS = THREE.RepeatWrapping;
    diffTex.wrapT = THREE.RepeatWrapping;
    diffTex.repeat.set(4, 4);

    const roughTex = new THREE.CanvasTexture(cvRough);
    roughTex.wrapS = THREE.RepeatWrapping;
    roughTex.wrapT = THREE.RepeatWrapping;
    roughTex.repeat.set(4, 4);

    return { diffTex, roughTex };
  }

  function generateFabricTexture() {
    const cv = document.createElement('canvas');
    cv.width = 512;
    cv.height = 512;
    const ctx = cv.getContext('2d');

    ctx.fillStyle = '#222c3c';
    ctx.fillRect(0, 0, 512, 512);

    ctx.fillStyle = 'rgba(255,255,255,0.04)';
    for (let x = 0; x < 512; x += 4) {
      ctx.fillRect(x, 0, 1.5, 512);
    }
    for (let y = 0; y < 512; y += 4) {
      ctx.fillRect(0, y, 512, 1.5);
    }

    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(6, 6);
    return tex;
  }

  function generateOakTexture() {
    const cv = document.createElement('canvas');
    cv.width = 256;
    cv.height = 1024;
    const ctx = cv.getContext('2d');

    ctx.fillStyle = '#946a44';
    ctx.fillRect(0, 0, 256, 1024);

    for (let i = 0; i < 90; i++) {
      const y = Math.random() * 1024;
      const h = 2 + Math.random() * 6;
      ctx.fillStyle = Math.random() > 0.5 ? 'rgba(60, 38, 20, 0.20)' : 'rgba(215, 175, 130, 0.14)';
      ctx.fillRect(0, y, 256, h);
    }

    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(1, 3);
    return tex;
  }

  function createContactShadow(width, length, opacity = 0.55) {
    const cv = document.createElement('canvas');
    cv.width = 256;
    cv.height = 256;
    const ctx = cv.getContext('2d');

    const rad = ctx.createRadialGradient(128, 128, 20, 128, 128, 128);
    rad.addColorStop(0, `rgba(4, 6, 10, ${opacity})`);
    rad.addColorStop(0.5, `rgba(4, 6, 10, ${opacity * 0.4})`);
    rad.addColorStop(1, 'transparent');
    ctx.fillStyle = rad;
    ctx.fillRect(0, 0, 256, 256);

    const tex = new THREE.CanvasTexture(cv);
    const geo = new THREE.PlaneGeometry(width, length);
    const mat = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      depthWrite: false
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = 0.003;
    return mesh;
  }

  // =========================================================================
  // 3. CONSTRUCCIÓN DETALLADA DE LA SALA

  function init() {
    container = document.getElementById('room-3d-container');
    canvas = document.getElementById('room-3d-canvas');
    if (!container || !canvas || typeof THREE === 'undefined') return;

    clock = new THREE.Clock();
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 420;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d1016);
    scene.fog = new THREE.FogExp2(0x0d1016, 0.035);

    camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 40);
    camera.position.set(2.6, 1.75, 1.8);

    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;

    try {
      envMap = generateStudioEnvMap(renderer);
      scene.environment = envMap;
    } catch (e) {
      console.warn('PMREM Environment fallback:', e);
    }

    controls = new THREE.OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI / 2 + 0.01;
    controls.minDistance = 0.8;
    controls.maxDistance = 7.5;
    controls.target.set(0, 0.82, -0.5);

    setupLighting();

    const textures = {
      parquet: generateParquetTextures(),
      fabric: generateFabricTexture(),
      oak: generateOakTexture()
    };

    buildEnclosedArchitecturalRoom(textures);
    buildRoundedCredenza();
    buildTelevisionLGOLEDGrounded();
    buildYamahaReceiverAVR();
    buildQ3020iSpeakersRounded();
    buildListeningSeatingAndRug(textures);
    buildProMeasurementRig();
    buildMeasurementClusterWide();
    buildAcousticWavefronts();

    setupEvents();
    animate();
  }

  function setupLighting() {
    const amb = new THREE.AmbientLight(0x283244, 1.3);
    scene.add(amb);

    const key = new THREE.DirectionalLight(0xfffaee, 2.2);
    key.position.set(2.5, 4.8, 2.2);
    key.castShadow = true;
    key.shadow.mapSize.width = 2048;
    key.shadow.mapSize.height = 2048;
    key.shadow.bias = -0.0003;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 12;
    key.shadow.camera.left = -3.2;
    key.shadow.camera.right = 3.2;
    key.shadow.camera.top = 3.2;
    key.shadow.camera.bottom = -3.2;
    scene.add(key);

    const coveLight = new THREE.PointLight(0xffcaa0, 3.6, 6.0, 1.4);

    const spotMic = new THREE.SpotLight(0xffeedb, 2.0, 5.0, Math.PI / 6, 0.4);
    spotMic.position.set(0, 3.2, 0.5);
    spotMic.target.position.set(0, 1.0, 0.5);
    scene.add(spotMic);
    scene.add(spotMic.target);

    const rim = new THREE.DirectionalLight(0x94b8e8, 0.65);
    rim.position.set(-3.2, 2.6, -1.6);
    scene.add(rim);
  }

  function buildEnclosedArchitecturalRoom(textures) {
    // Suelo de parquet noble
    const floorGeo = new THREE.PlaneGeometry(5.4, 6.2);
    const floorMat = new THREE.MeshStandardMaterial({
      map: textures.parquet.diffTex,
      roughnessMap: textures.parquet.roughTex,
      roughness: 0.32,
      metalness: 0.12
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0;
    floor.receiveShadow = true;
    scene.add(floor);

    // Techo arquitectónico con focos
    const ceilingGeo = new THREE.PlaneGeometry(5.4, 6.2);
    const ceilingMat = new THREE.MeshStandardMaterial({ color: 0x161c26, roughness: 0.85, side: THREE.BackSide });
    const ceiling = new THREE.Mesh(ceilingGeo, ceilingMat);
    ceiling.rotation.x = Math.PI / 2;
    ceiling.position.y = 3.2;
    scene.add(ceiling);

    const spotTrimMat = new THREE.MeshStandardMaterial({ color: 0x242e3e, metalness: 0.8, roughness: 0.2 });
    const spotGlassMat = new THREE.MeshBasicMaterial({ color: 0xffedd5 });
    [[-0.8, -1.2], [0.8, -1.2], [0, 0.5]].forEach(([sx, sz]) => {
      const trim = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.006, 16, 24), spotTrimMat);
      trim.rotation.x = Math.PI / 2;
      trim.position.set(sx, 3.195, sz);
      scene.add(trim);

      const glass = new THREE.Mesh(new THREE.CircleGeometry(0.038, 24), spotGlassMat);
      glass.rotation.x = Math.PI / 2;
      glass.position.set(sx, 3.193, sz);
      scene.add(glass);
    });

    // Pared trasera acústica
    const wallGeo = new THREE.PlaneGeometry(5.4, 3.4);
    const wallMat = new THREE.MeshStandardMaterial({ color: 0x090c12, roughness: 0.95 });
    const frontWall = new THREE.Mesh(wallGeo, wallMat);
    frontWall.position.set(0, 1.6, -2.28);
    frontWall.receiveShadow = true;
    scene.add(frontWall);

    // Palillería acústica semicilíndrica suave (Curved Slats)
    const slatGroup = new THREE.Group();
    const slatMat = new THREE.MeshStandardMaterial({
      map: textures.oak,
      roughness: 0.48,
      metalness: 0.04
    });
    for (let x = -2.35; x <= 2.35; x += 0.092) {
      // Semicilindro suave en lugar de prisma recto
      const slat = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 2.95, 16, 1, false, 0, Math.PI), slatMat);
      slat.position.set(x, 1.48, -2.26);
      slat.rotation.y = -Math.PI / 2;
      slat.castShadow = true;
      slat.receiveShadow = true;
      slatGroup.add(slat);
    }
    scene.add(slatGroup);

    // Pared lateral izquierda acústica
    const leftWallGeo = new THREE.PlaneGeometry(6.2, 3.4);
    const leftWallMat = new THREE.MeshStandardMaterial({ color: 0x10141e, roughness: 0.9 });
    const leftWall = new THREE.Mesh(leftWallGeo, leftWallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-2.7, 1.6, 0.8);
    leftWall.receiveShadow = true;
    scene.add(leftWall);

    // Cuadro difusor acústico orgánico de diseño
    const frameGeo = createRoundedBoxGeometry(0.04, 1.25, 1.65, 0.03, 6);
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x32241b, roughness: 0.4 });
    const frame = new THREE.Mesh(frameGeo, frameMat);
    frame.position.set(-2.67, 1.5, -0.6);
    scene.add(frame);
  }

  function buildRoundedCredenza() {
    const credGroup = new THREE.Group();

    // Sombra de contacto suave
    scene.add(createContactShadow(2.4, 0.8, 0.65));

    // Mueble aparador con cantos completamente redondeados (Curved Tambour Silhouette)
    const credMat = new THREE.MeshStandardMaterial({
      color: 0x34251c,
      roughness: 0.38,
      metalness: 0.06
    });
    const credGeo = createRoundedBoxGeometry(2.1, 0.38, 0.46, 0.045, 8);
    const credenza = new THREE.Mesh(credGeo, credMat);
    credenza.position.set(0, 0.24, -1.82);
    credenza.castShadow = true;
    credenza.receiveShadow = true;
    credGroup.add(credenza);

    // Patas cónicas redondeadas de latón dorado
    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      metalness: 0.9,
      roughness: 0.22
    });
    [-0.92, 0.92].forEach(lx => {
      [-0.18, 0.18].forEach(lz => {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.007, 0.09, 16), brassMat);
        leg.position.set(lx, 0.045, -1.82 + lz);
        leg.castShadow = true;
        credGroup.add(leg);
      });
    });

    scene.add(credGroup);
  }

  function buildTelevisionLGOLEDGrounded() {
    const tvGroup = new THREE.Group();

    // Superficie del aparador está en y = 0.24 + (0.38 / 2) = 0.43 m
    const CREDENZA_TOP_Y = 0.43;

    // -----------------------------------------------------------------
    // PEANA ALPINE ORIGINAL DE LA LG C5 APOYADA DIRECTAMENTE SOBRE EL MUEBLE
    // Base ancha de titanio cepillado que descansa plana sobre el aparador
    // -----------------------------------------------------------------
    const standMat = new THREE.MeshStandardMaterial({
      color: 0x1a202c,
      metalness: 0.94,
      roughness: 0.12
    });

    // Placa base plana de titanio (60 cm ancho x 22 cm fondo x 1.2 cm grosor)
    const standBaseGeo = createRoundedBoxGeometry(0.60, 0.012, 0.22, 0.005, 4);
    const standBase = new THREE.Mesh(standBaseGeo, standMat);
    standBase.position.set(0, CREDENZA_TOP_Y + 0.006, -1.80);
    standBase.castShadow = true;
    tvGroup.add(standBase);

    // Mástil de soporte curvo ascendente que conecta la base al panel
    const neckGeo = createRoundedBoxGeometry(0.18, 0.08, 0.06, 0.015, 6);
    const neck = new THREE.Mesh(neckGeo, standMat);
    neck.position.set(0, CREDENZA_TOP_Y + 0.045, -1.82);
    tvGroup.add(neck);

    // -----------------------------------------------------------------
    // PANEL OLED ULTRAFINO LG C5 (65")
    // Comienza a solo 5 cm por encima del mueble (apoyado firmemente)
    // Centro del panel: y = CREDENZA_TOP_Y + 0.05 + (0.84 / 2) = 0.90 m
    // -----------------------------------------------------------------
    const TV_CENTER_Y = CREDENZA_TOP_Y + 0.05 + 0.42; // 0.90m
    const TV_Z = -1.82;

    const bezelGeo = createRoundedBoxGeometry(1.46, 0.84, 0.012, 0.008, 6);
    const bezel = new THREE.Mesh(bezelGeo, standMat);
    bezel.position.set(0, TV_CENTER_Y, TV_Z);
    bezel.castShadow = true;
    tvGroup.add(bezel);

    // Carcasa trasera curva inferior de electrónica OLED
    const rearHousingGeo = createRoundedBoxGeometry(0.92, 0.44, 0.035, 0.02, 6);
    const rearHousing = new THREE.Mesh(rearHousingGeo, standMat);
    rearHousing.position.set(0, TV_CENTER_Y - 0.15, TV_Z - 0.022);
    tvGroup.add(rearHousing);

    // Pantalla de cristal OLED brillante con interfaz HDR activa
    const screenGeo = new THREE.PlaneGeometry(1.44, 0.82);
    const cv = document.createElement('canvas');
    cv.width = 1024;
    cv.height = 576;
    const ctx = cv.getContext('2d');

    const grad = ctx.createLinearGradient(0, 0, 1024, 576);
    grad.addColorStop(0, '#03050a');
    grad.addColorStop(0.5, '#0a1220');
    grad.addColorStop(1, '#04070e');
    ctx.fillStyle = grad;
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 22px "Inter", sans-serif';
    ctx.fillText('LG OLED C5 · Filmmaker Mode 4K', 44, 54);

    ctx.fillStyle = '#38bdf8';
    ctx.font = '16px "JetBrains Mono", monospace';
    ctx.fillText('HDMI 2 (eARC/ARC) ➔ YAMAHA RX-V673 · Bitstream Passthrough (Raw)', 44, 86);

    // Curva de respuesta acústica en pantalla
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    for (let x = 44; x < 980; x += 8) {
      const y = 350 + Math.sin(x * 0.02) * 38 + Math.cos(x * 0.045) * 20;
      if (x === 44) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.lineTo(980, 500);
    ctx.lineTo(44, 500);
    ctx.closePath();
    ctx.fillStyle = 'rgba(56, 189, 248, 0.08)';
    ctx.fill();

    // 31 bandas de ecualización ámbar cálido
    for (let i = 0; i < 31; i++) {
      const bx = 44 + i * 30;
      const bh = 30 + Math.abs(Math.sin(i * 0.35 + 1.2)) * 90;
      ctx.fillStyle = 'rgba(245, 158, 11, 0.85)';
      ctx.fillRect(bx, 480 - bh, 18, bh);
    }

    const screenTexture = new THREE.CanvasTexture(cv);
    if (renderer && renderer.capabilities) {
      screenTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    }
    const screenMat = new THREE.MeshStandardMaterial({
      map: screenTexture,
      roughness: 0.08,
      metalness: 0.15
    });
    const screen = new THREE.Mesh(screenGeo, screenMat);
    screen.position.set(0, TV_CENTER_Y, TV_Z + 0.007);
    tvGroup.add(screen);

    scene.add(tvGroup);
  }

  function buildYamahaReceiverAVR() {
    const rxGroup = new THREE.Group();

    // Chasis de aluminio cepillado con cantos biselados redondeados
    const chMat = new THREE.MeshStandardMaterial({
      color: 0x141822,
      roughness: 0.32,
      metalness: 0.85
    });
    const chGeo = createRoundedBoxGeometry(0.435, 0.171, 0.34, 0.015, 6);
    const chassis = new THREE.Mesh(chGeo, chMat);
    chassis.castShadow = true;
    rxGroup.add(chassis);

    // Ventana VFD tintada
    const vfdCv = document.createElement('canvas');
    vfdCv.width = 256;
    vfdCv.height = 64;
    const vfdCtx = vfdCv.getContext('2d');
    vfdCtx.fillStyle = '#06080e';
    vfdCtx.fillRect(0, 0, 256, 64);
    vfdCtx.fillStyle = '#f59e0b';
    vfdCtx.font = 'bold 22px monospace';
    vfdCtx.fillText('RX-V673 STRAIGHT', 14, 28);
    vfdCtx.font = '18px monospace';
    vfdCtx.fillText('PEQ: MANUAL -20dB', 14, 52);

    const vfdTex = new THREE.CanvasTexture(vfdCv);
    const vfdMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.24, 0.058),
      new THREE.MeshBasicMaterial({ map: vfdTex })
    );
    vfdMesh.position.set(0, 0.02, 0.175);
    rxGroup.add(vfdMesh);

    // Diales metálicos
    const dialMat = new THREE.MeshStandardMaterial({ color: 0x2e3644, metalness: 0.92, roughness: 0.18 });
    const volKnob = new THREE.Mesh(new THREE.CylinderGeometry(0.029, 0.029, 0.02, 32), dialMat);
    volKnob.rotation.x = Math.PI / 2;
    volKnob.position.set(0.165, -0.01, 0.178);
    rxGroup.add(volKnob);

    const inputKnob = new THREE.Mesh(new THREE.CylinderGeometry(0.021, 0.021, 0.016, 32), dialMat);
    inputKnob.rotation.x = Math.PI / 2;
    inputKnob.position.set(-0.165, -0.01, 0.176);
    rxGroup.add(inputKnob);

    const led = new THREE.Mesh(
      new THREE.SphereGeometry(0.003, 12, 12),
      new THREE.MeshBasicMaterial({ color: 0x22c55e })
    );
    led.position.set(-0.19, -0.055, 0.176);
    rxGroup.add(led);

    // Apoyado elegantemente a la derecha en la superficie del aparador
    rxGroup.position.set(0.62, 0.515, -1.82);
    scene.add(rxGroup);
  }

  function buildSingleSpeakerRounded(isLeft) {
    const spkGroup = new THREE.Group();
    const xPos = isLeft ? -1.15 : 1.15;
    const toeInAngle = isLeft ? 0.26 : -0.26; // 15 grados exactos hacia el oyente

    // Sombra de contacto
    const spkShadow = createContactShadow(0.42, 0.42, 0.55);
    spkShadow.position.set(xPos, 0.003, -1.75);
    scene.add(spkShadow);

    // Base del soporte con esquinas redondeadas
    const standMat = new THREE.MeshStandardMaterial({ color: 0x121620, roughness: 0.38, metalness: 0.88 });
    const basePlateGeo = createRoundedBoxGeometry(0.28, 0.025, 0.32, 0.02, 6);
    const basePlate = new THREE.Mesh(basePlateGeo, standMat);
    basePlate.position.set(0, 0.012, 0);
    basePlate.castShadow = true;
    spkGroup.add(basePlate);

    // Doble columna tubular
    [-0.04, 0.04].forEach(colX => {
      const col = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.024, 0.65, 24), standMat);
      col.position.set(colX, 0.35, 0);
      col.castShadow = true;
      spkGroup.add(col);
    });

    const topPlateGeo = createRoundedBoxGeometry(0.18, 0.015, 0.24, 0.015, 6);
    const topPlate = new THREE.Mesh(topPlateGeo, standMat);
    topPlate.position.set(0, 0.68, 0);
    spkGroup.add(topPlate);

    // -----------------------------------------------------------------
    // RECINTO Q ACOUSTICS 3020i (170 x 278 x 282 mm)
    // Curvas orgánicas fluidas en esquinas frontales y laterales (R=25mm)
    // -----------------------------------------------------------------
    const cabMat = new THREE.MeshStandardMaterial({
      color: 0x1e2430, // Grafito satinado suave
      roughness: 0.25,
      metalness: 0.12
    });
    const cabGeo = createRoundedBoxGeometry(0.17, 0.278, 0.282, 0.025, 8);
    const cabMesh = new THREE.Mesh(cabGeo, cabMat);
    cabMesh.position.set(0, 0.83, 0);
    cabMesh.castShadow = true;
    cabMesh.receiveShadow = true;
    spkGroup.add(cabMesh);

    // Puerto Bass-Reflex trasero
    const portMat = new THREE.MeshBasicMaterial({ color: 0x05070a });
    const port = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.024, 0.02, 24), portMat);
    port.rotation.x = Math.PI / 2;
    port.position.set(0, 0.88, -0.141);
    spkGroup.add(port);

    // Aros de aluminio pulido cromado
    const chromeMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      metalness: 0.98,
      roughness: 0.08
    });
    const coneMat = new THREE.MeshStandardMaterial({ color: 0x0f141c, roughness: 0.65 });

    // Woofer 5"
    const wooferRing = new THREE.Mesh(new THREE.TorusGeometry(0.062, 0.004, 16, 32), chromeMat);
    wooferRing.position.set(0, 0.78, 0.142);
    spkGroup.add(wooferRing);
    // Tweeter 22 mm desacoplado a 0.91m de oído
    const tweeterRing = new THREE.Mesh(new THREE.TorusGeometry(0.024, 0.003, 16, 32), chromeMat);
    tweeterRing.position.set(0, 0.91, 0.142);
    spkGroup.add(tweeterRing);

    const tweeterDome = new THREE.Mesh(
      new THREE.SphereGeometry(0.014, 18, 18),
      new THREE.MeshStandardMaterial({ color: 0x242c38, roughness: 0.25 })
    );
    tweeterDome.position.set(0, 0.91, 0.144);
    spkGroup.add(tweeterDome);

    spkGroup.position.set(xPos, 0, -1.75);
    spkGroup.rotation.y = toeInAngle;
    scene.add(spkGroup);
  }

  function buildQ3020iSpeakersRounded() {
    buildSingleSpeakerRounded(true);
    buildSingleSpeakerRounded(false);
  }

  function buildListeningSeatingAndRug(textures) {
    scene.add(createContactShadow(3.2, 3.2, 0.5));

    // Alfombra con esquinas redondeadas
    const rugGeo = createRoundedBoxGeometry(3.2, 0.012, 3.2, 0.12, 6);
    const rugMat = new THREE.MeshStandardMaterial({
      map: textures.fabric,
      color: 0x2c3748,
      roughness: 0.95,
      metalness: 0.02
    });
    const rug = new THREE.Mesh(rugGeo, rugMat);
    rug.position.set(0, 0.006, -0.3);
    rug.receiveShadow = true;
    scene.add(rug);

    // -----------------------------------------------------------------
    // BUTACA ESCANDINAVA ORGÁNICA (Curved Lounge Chair)
    // Cojines con curvatura anatómica suave
    // -----------------------------------------------------------------
    const chairGroup = new THREE.Group();
    const fabricMat = new THREE.MeshStandardMaterial({
      map: textures.fabric,
      color: 0x242e3e,
      roughness: 0.85,
      metalness: 0.05
    });
    const woodMat = new THREE.MeshStandardMaterial({ color: 0x36271e, roughness: 0.45 });

    // Cojín de asiento con bordes orgánicos redondeados
    const seatGeo = createRoundedBoxGeometry(0.78, 0.16, 0.74, 0.07, 8);
    const seat = new THREE.Mesh(seatGeo, fabricMat);
    seat.position.set(0, 0.38, 0.92);
    seat.castShadow = true;
    chairGroup.add(seat);

    // Respaldo curvado anatómico
    const backGeo = createRoundedBoxGeometry(0.74, 0.62, 0.14, 0.06, 8);
    const back = new THREE.Mesh(backGeo, fabricMat);
    back.position.set(0, 0.74, 1.24);
    back.rotation.x = -0.16;
    back.castShadow = true;
    chairGroup.add(back);

    // Reposacabezas acolchado
    const headrestGeo = createRoundedBoxGeometry(0.56, 0.24, 0.12, 0.05, 8);
    const headrest = new THREE.Mesh(headrestGeo, fabricMat);
    headrest.position.set(0, 1.06, 1.30);
    headrest.rotation.x = -0.16;
    headrest.castShadow = true;
    chairGroup.add(headrest);

    // Cojín lumbar redondeado
    const pillowGeo = createRoundedBoxGeometry(0.48, 0.22, 0.1, 0.04, 8);
    const pillow = new THREE.Mesh(pillowGeo, new THREE.MeshStandardMaterial({ color: 0x38485e, roughness: 0.9 }));
    pillow.position.set(0, 0.52, 1.14);
    chairGroup.add(pillow);

    // Patas cónicas de madera
    [-0.34, 0.34].forEach(lx => {
      [-0.28, 0.28].forEach(lz => {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.01, 0.38, 16), woodMat);
        leg.position.set(lx, 0.19, 0.92 + lz);
        leg.rotation.z = lx > 0 ? -0.1 : 0.1;
        leg.castShadow = true;
        chairGroup.add(leg);
      });
    });

    scene.add(chairGroup);
  }

  function buildProMeasurementRig() {
    const rigGroup = new THREE.Group();

    const tripodMat = new THREE.MeshStandardMaterial({
      color: 0x10131a,
      metalness: 0.9,
      roughness: 0.25
    });
    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      metalness: 0.92,
      roughness: 0.18
    });

    // 3 Patas de trípode
    for (let i = 0; i < 3; i++) {
      const angle = (i * Math.PI * 2) / 3;
      const legGeo = new THREE.CylinderGeometry(0.007, 0.005, 0.75, 16);
      const leg = new THREE.Mesh(legGeo, tripodMat);
      leg.position.set(Math.cos(angle) * 0.18, 0.32, 0.5 + Math.sin(angle) * 0.18);
      leg.rotation.z = Math.cos(angle) * 0.42;
      leg.rotation.x = -Math.sin(angle) * 0.42;
      leg.castShadow = true;
      rigGroup.add(leg);
    }

    // Columna telescópica
    const column = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.011, 0.65, 20), tripodMat);
    column.position.set(0, 0.68, 0.5);
    column.castShadow = true;
    rigGroup.add(column);

    const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.035, 20), brassMat);
    collar.position.set(0, 0.88, 0.5);
    rigGroup.add(collar);

    const mount = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.04, 16), tripodMat);
    mount.position.set(0, 0.94, 0.5);
    rigGroup.add(mount);

    // Micrófono calibrado UMIK-1 a 90°
    const micBodyMat = new THREE.MeshStandardMaterial({ color: 0xc0c8d4, metalness: 0.95, roughness: 0.15 });
    const micBody = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.11, 24), micBodyMat);
    micBody.position.set(0, 0.97, 0.5);
    micBody.castShadow = true;
    rigGroup.add(micBody);

    const micTip = new THREE.Mesh(
      new THREE.CylinderGeometry(0.0035, 0.005, 0.025, 20),
      new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.95, roughness: 0.1 })
    );
    micTip.position.set(0, 1.01, 0.5);
    rigGroup.add(micTip);

    scene.add(rigGroup);
  }

  function buildMeasurementClusterWide() {
    pointsGroup = new THREE.Group();

    // Líneas láser de referencia espacial amplia (40 cm de radio)
    const laserMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.35
    });

    // Barra lateral de 80 cm (P2 a P3)
    const barX = new THREE.Mesh(new THREE.CylinderGeometry(0.0018, 0.0018, 0.80, 12), laserMat);
    barX.rotation.z = Math.PI / 2;
    barX.position.set(0, 1.0, 0.5);
    pointsGroup.add(barX);

    // Barra longitudinal de 70 cm (P4 a P5)
    const barZ = new THREE.Mesh(new THREE.CylinderGeometry(0.0018, 0.0018, 0.70, 12), laserMat);
    barZ.rotation.x = Math.PI / 2;
    barZ.position.set(0, 1.0, 0.5);
    pointsGroup.add(barZ);

    // 5 Esferas gema pulidas bien separadas
    for (let id = 1; id <= 5; id++) {
      const cfg = CLUSTER_POINTS[id];
      const isCenter = (id === 1);
      const radius = isCenter ? 0.034 : 0.028;

      const sphMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.color,
        emissiveIntensity: isCenter ? 0.8 : 0.4,
        roughness: 0.12,
        metalness: 0.75
      });
      const sph = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 32), sphMat);
      sph.position.set(cfg.x, cfg.y, cfg.z);
      sph.userData = { pointId: id, config: cfg };
      pointsGroup.add(sph);
      pointMeshes[id] = sph;

      const ringGeo = new THREE.RingGeometry(radius + 0.008, radius + 0.014, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: cfg.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: isCenter ? 0.85 : 0.0
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.set(cfg.x, cfg.y - 0.002, cfg.z);
      pointsGroup.add(ring);
      pointRings[id] = ring;

      const numBadge = createNumberBadge(cfg.num, cfg.hex);
      numBadge.position.set(cfg.x, cfg.y + radius + 0.038, cfg.z);
      pointsGroup.add(numBadge);
      pointNumberSprites[id] = numBadge;
    }

    updateActiveTag();
    scene.add(pointsGroup);
  }

  function buildAcousticWavefronts() {
    acousticWaveGroup = new THREE.Group();

    [-1.15, 1.15].forEach((spkX, idx) => {
      const isLeft = (idx === 0);
      const toeIn = isLeft ? 0.26 : -0.26;

      for (let w = 1; w <= 4; w++) {
        const ringGeo = new THREE.RingGeometry(0.12 * w, 0.12 * w + 0.014, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.12 / w,
          side: THREE.DoubleSide
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        const initDist = 0.45 * w;
        ring.position.set(
          spkX + Math.sin(toeIn) * initDist,
          0.91,
          -1.75 + Math.cos(toeIn) * initDist
        );
        ring.rotation.y = toeIn;
        ring.userData = {
          originX: spkX,
          originZ: -1.75,
          toeIn: toeIn,
          dist: initDist,
          maxDist: 2.3
        };
        acousticWaveGroup.add(ring);
      }
    });

    scene.add(acousticWaveGroup);
  }

  function createNumberBadge(numStr, colorHex) {
    const cv = document.createElement('canvas');
    cv.width = 64;
    cv.height = 64;
    const ctx = cv.getContext('2d');

    ctx.fillStyle = 'rgba(10, 14, 22, 0.92)';
    ctx.beginPath();
    ctx.arc(32, 32, 28, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 3.5;
    ctx.stroke();

    ctx.font = 'bold 30px "Inter", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(numStr, 32, 33);

    const texture = new THREE.CanvasTexture(cv);
    texture.minFilter = THREE.LinearFilter;
    const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(0.08, 0.08, 1);
    return sprite;
  }

  function createActivePointTag(cfg, isDone) {
    const cv = document.createElement('canvas');
    cv.width = 340;
    cv.height = 84;
    const ctx = cv.getContext('2d');

    ctx.fillStyle = 'rgba(8, 12, 20, 0.95)';
    ctx.beginPath();
    ctx.roundRect(8, 8, 324, 68, 12);
    ctx.fill();

    ctx.strokeStyle = isDone ? '#22c55e' : cfg.hex;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    ctx.fillStyle = isDone ? '#22c55e' : cfg.hex;
    ctx.beginPath();
    ctx.arc(34, 42, 7, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = 'bold 20px "Inter", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${cfg.label} ${isDone ? '✓ (Medido)' : ''}`, 54, 32);

    ctx.font = '14px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(cfg.offset, 54, 54);

    const texture = new THREE.CanvasTexture(cv);
    texture.minFilter = THREE.LinearFilter;
    const mat = new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(0.42, 0.105, 1);
    return sprite;
  }

  function updateActiveTag() {
    if (activeTagSprite) {
      pointsGroup.remove(activeTagSprite);
      activeTagSprite.geometry.dispose();
      activeTagSprite.material.dispose();
      activeTagSprite = null;
    }

    const cfg = CLUSTER_POINTS[activePointId];
    if (!cfg) return;

    const isDone = Boolean(pointsStatus[activePointId]);
    activeTagSprite = createActivePointTag(cfg, isDone);
    activeTagSprite.position.set(cfg.x, cfg.y + 0.16, cfg.z);
    pointsGroup.add(activeTagSprite);
  }

  function setupEvents() {
    canvas.addEventListener('pointerup', onPointerUp, false);
    canvas.addEventListener('pointermove', onPointerMove, false);

    const ro = new ResizeObserver(() => resize());
    ro.observe(container);

    const btnIso = document.getElementById('cam-preset-iso');
    if (btnIso) btnIso.onclick = () => setViewPreset('iso');

    const btnTop = document.getElementById('cam-preset-top');
    if (btnTop) btnTop.onclick = () => setViewPreset('top');

    const btnSweet = document.getElementById('cam-preset-sweet');
    if (btnSweet) btnSweet.onclick = () => setViewPreset('sweet');

    const btnFront = document.getElementById('cam-preset-front');
    if (btnFront) btnFront.onclick = () => setViewPreset('front');

    const btnToggle3D = document.getElementById('btn-toggle-3d');
    const btnToggle2D = document.getElementById('btn-toggle-2d');
    const room3D = document.getElementById('room-3d-container');
    const room2D = document.getElementById('room-2d-container');

    if (btnToggle3D && btnToggle2D && room3D && room2D) {
      btnToggle3D.onclick = () => {
        btnToggle3D.classList.add('active');
        btnToggle2D.classList.remove('active');
        room3D.style.display = 'block';
        room2D.style.display = 'none';
        resize();
      };
      btnToggle2D.onclick = () => {
        btnToggle2D.classList.add('active');
        btnToggle3D.classList.remove('active');
        room3D.style.display = 'none';
        room2D.style.display = 'block';
      };
    }
  }

  function getPointerPos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * 2 - 1,
      y: -((e.clientY - rect.top) / rect.height) * 2 + 1
    };
  }

  function onPointerMove(e) {
    const pos = getPointerPos(e);
    mouse.x = pos.x;
    mouse.y = pos.y;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Object.values(pointMeshes));

    const infoBox = document.getElementById('room-3d-point-info');
    const infoTitle = document.getElementById('room-3d-info-title');
    const infoCoords = document.getElementById('room-3d-info-coords');

    if (intersects.length > 0) {
      canvas.style.cursor = 'pointer';
      const ptId = intersects[0].object.userData.pointId;
      const cfg = CLUSTER_POINTS[ptId];
      const isDone = pointsStatus[ptId];

      if (infoBox && infoTitle && infoCoords) {
        infoBox.style.display = 'block';
        infoTitle.textContent = `${cfg.name} ${isDone ? '✓ (Medido)' : '(Pendiente)'}`;
        infoTitle.style.color = isDone ? '#22c55e' : cfg.hex;
        infoCoords.textContent = `${cfg.offset} · [x: ${(cfg.x * 100).toFixed(0)}cm, y: ${(cfg.y * 100).toFixed(0)}cm, z: ${(cfg.z * 100).toFixed(0)}cm]`;
      }
    } else {
      canvas.style.cursor = 'default';
      if (infoBox) infoBox.style.display = 'none';
    }
  }

  function onPointerUp(e) {
    const pos = getPointerPos(e);
    mouse.x = pos.x;
    mouse.y = pos.y;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Object.values(pointMeshes));

    if (intersects.length > 0) {
      const ptId = intersects[0].object.userData.pointId;
      selectPoint(ptId);
    }
  }

  function selectPoint(ptId) {
    activePointId = ptId;
    updateActivePointDisplay();
    updateActiveTag();

    const ptEl = document.querySelector(`.point[data-point="${ptId}"]`);
    if (ptEl) ptEl.click();
    const roomPtEl = document.querySelector(`.room-diagram .pt[data-room-pt="${ptId}"]`);
    if (roomPtEl) roomPtEl.click();
  }

  function setViewPreset(preset) {
    if (preset === 'iso') {
      targetCamPos = new THREE.Vector3(2.6, 1.75, 1.8);
      targetControlsTarget = new THREE.Vector3(0, 0.82, -0.5);
    } else if (preset === 'top') {
      targetCamPos = new THREE.Vector3(0, 4.4, -0.4);
      targetControlsTarget = new THREE.Vector3(0, 0.5, -0.4);
    } else if (preset === 'sweet') {
      targetCamPos = new THREE.Vector3(0, 1.18, 1.35);
      targetControlsTarget = new THREE.Vector3(0, 0.90, -1.80);
    } else if (preset === 'front') {
      targetCamPos = new THREE.Vector3(0, 1.35, -2.5);
      targetControlsTarget = new THREE.Vector3(0, 0.95, 0.5);
    }
  }

  function resize() {
    if (!container || !renderer || !camera) return;
    const width = container.clientWidth;
    const height = container.clientHeight;
    if (width === 0 || height === 0) return;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  function updatePoints(statusObj, activeId) {
    if (statusObj) pointsStatus = Object.assign({}, statusObj);
    if (activeId !== undefined) activePointId = activeId;
    updateActivePointDisplay();
    updateActiveTag();
  }

  function updateActivePointDisplay() {
    for (let id = 1; id <= 5; id++) {
      const sph = pointMeshes[id];
      const ring = pointRings[id];
      const cfg = CLUSTER_POINTS[id];
      const isDone = Boolean(pointsStatus[id]);
      const isActive = (id === activePointId);

      if (sph) {
        if (isDone) {
          sph.material.color.setHex(0x22c55e);
          sph.material.emissive.setHex(0x16a34a);
          sph.material.emissiveIntensity = 0.85;
        } else {
          sph.material.color.setHex(cfg.color);
          sph.material.emissive.setHex(cfg.color);
          sph.material.emissiveIntensity = isActive ? 0.85 : 0.4;
        }
      }

      if (ring) {
        ring.material.opacity = isActive ? 0.85 : (isDone ? 0.4 : 0.0);
        if (isDone) ring.material.color.setHex(0x22c55e);
        else ring.material.color.setHex(cfg.color);
      }
    }
  }

  function animate() {
    animId = requestAnimationFrame(animate);

    const time = clock.getElapsedTime();

    if (targetCamPos && targetControlsTarget) {
      camera.position.lerp(targetCamPos, 0.08);
      controls.target.lerp(targetControlsTarget, 0.08);
      if (camera.position.distanceTo(targetCamPos) < 0.02) {
        targetCamPos = null;
        targetControlsTarget = null;
      }
    }

    controls.update();

    if (pointRings[activePointId]) {
      const s = 1.0 + Math.sin(time * 3.5) * 0.12;
      pointRings[activePointId].scale.set(s, s, 1);
    }

    if (acousticWaveGroup) {
      acousticWaveGroup.children.forEach(w => {
        w.userData.dist += 0.0045;
        if (w.userData.dist > w.userData.maxDist) {
          w.userData.dist = 0.25;
        }
        w.position.x = w.userData.originX + Math.sin(w.userData.toeIn) * w.userData.dist;
        w.position.z = w.userData.originZ + Math.cos(w.userData.toeIn) * w.userData.dist;
        const progress = (w.userData.dist - 0.25) / (w.userData.maxDist - 0.25);
        w.material.opacity = Math.sin(progress * Math.PI) * 0.16;
      });
    }

    renderer.render(scene, camera);
  }

  window.Room3D = {
    init,
    resize,
    updatePoints,
    setViewPreset,
    selectPoint
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    setTimeout(init, 50);
  }
})();
