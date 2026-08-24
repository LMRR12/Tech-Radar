const state={items:[],cat:"All",query:"",sort:"new"};
const $=s=>document.querySelector(s);

function esc(s=""){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function relative(iso){const d=Date.now()-new Date(iso).getTime(),m=Math.max(0,Math.floor(d/60000));if(m<60)return `${m}m ago`;const h=Math.floor(m/60);if(h<24)return `${h}h ago`;return `${Math.floor(h/24)}d ago`}
function render(){
 let x=state.items.filter(i=>state.cat==="All"||i.category===state.cat);
 if(state.query)x=x.filter(i=>(i.title+" "+i.description+" "+i.source+" "+i.category).toLowerCase().includes(state.query.toLowerCase()));
 if(state.sort==="signal")x.sort((a,b)=>(b.score||0)-(a.score||0));
 if(state.sort==="source")x.sort((a,b)=>a.source.localeCompare(b.source));
 if(state.sort==="new")x.sort((a,b)=>new Date(b.date)-new Date(a.date));
 $("#feed").innerHTML=x.length?x.map(i=>`<article class="card">
   <div class="meta"><span class="tag">${esc(i.category)}</span><span>${esc(i.source)} · ${relative(i.date)}</span></div>
   <h3><a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title)}</a></h3>
   <p>${esc(i.description||"No description available.")}</p>
   <div class="meta"><span>${esc(i.kind||"news")}</span><span class="score">SIGNAL ${i.score||50}</span></div>
 </article>`).join(""):`<div class="empty">No signals match that filter.</div>`;
 $("#stats").innerHTML=[
   ["TOTAL",state.items.length],["TODAY",state.items.filter(i=>Date.now()-new Date(i.date)<864e5).length],
   ["HIGH SIGNAL",state.items.filter(i=>(i.score||0)>=75).length],["SOURCES",new Set(state.items.map(i=>i.source)).size]
 ].map(x=>`<div class="stat"><b>${x[1]}</b><span>${x[0]}</span></div>`).join("");
}
async function load(){
 $("#feed").innerHTML='<div class="loading">Updating radar...</div>';
 try{
  const r=await fetch("data/news.json?"+Date.now()); if(!r.ok)throw Error("No data");
  const d=await r.json(); state.items=d.items||[]; $("#updated").textContent="updated "+new Date(d.generated_at).toLocaleString();
  render();
 }catch(e){$("#feed").innerHTML='<div class="empty">No generated feed yet. Run the GitHub Action once, then refresh.</div>'}
}
$("#filters").addEventListener("click",e=>{if(!e.target.dataset.cat)return;state.cat=e.target.dataset.cat;document.querySelectorAll(".filters button").forEach(b=>b.classList.remove("active"));e.target.classList.add("active");render()});
$("#search").addEventListener("input",e=>{state.query=e.target.value;render()});
$("#sort").addEventListener("change",e=>{state.sort=e.target.value;render()});
$("#refreshBtn").onclick=load;
$("#themeBtn").onclick=()=>document.body.classList.toggle("light");
setInterval(()=>$("#clock").textContent=new Date().toLocaleString([], {dateStyle:"medium",timeStyle:"short"}),1000);
load();