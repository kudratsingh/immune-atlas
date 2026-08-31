import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const dashboardRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const fixture = resolve(dashboardRoot, "../contracts/fixtures/bundle.small.json");
const destination = resolve(dashboardRoot, "public/data/bundle.json");

await mkdir(dirname(destination), { recursive: true });
await copyFile(fixture, destination);
process.stdout.write("Fixture bundle copied to dashboard/public/data/bundle.json\n");
