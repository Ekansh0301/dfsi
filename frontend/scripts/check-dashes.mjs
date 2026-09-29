// Fails the build if an em dash or en dash appears in site content or docs.
// Runs automatically before `npm run build` (see "prebuild" in package.json).
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const BANNED = /[\u2014\u2013]/;
const TARGETS = ["src", "public", "index.html", "package.json", "README.md", "../README.md"];
const TEXT = /\.(tsx?|jsx?|mjs|css|html|md|json|svg|webmanifest|txt)$/;

const files = [];
const walk = (p) => {
  if (!existsSync(p)) return;
  if (statSync(p).isDirectory()) readdirSync(p).forEach((f) => walk(join(p, f)));
  else if (TEXT.test(p)) files.push(p);
};
TARGETS.forEach(walk);

const hits = [];
for (const f of files) {
  readFileSync(f, "utf8")
    .split("\n")
    .forEach((line, i) => BANNED.test(line) && hits.push(`${relative(".", f)}:${i + 1}: ${line.trim()}`));
}

if (hits.length) {
  console.error(`Found ${hits.length} line(s) with an em/en dash. Use a comma, colon, period or hyphen instead:\n` + hits.join("\n"));
  process.exit(1);
}
console.log(`Dash check passed (${files.length} files).`);
