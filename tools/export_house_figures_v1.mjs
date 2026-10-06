#!/usr/bin/env node
/** Export the site's actual house components; no model, training or invented observations. */
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {existsSync,mkdirSync,mkdtempSync,readFileSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const site = path.resolve(process.argv[process.argv.indexOf('--site')+1] ?? '');
if (!process.argv.includes('--site') || !existsSync(path.join(site,'src/widgets/training'))) throw Error('Use --site /path/to/validated/profrod-site (Node 24 and installed site dependencies).');
const root = path.resolve(import.meta.dirname,'..');
const {createServer} = await import(pathToFileURL(path.join(site,'node_modules/vite/dist/node/index.js')));
const require = createRequire(path.join(site,'package.json'));
const {createElement} = require('react'), {renderToStaticMarkup} = require('react-dom/server');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const font=readFileSync(path.join(site,'public/fonts/routed-gothic/routed-gothic.ttf'));
const face=`@font-face{font-family:"Routed Gothic";src:url("data:font/ttf;base64,${font.toString('base64')}") format("truetype");font-weight:400}`;
const receiptNames={'train-a-tiny-gpt-on-colab':['tinygpt-t4-v1.json','tinygpt-full-20261003.json'],'sft-then-dpo-on-a-colab-t4':['sftdpo-t4-v1.json','sftdpo-full-20261003.json']};
const specs=[
 ['train-a-tiny-gpt-on-colab','figures-v4','tinygpt-attention','AttentionBoundary'],
 ['train-a-tiny-gpt-on-colab','figures-v4','tinygpt-curves','TrainingCurves'],
 ['train-a-tiny-gpt-on-colab','figures-v4','tinygpt-intervals','PredictionInterval'],
 ['sft-then-dpo-on-a-colab-t4','figures-v2','sftdpo-seeds','PairedSeeds'],
 ['sft-then-dpo-on-a-colab-t4','figures-v2','sftdpo-intervals','PairedIntervals'],
];
const work=mkdtempSync(path.join(tmpdir(),'profrod-house-exports-'));
const vite=await createServer({root:site,configFile:false,resolve:{alias:{'@':path.join(site,'src'),'@sa/brand':path.join(site,'src/brand-local'),'@sa/assets':path.join(site,'src/assets-local')}},esbuild:{jsx:'automatic'},server:{middlewareMode:true,watch:null},appType:'custom'});
const head=execFileSync('git',['rev-parse','HEAD'],{cwd:site,encoding:'utf8'}).trim();
const outputs=new Map();
try {
 for(const [slug,version,name,moduleName] of specs){
  const out=path.join(root,'articles',slug,version);mkdirSync(out,{recursive:true});
  const [siteReceipt,companionReceipt]=receiptNames[slug];
  const raw=readFileSync(path.join(root,'articles',slug,'receipts/colab',companionReceipt));
  if(sha(raw)!==sha(readFileSync(path.join(site,'src/widgets/training',siteReceipt))))throw Error('Receipt differs from site: '+slug);
  const {default:Figure}=await vite.ssrLoadModule('/src/widgets/training/'+moduleName+'.tsx');
  const html=renderToStaticMarkup(createElement(Figure));
  const desc=html.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
  const contextFile=name+'.html';
  writeFileSync(path.join(out,contextFile),'<!doctype html><meta charset="utf-8"><style>'+face+'body{max-width:760px;margin:2rem auto;background:#F4EFE2;color:#2F4A43;font:17px Georgia}svg{display:block;width:100%;height:auto}details{display:block}figure{margin:0}table{width:100%;border-collapse:collapse}th,td{padding:.3rem;text-align:left}</style>'+html.replace(/<details\b/g,'<details open'));
  const svgs=[...html.matchAll(/<svg\b[^>]*\brole="img"[\s\S]*?<\/svg>/g)].map(m=>m[0]);
  if(!svgs.length)throw Error('No rendered house SVG: '+name);
  const rows=outputs.get(out)??[];
  for(let i=0;i<svgs.length;i++){
   const stem=name+(svgs.length>1?'-'+['healthy','no-causal-mask','softmax-wrong-dim','no-zero-grad'][i]:'');
   const vb=/viewBox="([^"]+)"/.exec(svgs[i])[1].split(' ').map(Number), width=vb[2],height=vb[3];
   const svg=svgs[i].replace('<svg ',`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" `).replace(/ class="[^"]*"/g,'').replace(/ aria-labelledby="[^"]*"/,' aria-labelledby="export-context"').replace('><defs>',`><desc id="export-context">${desc}</desc><style>${face}</style><defs>`);
   writeFileSync(path.join(out,stem+'.svg'),svg+'\n');
   const page=path.join(work,stem+'.html');
   writeFileSync(page,`<!doctype html><meta charset="utf-8"><style>${face}body{margin:0;width:${width}px;height:${height}px}svg{display:block}</style>${svg}`);
   const chrome=process.env.CHROME_PATH;
   if(!chrome||!existsSync(chrome))throw Error('Set CHROME_PATH to Chromium for PNG export.');
   execFileSync(chrome,['--headless','--disable-gpu','--hide-scrollbars','--allow-file-access-from-files',`--user-data-dir=${path.join(work,'profile-'+stem)}`,`--window-size=${width},${height}`,'--force-device-scale-factor=2','--virtual-time-budget=3000',`--screenshot=${path.join(out,stem+'.png')}`,pathToFileURL(page).href],{stdio:'ignore'});
   rows.push({name:stem,svgSha256:sha(readFileSync(path.join(out,stem+'.svg'))),pngSha256:sha(readFileSync(path.join(out,stem+'.png'))),contextFile,contextSha256:sha(readFileSync(path.join(out,contextFile))),receiptSha256:sha(raw),component:'src/widgets/training/'+moduleName+'.tsx',componentSha256:sha(readFileSync(path.join(site,'src/widgets/training',moduleName+'.tsx')))});
  }
  outputs.set(out,rows);
 }
}finally{await vite.close();}
for(const [out,figures] of outputs){
 writeFileSync(path.join(out,'Routed-Gothic-OFL.txt'),readFileSync(path.join(site,'vendor/fonts/OFL.txt')));
 const shared=['src/widgets/training/measured.ts','src/widgets/training/FigureShell.tsx','src/widgets/chalkboard/chalk.tsx','src/widgets/chalkboard/chalkTokens.ts','src/components/content/ProfrodMark.tsx','src/lib/diagrams/diagramSource.mjs','src/diagrams/profrod-mark.json'];
 writeFileSync(path.join(out,'manifest.json'),JSON.stringify({siteRepo:'rodriveracom/profrod-site',siteCommit:head,font:{name:'Routed Gothic',sha256:sha(font),license:'SIL Open Font License 1.1; see Routed-Gothic-OFL.txt'},sharedSources:shared.map(file=>({file,sha256:sha(readFileSync(path.join(site,file)))})),figures,evidence:'Original hash-bound operator T4 receipts. No new run or reconstruction. Read adjacent HTML context, including legends/tables and conditional uncertainty limits. SVGs embed the licensed font; PNGs are 2× raster exports of those actual boards.'},null,2)+'\n');
 console.log(path.relative(root,out)+': '+figures.length+' house boards exported');
}
