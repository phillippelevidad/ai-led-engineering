const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const claudeSkillsDir = path.join(root, ".claude", "skills");
const agentsSkillsDir = path.join(root, ".agents", "skills");

if (fs.existsSync(claudeSkillsDir)) {
  fs.rmSync(claudeSkillsDir, { recursive: true, force: true });
}

if (!fs.existsSync(agentsSkillsDir)) {
  console.error(`Source directory not found: ${agentsSkillsDir}`);
  process.exit(1);
}

fs.mkdirSync(claudeSkillsDir, { recursive: true });

const linkType = process.platform === "win32" ? "junction" : "dir";

for (const entry of fs.readdirSync(agentsSkillsDir, { withFileTypes: true })) {
  if (!entry.isDirectory()) {
    continue;
  }

  const target = path.join(agentsSkillsDir, entry.name);
  const link = path.join(claudeSkillsDir, entry.name);
  fs.symlinkSync(target, link, linkType);
  console.log(`Linked ${entry.name}`);
}
