"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const BUILTIN_PACKAGES = ["npm:pi-web-access", "npm:@tifan/pi-fixed-editor"];
const RECONCILE_VERSION = 1;
const SETTINGS_LOCK_RETRY_MS = 20;
const SETTINGS_LOCK_ATTEMPTS = 750;
const SETTINGS_LOCK_STALE_MS = 10_000;
const sleepBuffer = new Int32Array(new SharedArrayBuffer(4));

function readJsonObject(file) {
  try {
    const value = JSON.parse(fs.readFileSync(file, "utf8"));
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch (_) {
    return {};
  }
}

function stringMap(value) {
  if (value === undefined) return {};
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  const result = {};
  for (const [identity, source] of Object.entries(value)) {
    if (typeof identity !== "string" || typeof source !== "string") return undefined;
    result[identity] = source;
  }
  return result;
}

function readReconcileState(file) {
  try {
    const value = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return { corrupt: true, managed: {}, pendingGit: {}, pendingRemove: {} };
    }
    const managed = stringMap(value.managed);
    const pendingGit = stringMap(value.pendingGit);
    const pendingRemove = stringMap(value.pendingRemove);
    if (
      value.version !== RECONCILE_VERSION ||
      managed === undefined ||
      pendingGit === undefined ||
      pendingRemove === undefined
    ) {
      return { corrupt: true, managed: {}, pendingGit: {}, pendingRemove: {} };
    }
    return { corrupt: false, managed, pendingGit, pendingRemove };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { corrupt: false, managed: {}, pendingGit: {}, pendingRemove: {} };
    }
    return { corrupt: true, managed: {}, pendingGit: {}, pendingRemove: {} };
  }
}

function writeJsonAtomic(file, value, defaultMode = 0o600) {
  const content = `${JSON.stringify(value, null, 2)}\n`;
  try {
    if (fs.readFileSync(file, "utf8") === content) return;
  } catch (_) {}

  const directory = path.dirname(file);
  fs.mkdirSync(directory, { recursive: true });
  let mode = defaultMode;
  try {
    mode = fs.statSync(file).mode & 0o777;
  } catch (_) {}

  const temporary = path.join(
    directory,
    `.${path.basename(file)}.${process.pid}.${Date.now()}.tmp`,
  );
  try {
    fs.writeFileSync(temporary, content, { encoding: "utf8", mode });
    const descriptor = fs.openSync(temporary, "r");
    try {
      fs.fsyncSync(descriptor);
    } finally {
      fs.closeSync(descriptor);
    }
    fs.renameSync(temporary, file);
  } finally {
    try {
      fs.unlinkSync(temporary);
    } catch (_) {}
  }
}

function sleepSync(milliseconds) {
  Atomics.wait(sleepBuffer, 0, 0, milliseconds);
}

function acquireSettingsLock(settingsFile) {
  const lockPath = `${settingsFile}.lock`;
  fs.mkdirSync(path.dirname(settingsFile), { recursive: true });
  for (let attempt = 0; attempt < SETTINGS_LOCK_ATTEMPTS; attempt += 1) {
    try {
      fs.mkdirSync(lockPath);
      return () => {
        try {
          fs.rmdirSync(lockPath);
        } catch (_) {}
      };
    } catch (error) {
      if (!error || error.code !== "EEXIST") throw error;
      try {
        const age = Date.now() - fs.statSync(lockPath).mtimeMs;
        if (age > SETTINGS_LOCK_STALE_MS) {
          fs.rmSync(lockPath, { recursive: true, force: true });
          continue;
        }
      } catch (statError) {
        if (!statError || statError.code !== "ENOENT") throw statError;
        continue;
      }
      sleepSync(SETTINGS_LOCK_RETRY_MS);
    }
  }
  throw new Error(`timed out acquiring Pi settings lock: ${lockPath}`);
}

function withSettingsLock(settingsFile, operation) {
  const release = acquireSettingsLock(settingsFile);
  try {
    return operation();
  } finally {
    release();
  }
}

