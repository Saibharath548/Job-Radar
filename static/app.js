const $=s=>document.querySelector(s);
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function load(){
 const res=await fetch('/api/jobs'),jobs=await res.json();
 $('#total').textContent=jobs.length;
 $('#strong').textContent=jobs.filter(j=>j.match>=70).length;
 $('#progress').textContent=jobs.filter(j=>['Applied','Interview','Follow-up'].includes(j.status)).length;
 const q=$('#search').value.toLowerCase();
 const filtered=jobs.filter(j=>(j.title+' '+j.company+' '+j.location+' '+j.description).toLowerCase().includes(q));
 $('#jobs').innerHTML=filtered.length?filtered.map(j=>`<article class="job">
 <div class="jobtop"><div><h3>${esc(j.title)}</h3><div class="muted">${esc(j.company||'Company not specified')} · ${esc(j.location||'Location not specified')} · ${esc(j.source)}</div></div><div class="score">${j.match}% match</div></div>
 <p class="muted">Matched skills: ${j.matched_skills.map(esc).join(', ')||'No profile keywords found yet'}</p>
 <div class="jobfoot"><span class="muted">Status: ${esc(j.status)}</span><div>${j.url?`<a href="${esc(j.url)}" target="_blank" rel="noopener">Open listing ↗</a> · `:''}
 <select aria-label="Application status" onchange="setStatus(${j.id},this.value)">${['New','Shortlisted','Applied','Interview','Rejected','Not suitable'].map(s=>`<option ${s===j.status?'selected':''}>${s}</option>`).join('')}</select></div></div></article>`).join(''):'<div class="empty">No matching jobs yet. Add a listing above to start your tracker.</div>';
}
async function setStatus(id,status){await fetch('/api/jobs/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});load()}
$('#jobForm').addEventListener('submit',async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));const r=await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(r.ok){e.target.reset();load()}else alert((await r.json()).error||'Could not add job')});
$('#search').addEventListener('input',load);load();