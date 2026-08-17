import { execFileSync } from "node:child_process";
import { access, chmod, mkdir, unlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const destDir = path.join(root, "defaults", "bin");
const dest = path.join(destDir, "bw");
const url = "https://vault.bitwarden.com/download/?app=cli&platform=linux";

try {
  await access(dest);
  await chmod(dest, 0o755);
  console.log(`bw already present: ${dest}`);
  process.exit(0);
} catch {
  // download
}

await mkdir(destDir, { recursive: true });
const res = await fetch(url);
if (!res.ok) {
  throw new Error(`download failed: ${res.status}`);
}
const tmpZip = path.join(destDir, ".bw.zip");
await writeFile(tmpZip, Buffer.from(await res.arrayBuffer()));

try {
  execFileSync("unzip", ["-qo", tmpZip, "bw", "-d", destDir], { stdio: "inherit" });
} catch {
  execFileSync(
    "python3",
    [
      "-c",
      "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extract('bw', sys.argv[2])",
      tmpZip,
      destDir,
    ],
    { stdio: "inherit" },
  );
} finally {
  await unlink(tmpZip).catch(() => {});
}

await chmod(dest, 0o755);
console.log(`fetched ${dest}`);