function packageSource(entry) {
  if (typeof entry === "string") return entry;
  if (entry && typeof entry === "object" && typeof entry.source === "string") {
    return entry.source;
  }
  return undefined;
}

function npmIdentity(source) {
  const spec = source.slice("npm:".length);
  if (!spec) return undefined;
  if (spec.startsWith("@")) {
    const slash = spec.indexOf("/");
    if (slash < 2) return undefined;
    const versionSeparator = spec.indexOf("@", slash + 1);
    return `npm:${versionSeparator < 0 ? spec : spec.slice(0, versionSeparator)}`;
  }
  const versionSeparator = spec.indexOf("@");
  return `npm:${versionSeparator < 0 ? spec : spec.slice(0, versionSeparator)}`;
}

function pathWithoutRef(pathWithRef) {
  const separator = pathWithRef.indexOf("@");
  return separator < 0 ? pathWithRef : pathWithRef.slice(0, separator);
}

function gitIdentity(source) {
  const spec = source.slice("git:".length).trim();
  if (!spec) return undefined;

  let host;
  let repositoryPath;
  const scpLike = spec.match(/^git@([^:]+):(.+)$/);
  if (scpLike) {
    host = scpLike[1];
    repositoryPath = pathWithoutRef(scpLike[2]);
  } else if (spec.includes("://")) {
    try {
      const parsed = new URL(spec);
      host = parsed.hostname;
      repositoryPath = pathWithoutRef(parsed.pathname.replace(/^\/+/, ""));
    } catch (_) {
      return undefined;
    }
  } else {
    const slash = spec.indexOf("/");
    if (slash < 1) return undefined;
    host = spec.slice(0, slash);
    repositoryPath = pathWithoutRef(spec.slice(slash + 1));
  }

  const normalizedHost = host?.toLowerCase();
  const normalizedPath = repositoryPath
    ?.replace(/^\/+|\/+$/g, "")
    .replace(/\.git$/, "");
  if (
    !normalizedHost ||
    !normalizedPath ||
    normalizedPath.split("/").length < 2 ||
    normalizedPath.split("/").includes("..")
  ) {
    return undefined;
  }
  return `git:${normalizedHost}/${normalizedPath}`;
}

function packageIdentity(entry) {
  const source = packageSource(entry);
  if (!source) return undefined;
  if (source.startsWith("npm:")) return npmIdentity(source);
  if (source.startsWith("git:")) return gitIdentity(source);
  return undefined;
}

function coalesceManagedPackages(sources) {
  const managed = [];
  const indexes = new Map();
  for (const source of sources) {
    const identity = packageIdentity(source);
    if (!identity) throw new Error(`invalid managed package source: ${source}`);
    const existingIndex = indexes.get(identity);
    if (existingIndex === undefined) {
      indexes.set(identity, managed.length);
      managed.push({ identity, source });
    } else {
      managed[existingIndex] = { identity, source };
    }
  }
  return managed;
}

function replaceEntrySource(entry, source) {
  return typeof entry === "string" ? source : { ...entry, source };
}

function mergePackages(existingPackages, managedPackages) {
  const desiredByIdentity = new Map(
    managedPackages.map(({ identity, source }) => [identity, source]),
  );
  const seen = new Set();
  const changedIdentities = new Set();
  const packages = [];

  for (const entry of existingPackages) {
    const identity = packageIdentity(entry);
    const desiredSource = identity ? desiredByIdentity.get(identity) : undefined;
    if (!identity || desiredSource === undefined) {
      packages.push(entry);
      continue;
    }
    if (seen.has(identity)) continue;
    seen.add(identity);
    if (packageSource(entry) !== desiredSource) changedIdentities.add(identity);
    packages.push(replaceEntrySource(entry, desiredSource));
  }

  for (const { identity, source } of managedPackages) {
    if (seen.has(identity)) continue;
    seen.add(identity);
    changedIdentities.add(identity);
    packages.push(source);
  }

  return { packages, changedIdentities };
}

