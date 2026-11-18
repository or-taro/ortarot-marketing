const NAME='__NAME__';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
for(let i=0;i<40&&!(window.tinymce&&tinymce.activeEditor&&tinymce.activeEditor.getBody()&&document.getElementById('tagText'));i++) await sleep(300);
const p=await fetch('https://raw.githubusercontent.com/or-taro/ortarot-marketing/main/blog/posts/'+NAME+'.json?t='+Date.now()).then(r=>r.json());
const ed=tinymce.activeEditor;const toks=[];
for(const [i,u] of p.images.entries()){
  const blob=await fetch(u+'?t='+Date.now()).then(r=>r.blob());
  const dt=new DataTransfer();dt.items.add(new File([blob],`${NAME}_${i+1}.jpg`,{type:'image/jpeg'}));
  ed.setContent('');ed.getBody().dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));
  let m=null;for(let k=0;k<50&&!m;k++){await sleep(300);m=ed.getContent().match(/\[##_Image\|[^\]]*?_##\]/);}
  if(!m) throw new Error('upload failed '+i);
  toks.push(p.alts&&p.alts[i]?m[0].replace(/\}_##\]$/,`,"alt":"${p.alts[i]}"}_##]`):m[0]);
}
let h=p.html;toks.forEach((t,i)=>{h=h.replace(`{{IMG${i+1}}}`,'<p>'+t+'</p>');});
if(/\{\{IMG/.test(h)) throw new Error('placeholder left');
ed.setContent(h);await sleep(800);
{const img=ed.getBody().querySelector('img');const r=img.getBoundingClientRect();
 for(const ty of ['mouseover','mouseenter','mousemove','mousedown','mouseup','click'])img.dispatchEvent(new MouseEvent(ty,{bubbles:true,cancelable:true,clientX:r.x+50,clientY:r.y+50,view:ed.getWin()}));
 await sleep(500);const rb=document.querySelector('.mce-represent-image-btn');if(!rb) throw new Error('no represent btn');
 if(!rb.classList.contains('active')) for(const ty of ['mousedown','mouseup','click'])rb.dispatchEvent(new MouseEvent(ty,{bubbles:true,cancelable:true}));
 await sleep(400);if(!rb.classList.contains('active')) throw new Error('represent not set');}
const t=document.getElementById('post-title-inp');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t,p.title);t.dispatchEvent(new Event('input',{bubbles:true}));
document.getElementById('category-btn').click();await sleep(400);document.getElementById('category-item-1439947').click();await sleep(300);
const inp=document.getElementById('tagText');const sv=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
for(const tg of p.tags){inp.focus();sv.call(inp,tg);inp.dispatchEvent(new Event('input',{bubbles:true}));for(const ty of ['keydown','keypress','keyup'])inp.dispatchEvent(new KeyboardEvent(ty,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));await sleep(100);}
[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='완료').click();await sleep(1000);
document.getElementById('open20').click();await sleep(200);
[...document.querySelectorAll('button.btn_date')].find(b=>b.textContent.trim()==='예약').click();await sleep(400);
const [d,tm]=p.at.split(' ');const [Y,M,D]=d.split('-').map(Number);const [hh,mm]=tm.split(':');
if(!document.querySelector('.box_calendar')||!document.querySelector('.box_calendar').offsetParent){document.querySelector('.btn_reserve').click();await sleep(400);}
for(let i=0;i<14;i++){if(document.querySelector('.txt_calendar').textContent.trim()===`${Y}년 ${M}월`)break;document.querySelector('.box_calendar .btn_next').click();await sleep(250);}
const day=[...document.querySelectorAll('.tbl_calendar .btn_day')].find(b=>b.textContent.trim()===String(D)&&!b.disabled);if(!day) throw new Error('no day');day.click();await sleep(300);
for(const [id,v] of [['dateHour',hh],['dateMinute',mm]]){const e=document.getElementById(id);e.focus();sv.call(e,v);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.dispatchEvent(new Event('blur',{bubbles:true}));}
await sleep(300);
const chk=[document.querySelector('.btn_reserve').textContent.trim(),document.getElementById('dateHour').value,document.getElementById('dateMinute').value];
if(chk[0]!==d||chk[1]!==hh||chk[2]!==mm) throw new Error('date mismatch '+chk.join(' '));
if(!document.querySelector('.box_thumb .thumb_g')) throw new Error('no thumbnail');
document.getElementById('publish-btn').click();
return 'submitted '+NAME+' '+p.at;
