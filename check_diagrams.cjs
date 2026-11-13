const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/sachi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async () => {
  const root = path.resolve(__dirname, '../dancing-with-the-sars/docs');
  const browser = await chromium.launch({executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true, args:['--disable-gpu']});
  const page = await browser.newPage({viewport:{width:1600,height:1200}});
  await page.setContent('<html><body style="background:white"></body></html>');
  await page.addScriptTag({path:path.join(__dirname,'mermaid.min.js')});
  await page.evaluate(() => mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'default'}));
  const results = [];
  for (const name of fs.readdirSync(root).filter(x=>x.endsWith('.md'))) {
    const text = fs.readFileSync(path.join(root,name),'utf8');
    for (const match of text.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)) {
      const id = 'diagram' + results.length;
      try {
        const svg = await page.evaluate(async ({content,id})=>{
          await mermaid.parse(content);
          const r=await mermaid.render(id,content);
          return r.svg;
        },{content:match[1],id});
        fs.mkdirSync(path.join(__dirname,'diagrams'),{recursive:true});
        fs.writeFileSync(path.join(__dirname,'diagrams',id+'.svg'),svg);
        results.push({file:name,id,status:'PASS'});
      } catch(e) { results.push({file:name,id,status:'FAIL',error:String(e)}); }
    }
  }
  await browser.close();
  fs.writeFileSync(path.join(__dirname,'diagram-results.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results,null,2));
  process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});