function decodeHostPackages(encoded) {
  return Buffer.from(encoded || "", "base64")
    .toString("utf8")
    .split(/\n/)
    .filter(Boolean);
}

function runCommand(command, args, options, description) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    env: process.env,
    stdio: "inherit",
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const reason = result.signal ? `signal ${result.signal}` : `exit status ${result.status}`;
    throw new Error(`${description}: ${reason}`);
  }
}

function runPiPackageCommand(action, source) {
  runCommand(
    "pi",
    [action, source, "--no-approve"],
    { cwd: "/" },
    `pi ${action} failed for ${source}`,
  );
}

function gitInstallDirectory(identity, settingsFile) {
  const gitRoot = path.resolve(path.dirname(settingsFile), "git");
  const relativePath = identity.slice("git:".length);
  const installDirectory = path.resolve(gitRoot, relativePath);
  if (!installDirectory.startsWith(`${gitRoot}${path.sep}`)) {
    throw new Error(`refusing Git install path outside ${gitRoot}: ${identity}`);
  }
  return installDirectory;
}

function installGitDependencies(identity, settingsFile, settings) {
  const installDirectory = gitInstallDirectory(identity, settingsFile);
  if (!fs.existsSync(path.join(installDirectory, "package.json"))) return;

  const configured = settings.npmCommand;
  if (Array.isArray(configured) && configured.length > 0) {
    if (!configured.every((part) => typeof part === "string" && part.length > 0)) {
      throw new Error("invalid npmCommand in Pi settings");
    }
    const [command, ...prefixArgs] = configured;
    runCommand(
      command,
      [...prefixArgs, "install"],
      { cwd: installDirectory },
      `dependency install failed for ${identity}`,
    );
    return;
  }

  runCommand(
    "npm",
    ["install", "--omit=dev"],
    { cwd: installDirectory },
    `dependency install failed for ${identity}`,
  );
}

function writeReconcileState(file, state) {
  writeJsonAtomic(file, {
    version: RECONCILE_VERSION,
    managed: state.managed,
    pendingGit: state.pendingGit,
    pendingRemove: state.pendingRemove,
  });
}

function npmInstallDirectory(identity, settingsFile) {
  const packageName = identity.slice("npm:".length);
  const installRoot = path.resolve(path.dirname(settingsFile), "npm", "node_modules");
  const installDirectory = path.resolve(installRoot, packageName);
  if (!installDirectory.startsWith(`${installRoot}${path.sep}`)) {
    throw new Error(`refusing npm removal path outside ${installRoot}: ${identity}`);
  }
  return installDirectory;
}

function removePackageArtifacts(identity, settingsFile) {
  const installDirectory = identity.startsWith("git:")
    ? gitInstallDirectory(identity, settingsFile)
    : npmInstallDirectory(identity, settingsFile);
  fs.rmSync(installDirectory, { recursive: true, force: true });
}

function reconcileRemovedPackages(state, reconcileFile, settingsFile) {
  for (const [identity] of Object.entries(state.pendingRemove)) {
    removePackageArtifacts(identity, settingsFile);
    delete state.pendingRemove[identity];
    writeReconcileState(reconcileFile, state);
  }
}

function reconcileGitPackages(state, reconcileFile, settingsFile, settings) {
  for (const [identity, source] of Object.entries(state.pendingGit)) {
    runPiPackageCommand("install", source);
    // Pi skips npm install when a previous interrupted attempt already moved HEAD.
    // Run it once more before clearing durable pending state.
    installGitDependencies(identity, settingsFile, settings);
    delete state.pendingGit[identity];
    writeReconcileState(reconcileFile, state);
  }
}

