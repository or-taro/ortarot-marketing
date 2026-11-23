// 이미 있는 글(공개·예약)의 본문·제목·태그를 새 원고로 바꾼다. 발행일 그대로, 예약 글은 p.at으로 예약 유지.
const NAME='__NAME__',SHA='__SHA__';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
for(let i=0;i<40&&!(window.tinymce&&tinymce.activeEditor&&tinymce.activeEditor.getBody()&&document.getElementById('tagText'));i++) await sleep(300);
await sleep(800);
const p=await fetch(`https://raw.githubusercontent.com/or-taro/ortarot-marketing/${SHA}/blog/posts/${NAME}.json`).then(r=>r.json());
const ed=tinymce.activeEditor;const toks=[];
for(const [i,u0] of p.images.entries()){const u=u0.replace('/main/',`/${SHA}/`);
  const blob=await fetch(u).then(r=>r.blob());const dt=new DataTransfer();dt.items.add(new File([blob],`${NAME}_${i+1}.jpg`,{type:'image/jpeg'}));
  ed.setContent('');ed.getBody().dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));
  let m=null;for(let k=0;k<50&&!m;k++){await sleep(300);m=ed.getContent().match(/\[##_Image\|[^\]]*?_##\]/);}
  if(!m) throw new Error('upload failed '+i);
  toks.push(p.alts&&p.alts[i]?m[0].replace(/\}_##\]$/,`,"alt":"${p.alts[i]}"}_##]`):m[0]);}
let h=p.html;toks.forEach((t,i)=>{h=h.replace(`{{IMG${i+1}}}`,'<p>'+t+'</p>');});
if(/\{\{IMG/.test(h)) throw new Error('placeholder left');
ed.setContent(h);ed.undoManager.add();ed.fire('change');ed.fire('input');ed.nodeChanged();await sleep(800);
const t=document.getElementById('post-title-inp');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t,p.title);t.dispatchEvent(new Event('input',{bubbles:true}));
// 태그: 기존 칩 지우고 새로
for(let k=0;k<20;k++){const del=[...document.querySelectorAll('button,a,span')].find(e=>/태그 삭제/.test(e.textContent)&&e.offsetParent);if(!del)break;del.click();await sleep(80);}
const inp=document.getElementById('tagText');const sv=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
for(const tg of p.tags){inp.focus();sv.call(inp,tg);inp.dispatchEvent(new Event('input',{bubbles:true}));for(const ty of ['keydown','keypress','keyup'])inp.dispatchEvent(new KeyboardEvent(ty,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));await sleep(100);}
{const img=ed.getBody().querySelector('img');const r=img.getBoundingClientRect();
 for(const ty of ['mouseover','mouseenter','mousemove','mousedown','mouseup','click'])img.dispatchEvent(new MouseEvent(ty,{bubbles:true,cancelable:true,clientX:r.x+50,clientY:r.y+50,view:ed.getWin()}));
 await sleep(500);const rb=document.querySelector('.mce-represent-image-btn');if(!rb) throw new Error('no represent btn');
 if(!rb.classList.contains('active')) for(const ty of ['mousedown','mouseup','click'])rb.dispatchEvent(new MouseEvent(ty,{bubbles:true,cancelable:true}));
 await sleep(400);if(!rb.classList.contains('active')) throw new Error('represent not set');}
[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='완료').click();await sleep(1000);
document.getElementById('open20').click();await sleep(200);
if(p.at&&new Date(p.at.replace(' ','T')+':00+09:00')>new Date()){
const sv2=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
[...document.querySelectorAll('button.btn_date')].find(b=>b.textContent.trim()==='예약').click();await sleep(400);
const [d,tm]=p.at.split(' ');const [Y,M,D]=d.split('-').map(Number);const [hh,mm]=tm.split(':');
if(!document.querySelector('.box_calendar')||!document.querySelector('.box_calendar').offsetParent){document.querySelector('.btn_reserve').click();await sleep(400);}
for(let i=0;i<14;i++){if(document.querySelector('.txt_calendar').textContent.trim()===`${Y}년 ${M}월`)break;document.querySelector('.box_calendar .btn_next').click();await sleep(250);}
const day=[...document.querySelectorAll('.tbl_calendar .btn_day')].find(b=>b.textContent.trim()===String(D)&&!b.disabled);if(!day) throw new Error('no day');day.click();await sleep(300);
for(const [id,v] of [['dateHour',hh],['dateMinute',mm]]){const e=document.getElementById(id);e.focus();sv2.call(e,v);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.dispatchEvent(new Event('blur',{bubbles:true}));}
await sleep(300);const chk=[document.querySelector('.btn_reserve').textContent.trim(),document.getElementById('dateHour').value,document.getElementById('dateMinute').value];
if(chk[0]!==d||chk[1]!==hh||chk[2]!==mm) throw new Error('date mismatch '+chk.join(' '));}
if(!document.querySelector('.box_thumb .thumb_g')) throw new Error('no thumbnail');
if(ed.getContent().length<4000) throw new Error('content too short '+ed.getContent().length);
document.getElementById('publish-btn').click();
return 'updated '+NAME;
