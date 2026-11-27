const $=s=>document.querySelector(s);
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function load(){
 const [res,statsRes]=await Promise.all([fetch('/api/jobs'),fetch('/api/stats')]);
 const jobs=await res.json(),stats=await statsRes.json();
 $('#sourceTotal').textContent=stats.total+' total records';
 $('#sourceCounts').innerHTML=Object.entries(stats.sources).map(([name,count])=>`<div class="source-count"><span>${esc(name)}</span><strong>${count}</strong></div>`).join('');
 $('#total').textContent=jobs.length;$('#strong').textContent=jobs.filter(j=>j.match>=70).length;
 $('#progress').textContent=jobs.filter(j=>['Applied','Interview','Follow-up'].includes(j.status)).length;
 const q=$('#search').value.toLowerCase();
 const filtered=jobs.filter(j=>(j.title+' '+j.company+' '+j.location+' '+j.description).toLowerCase().includes(q));
 $('#jobs').innerHTML=filtered.length?filtered.map(j=>`<article class="job">
 <div class="jobtop"><div><h3>${esc(j.title)}</h3><div class="muted">${esc(j.company||'Company not specified')} · ${esc(j.location||'Location not specified')} · ${esc(j.source)}</div></div><div class="score">${j.match}% match</div></div>
 <p class="muted">Matched skills: ${j.matched_skills.map(esc).join(', ')||'No profile keywords found yet'}</p>
 <div class="jobfoot"><span class="muted">Status: ${esc(j.status)}</span><div>${j.url?`<a href="${esc(j.url)}" target="_blank" rel="noopener">Apply / view listing ↗</a> · `:''}
 <select aria-label="Application status" onchange="setStatus(${j.id},this.value)">${['New','Shortlisted','Applied','Interview','Rejected','Not suitable'].map(s=>`<option ${s===j.status?'selected':''}>${s}</option>`).join('')}</select></div></div>
 ${j.source==='Himalayas'?'<div class="muted">Source: <a href="https://himalayas.app" target="_blank" rel="noopener">Himalayas</a></div>':''}</article>`).join(''):'<div class="empty">No matching jobs yet. Use Discover jobs now or add a listing above.</div>';
}
async function setStatus(id,status){await fetch('/api/jobs/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});load()}
$('#discoverBtn').addEventListener('click',async()=>{const b=$('#discoverBtn'),m=$('#discoverMessage');b.disabled=true;b.textContent='Searching…';m.textContent='Checking public job listings. This may take a few seconds.';
 try{const r=await fetch('/api/discover',{method:'POST'}),d=await r.json();if(!r.ok)throw new Error(d.error||'Discovery failed');
 const summary=(d.sources||[]).map(s=>s.source+': added '+s.added+'; '+s.duplicates+' duplicates').join(' · ');m.textContent=(summary||'No feed results returned.')+(d.errors?.length?' Errors: '+d.errors.join(' | '):'');await load();
 }catch(e){m.textContent='Could not complete discovery: '+e.message}
 finally{b.disabled=false;b.textContent='Discover jobs now'}});
$('#jobForm').addEventListener('submit',async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));const r=await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(r.ok){e.target.reset();load()}else alert((await r.json()).error||'Could not add job')});
$('#search').addEventListener('input',load);load();