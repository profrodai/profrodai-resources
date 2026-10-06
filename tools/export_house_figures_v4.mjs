#!/usr/bin/env node
/** Append P1/P2 legible scientific WebPs and static worked context; keep prior exports immutable. */
import {createHash} from "node:crypto";
import {createRequire} from "node:module";
import {execFileSync} from "node:child_process";
import {existsSync,mkdirSync,readFileSync,writeFileSync} from "node:fs";
import path from "node:path";
import {pathToFileURL} from "node:url";
const site=path.resolve(process.argv[process.argv.indexOf("--site")+1]??"");
if(!process.argv.includes("--site")||!existsSync(path.join(site,"src/figures/provenance-v1.json")))throw Error("Use --site /path/to/validated/profrod-site with Node 24 and installed site dependencies.");
if(execFileSync("git",["status","--porcelain"],{cwd:site,encoding:"utf8"}).trim())throw Error("Export only from a clean, committed site checkout.");
const root=path.resolve(import.meta.dirname,".."),sha=b=>createHash("sha256").update(b).digest("hex");
const head=execFileSync("git",["rev-parse","HEAD"],{cwd:site,encoding:"utf8"}).trim();
const provenance=JSON.parse(readFileSync(path.join(site,"src/figures/provenance-v1.json"),"utf8"));
const require=createRequire(path.join(site,"package.json")),{createElement}=require("react"),{renderToStaticMarkup}=require("react-dom/server");
const {createServer}=await import(pathToFileURL(path.join(site,"node_modules/vite/dist/node/index.js")));
const vite=await createServer({root:site,configFile:false,resolve:{alias:{"@":path.join(site,"src"),"@sa/brand":path.join(site,"src/brand-local"),"@sa/assets":path.join(site,"src/assets-local")}},esbuild:{jsx:"automatic"},server:{middlewareMode:true,watch:null},appType:"custom"});
const specs=[
 ["train-a-tiny-gpt-on-colab","figures-v7",["tinygpt-attention","tinygpt-curves","tinygpt-intervals"],"tinygpt-t4-v1.json","tinygpt-full-20261003.json"],
 ["sft-then-dpo-on-a-colab-t4","figures-v4",["sftdpo-seeds","sftdpo-intervals","sftdpo-margin"],"sftdpo-t4-v1.json","sftdpo-full-20261003.json"],
];
const font=readFileSync(path.join(site,"public/fonts/routed-gothic/routed-gothic.ttf"));
const face='@font-face{font-family:"Routed Gothic";src:url("data:font/ttf;base64,'+font.toString("base64")+'") format("truetype")}';
try {
 const {FIGURES}=await vite.ssrLoadModule("/src/widgets/figures.ts");
 for(const [slug,version,names,siteReceipt,resourceReceipt] of specs) {
  const out=path.join(root,"articles",slug,version);if(existsSync(out))throw Error("Retain immutable exports; choose a new version: "+out);mkdirSync(out,{recursive:true});
  const receipt=readFileSync(path.join(root,"articles",slug,"receipts/colab",resourceReceipt));
  if(sha(receipt)!==sha(readFileSync(path.join(site,"src/widgets/training",siteReceipt))))throw Error("Receipt differs from site: "+slug);
  const figures=[];
  for(const name of names) {
   const rows=provenance.figures.filter(row=>row.kind==="research"&&row.name===name);
   if(!rows.length)throw Error("Missing delivered figure: "+name);
   const local=new Map();
   for(const [index,row] of rows.entries()) {
    const label=name+(rows.length>1?"-"+["healthy","no-causal-mask","softmax-wrong-dim","no-zero-grad"][index]:"");
    const source=readFileSync(path.join(site,"src/figures/rendered",row.key+".svg"));
    if(sha(source)!==row.sourceSvgSha256)throw Error("Source drawing differs: "+name);
    writeFileSync(path.join(out,label+".source.svg"),source);
    const artifacts=[];
    for(const artifact of row.artifacts) {
     const bytes=readFileSync(path.join(site,"content/figure-media",artifact.file));
     if(sha(bytes)!==artifact.sha256||bytes.length!==artifact.bytes)throw Error("Delivery artifact differs: "+artifact.file);
     const file=label+"-w"+artifact.width+".webp";writeFileSync(path.join(out,file),bytes);
     local.set("/figure-media/"+artifact.file,file);artifacts.push({...artifact,file});
    }
    figures.push({name:label,key:row.key,sourceSvgSha256:row.sourceSvgSha256,artifacts,receiptSha256:sha(receipt),component:name,contextFile:name+".html"});
   }
   const {default:Figure}=await FIGURES[name]();let html=renderToStaticMarkup(createElement(Figure));
   for(const [url,file] of local)html=html.split(url).join(file);
   html=html.replace(/<details\b/g,"<details open").replace(/<(select|input|button)\b/g,"<$1 disabled");
   const doc='<!doctype html><meta charset="utf-8"><title>'+name+' — Prof Rod</title><style>'+face+'body{max-width:760px;margin:2rem auto;padding:0 1rem;background:#F4EFE2;color:#2F4A43;font:17px Georgia}img[data-house-figure]{display:block;width:100%;height:auto;border-radius:10px}figure{margin:0 0 2rem}figcaption{font-size:1.3rem;font-weight:bold}details{margin:1.5rem 0}summary{font-weight:bold}table{width:100%;border-collapse:collapse}th,td{padding:.4rem;text-align:left}a{color:inherit}svg[aria-hidden]{width:14px;height:14px;vertical-align:middle}li{margin:.4rem 0}</style><p><strong>Static companion export.</strong> Controls show the initial state and are disabled here. The worked comparison remains expanded below (C → D for attention; −1/−3 for the DPO margin). The website supplies the interactive exploration after its publication hold is released.</p>'+html;
   writeFileSync(path.join(out,name+".html"),doc);
   for(const row of figures.filter(row=>row.component===name))row.contextSha256=sha(Buffer.from(doc));
  }
  writeFileSync(path.join(out,"Routed-Gothic-OFL.txt"),readFileSync(path.join(site,"vendor/fonts/OFL.txt")));
  const shared=["src/widgets/training/measured.ts","src/widgets/training/AttentionBoundary.tsx","src/widgets/training/attentionModel.ts","src/widgets/training/DpoMargin.tsx","src/widgets/training/dpoModel.ts","src/widgets/training/TrainingCurves.tsx","src/widgets/training/PairedSeeds.tsx","src/widgets/training/PairedIntervals.tsx","src/widgets/training/PredictionInterval.tsx","src/widgets/training/FigureShell.tsx","src/widgets/chalkboard/chalk.tsx","src/widgets/chalkboard/RasterFigure.tsx","src/widgets/chalkboard/chalkTokens.ts","src/components/content/ProfrodMark.tsx","src/lib/diagrams/diagramSource.mjs","src/diagrams/profrod-mark.json"];
  writeFileSync(path.join(out,"manifest.json"),JSON.stringify({siteRepo:"rodriveracom/profrod-site",siteCommit:head,font:{name:"Routed Gothic",sha256:sha(font),license:"SIL Open Font License 1.1; see Routed-Gothic-OFL.txt"},sharedSources:shared.map(file=>({file,sha256:sha(readFileSync(path.join(site,file)))})),rendererSources:provenance.rendererSources,figures,evidence:"Exact responsive WebP bytes delivered by the site, with adjacent HTML descriptions, legends and tables. .source.svg files are editable authoring sources, not the website image format. The attention and fixed-reference DPO examples are synthetic arithmetic, separate from the unchanged operator T4 receipts. Static controls are disabled in this export; no training, new measurement or publication is implied."},null,2)+"\n");
  console.log(path.relative(root,out)+": "+figures.length+" boards, four exact WebP widths each");
 }
}finally{await vite.close();}