function configureKeybindings(keybindingsFile) {
  const keybindings = readJsonObject(keybindingsFile);
  const newLineAction = "tui.input.newLine";
  const existingNewLine = keybindings[newLineAction] ?? keybindings.newLine;
  const newLineKeys = Array.isArray(existingNewLine)
    ? existingNewLine.filter((key) => typeof key === "string")
    : typeof existingNewLine === "string"
      ? [existingNewLine]
      : ["shift+enter"];
  for (const key of ["shift+enter", "ctrl+j"]) {
    if (!newLineKeys.includes(key)) newLineKeys.push(key);
  }
  keybindings[newLineAction] = newLineKeys;
  delete keybindings.newLine;
  writeJsonAtomic(keybindingsFile, keybindings);
}

function prepareBootstrap(settingsFile, keybindingsFile, reconcileFile, hostPackages) {
  const managedPackages = coalesceManagedPackages([...BUILTIN_PACKAGES, ...hostPackages]);
  const managedHostPackages = new Map(
    coalesceManagedPackages(hostPackages).map(({ identity, source }) => [identity, source]),
  );
  const managedHostGit = new Map(
    [...managedHostPackages].filter(([identity]) => identity.startsWith("git:")),
  );

  const settings = readJsonObject(settingsFile);
  const reconcileState = readReconcileState(reconcileFile);
  const pendingRemove = {};
  for (const [identity, source] of Object.entries(reconcileState.pendingRemove)) {
    if (!managedHostPackages.has(identity)) pendingRemove[identity] = source;
  }
  for (const [identity, source] of Object.entries(reconcileState.managed)) {
    if (!managedHostPackages.has(identity)) pendingRemove[identity] = source;
  }

  const pendingGit = {};
  for (const [identity] of Object.entries(reconcileState.pendingGit)) {
    const currentSource = managedHostGit.get(identity);
    if (currentSource) pendingGit[identity] = currentSource;
  }
  if (reconcileState.corrupt) {
    for (const [identity, source] of managedHostGit) pendingGit[identity] = source;
  }

  const removedIdentities = new Set(Object.keys(pendingRemove));
  const existingPackages = (Array.isArray(settings.packages) ? settings.packages : [])
    .filter((entry) => !removedIdentities.has(packageIdentity(entry)));
  const merged = mergePackages(existingPackages, managedPackages);
  for (const identity of merged.changedIdentities) {
    const source = managedHostGit.get(identity);
    if (source) pendingGit[identity] = source;
  }

  const state = {
    managed: Object.fromEntries(managedHostPackages),
    pendingGit,
    pendingRemove,
  };

  // Persist pending work first. If startup is interrupted after settings change,
  // the next run must finish install/remove before loading extensions.
  writeReconcileState(reconcileFile, state);
  reconcileRemovedPackages(state, reconcileFile, settingsFile);
  settings.packages = merged.packages;
  writeJsonAtomic(settingsFile, settings, 0o644);
  configureKeybindings(keybindingsFile);
  return { settings, state };
}

function main() {
  const settingsFile = process.env.PI_SETTINGS_FILE || "/home/pi/.pi/agent/settings.json";
  const keybindingsFile = process.env.PI_KEYBINDINGS_FILE || "/home/pi/.pi/agent/keybindings.json";
  const reconcileFile =
    process.env.PIDOCKER_PACKAGE_RECONCILE_FILE ||
    "/home/pi/.pidocker/package-reconcile.json";
  const hostPackages = decodeHostPackages(process.env.PIDOCKER_PACKAGE_SPECS_B64);

  const prepared = withSettingsLock(settingsFile, () =>
    prepareBootstrap(settingsFile, keybindingsFile, reconcileFile, hostPackages),
  );
  reconcileRemovedPackages(prepared.state, reconcileFile, settingsFile);
  reconcileGitPackages(
    prepared.state,
    reconcileFile,
    settingsFile,
    prepared.settings,
  );
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`pidocker: package bootstrap failed: ${message}`);
    process.exitCode = 1;
  }
}

module.exports = {
  coalesceManagedPackages,
  gitIdentity,
  mergePackages,
  npmIdentity,
  packageIdentity,
};
