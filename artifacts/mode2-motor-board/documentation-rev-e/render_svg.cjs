const fs = require('fs');
const sharp = require('C:/Users/LS404/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
async function main() {
  for (const side of ['front', 'back']) {
    const path = `${__dirname}/assets/pcb-${side}-copper`;
    const xml = fs.readFileSync(`${path}.svg`, 'utf8').replace(/width="[^"]+mm" height="[^"]+mm"/, 'width="1600px" height="1535px"');
    await sharp(Buffer.from(xml)).flatten({background:'#ffffff'}).png().toFile(`${path}.png`);
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
