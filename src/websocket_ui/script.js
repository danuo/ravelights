import * as THREE from "three";

let scene, camera, renderer;

function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}

function linspace(start, end, num) {
  const step = (end - start) / (num - 1);
  const result = [];
  for (let i = 0; i < num; i++) {
    result.push(start + i * step);
  }
  return result;
}

function sum(array) {
  let sum = 0;
  for (let i = 0; i < array.length; i++) {
    sum += array[i];
  }
  return sum;
}

function initTexture(data, SIZE) {
  const texture = new THREE.DataTexture(data, 1, SIZE, THREE.RGBAFormat);
  texture.needsUpdate = true;
  return texture;
}

function initWebGL(NLEDS, NLIGHTS, SIZE, texture) {
  console.log(NLEDS);
  console.log(NLIGHTS);
  console.log(texture);
  const container = document.getElementById("container");
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.Camera();

  // Create two PlaneGeometries
  let spacings = [0];
  let pixelCounter = 0;
  for (let i = 0; i < NLIGHTS; i++) {
    pixelCounter += NLEDS[i];
    spacings.push(pixelCounter / SIZE);
  }

  const planeWidth = (1 / NLIGHTS) * 1.3;
  const planeHeight = 1.8;
  const spread = 1 - planeWidth / 2 - 0.07;
  const positions = linspace(-spread, spread, NLIGHTS);

  for (let i = 0; i < NLIGHTS; i++) {
    let planeGeometry = new THREE.PlaneGeometry(planeWidth, planeHeight, 1, 1);
    let uvAttribute = planeGeometry.getAttribute("uv");
    const xStart = spacings[i];
    const xEnd = spacings[i + 1];

    // flipped with vars
    uvAttribute.setXY(0, 0, xStart);
    uvAttribute.setXY(1, 1, xStart);
    uvAttribute.setXY(2, 0, xEnd);
    uvAttribute.setXY(3, 1, xEnd);

    // planeGeometry.uvsNeedUpdate = true;
    let material = new THREE.MeshBasicMaterial({ map: texture });
    let mesh = new THREE.Mesh(planeGeometry, material);

    mesh.position.x = positions[i];
    scene.add(mesh);
  }

  window.addEventListener("resize", onWindowResize);
  render();
}

function onWindowResize() {
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function render() {
  renderer.render(scene, camera);
}

// websocket
const apiUrl = "/rest/settings";
async function fetchData() {
  const response = await fetch(apiUrl);
  if (response.status === 200) {
    const data = response.json();
    console.log(data);
    return data;
  }
  return null;
}

function deviceConfigToNLEDS(deviceConfig) {
  let n_lights = [];
  deviceConfig.forEach((element) => {
    for (let i = 0; i < element.n_lights; i++) {
      n_lights.push(element.n_leds);
    }
  });
  return n_lights;
}

async function initWebsocket() {
  const apiData = await fetchData();
  const deviceConfig = apiData.device_config;
  const NLEDS = deviceConfigToNLEDS(deviceConfig);
  const NLIGHTS = NLEDS.length;
  const SIZE = sum(NLEDS);
  var data = new Uint8Array(4 * SIZE);
  const texture = initTexture(data, SIZE);
  initWebGL(NLEDS, NLIGHTS, SIZE, texture);
  const socket = io();
  socket.on("message", (in_data) => {
    let array = new Uint8Array(in_data);
    data.set(array);
    texture.needsUpdate = true;
    render();
  });
}

initWebsocket();
