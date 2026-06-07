// Оптимизация веса арта для веб: уменьшение размеров + сжатие PNG (с прозрачностью).
const sharp = require("D:/Claude/DigitalTwins/node_modules/sharp");
const fs = require("fs"), path = require("path");
const base = "D:/Claude/DigitalTwins/trenajer/assets";
const plan = { hub:1280, hero:520, product:760, station:800, ui:200 };

(async () => {
  for (const dir of Object.keys(plan)) {
    const d = path.join(base, dir);
    if (!fs.existsSync(d)) continue;
    for (const f of fs.readdirSync(d)) {
      if (!/\.png$/i.test(f)) continue;
      const p = path.join(d, f);
      const buf = fs.readFileSync(p);
      const meta = await sharp(buf).metadata();
      let img = sharp(buf);
      if (meta.width > plan[dir]) img = img.resize({ width: plan[dir] });
      const out = await img.png({ compressionLevel: 9, quality: 80, effort: 9, palette: true }).toBuffer();
      fs.writeFileSync(p, out);
      console.log(dir + "/" + f, meta.width + "px", Math.round(buf.length/1024) + "KB -> " + Math.round(out.length/1024) + "KB");
    }
  }
  console.log("done");
})().catch(e => { console.error(e); process.exit(1); });
