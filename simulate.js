const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { tgNotify } = require("./integration");

function getArg(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || !process.argv[index + 1]) {
    throw new Error(`Нужен аргумент ${name}`);
  }
  return process.argv[index + 1];
}

function getOptionalArg(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || !process.argv[index + 1]) {
    return null;
  }
  return process.argv[index + 1];
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit", shell: true });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function resolveOfferMode() {
  if (hasFlag("--no-offer")) {
    return "manual";
  }
  if (hasFlag("--offer")) {
    return "auto";
  }

  const mode = (process.env.OFFER_MODE || "manual").trim().toLowerCase();
  if (mode !== "manual" && mode !== "auto") {
    console.error(`Неизвестный OFFER_MODE: ${mode}`);
    process.exit(1);
  }
  return mode;
}

function runManualPreview(target, orderResponsePath) {
  const result = spawnSync(
    "python",
    [
      "-m",
      "final_response.manual_preview",
      "--url",
      target,
      "--order-response",
      orderResponsePath,
    ],
    { encoding: "utf8", shell: true },
  );

  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }

  tgNotify("manual_preview", true);
}

function runOffer(args) {
  const result = spawnSync("python", args, { encoding: "utf8", shell: true });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);

  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  if (output.includes("offer: ok")) {
    tgNotify("offer_ok", true);
  } else if (output.includes("offer: no_balance")) {
    tgNotify("offer_no_balance", false);
  } else if (output.includes("offer: already")) {
    tgNotify("offer_already", false);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function loadEnv() {
  const envPath = path.join(__dirname, ".env");
  if (!fs.existsSync(envPath)) return;
  try {
    process.loadEnvFile(envPath);
  } catch {
    // Node < 20.12 — переменные задаются снаружи
  }
}

loadEnv();

const target = getArg("--target");
const mode = getOptionalArg("--mode");
const skipAi = hasFlag("--skip-ai");
const offerMode = resolveOfferMode();
const workDir = path.join(__dirname, ".simulate");
const projectJson = path.join(workDir, "project.json");
const orderResponse = path.join(workDir, "order-response.json");
const filesDir = path.join(workDir, "files");
const sessionPath = path.join(workDir, "session.json");

if (!fs.existsSync(sessionPath)) {
  console.error("нет сессии, запустите node auth.js");
  process.exit(1);
}

fs.mkdirSync(workDir, { recursive: true });

run("python", [
  "info2.py",
  "--target",
  target,
  "--output",
  projectJson,
  "--output-dir",
  filesDir,
  "--session",
  sessionPath,
]);

const project = JSON.parse(fs.readFileSync(projectJson, "utf8"));
if (project.type !== "project" && project.type !== "vacancy") {
  console.error(`Неизвестный тип страницы «${project.type}»`);
  process.exit(1);
}

console.log(`type: ${project.type}`);
console.log(`offer_mode: ${offerMode}`);

if (skipAi) {
  if (!fs.existsSync(orderResponse)) {
    console.error(`--skip-ai: нужен файл ${orderResponse}`);
    process.exit(1);
  }
} else {
  const aiArgs = ["ai.py", "--input", projectJson, "--output", orderResponse];
  if (mode) {
    aiArgs.push("--mode", mode);
  }
  run("python", aiArgs);
}

if (offerMode === "manual") {
  runManualPreview(target, orderResponse);
  process.exit(0);
}

const offerArgs = [
  "offer.py",
  "--target",
  target,
  "--order-response",
  orderResponse,
  "--session",
  sessionPath,
  "--type",
  project.type,
];

const resumePath = process.env.FL_RESUME_PATH;
if (project.type === "vacancy" && resumePath) {
  offerArgs.push("--resume-path", resumePath);
}

runOffer(offerArgs);
