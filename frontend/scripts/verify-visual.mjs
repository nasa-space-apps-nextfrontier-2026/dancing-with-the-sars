/* global console, process */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const directory=resolve('docs/visual/phase5_1_current')
const sizes=[[1440,900],[1366,768],[1024,768],[768,1024],[390,844]]
const states=['main','alert','area','brief','routes','shelters','inspect','sources','signin','phone','main-layers','main-alerts']
let count=0
for(const [width,height] of sizes) for(const state of states) for(const kind of ['prototype','react']) {
  const name=`${kind}-${state}-${width}x${height}-light.png`
  const bytes=readFileSync(resolve(directory,name))
  if(bytes.subarray(1,4).toString()!=='PNG'||bytes.readUInt32BE(16)!==width||bytes.readUInt32BE(20)!==height) throw new Error(`Invalid image dimensions: ${name}`)
  count++
}
console.log(`PASS: ${count} screenshots / ${count/2} pairs across ${sizes.length} viewports`)
if(count!==120) process.exitCode=1
