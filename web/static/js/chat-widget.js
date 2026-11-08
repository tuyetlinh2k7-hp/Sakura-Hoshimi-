/* Sakura floating chat widget — 2 tab: Sakura AI + Global (cần login) */
(function(){
  function getToken(){return localStorage.getItem('sakura_auth_token')|| (document.cookie.match(/sakura_token=([^;]+)/)||[])[1]||''}
  function createWidget(){
    if(document.getElementById('sakuraChatFab')) return;
    const fab=document.createElement('button');
    fab.id='sakuraChatFab'; fab.className='chat-fab'; fab.setAttribute('aria-label','Mở chat');
    fab.innerHTML='💬<span class="chat-badge" id="chatBadge" style="display:none">1</span>';
    const widget=document.createElement('div');
    widget.id='sakuraChatWidget'; widget.className='chat-widget';
    widget.innerHTML=`
      <div class="chat-widget-header" style="flex-direction:column;gap:8px;align-items:stretch">
        <div style="display:flex;justify-content:space-between;align-items:center"><div style="display:flex;gap:8px;align-items:center"><span>🌸</span><strong>Sakura Chat</strong></div><button class="chat-widget-close" aria-label="Đóng">✕</button></div>
        <div style="display:flex;gap:6px;background:rgba(0,0,0,0.15);padding:4px;border-radius:10px">
          <button id="chatTabAI" class="chat-tab active" style="flex:1;padding:6px 8px;border-radius:8px;border:none;background:rgba(255,255,255,0.9);color:#d81b60;font-weight:700;cursor:pointer">🌸 Sakura AI</button>
          <button id="chatTabGlobal" class="chat-tab" style="flex:1;padding:6px 8px;border-radius:8px;border:none;background:transparent;color:#fff;font-weight:600;cursor:pointer">💬 Global</button>
        </div>
      </div>
      <div class="chat-messages" id="chatMessages"><div class="chat-bubble bot">Xin chào! Mình là Sakura 🌸 — chọn tab Global để chat với mọi người (cần đăng nhập) nhé!<div class="chat-time">${new Date().toLocaleTimeString('vi-VN')}</div></div></div>
      <div class="chat-input-bar"><input id="chatInput" class="chat-input" placeholder="Nhập tin nhắn Sakura AI..." autocomplete="off"><button id="chatSend" class="chat-send">➤</button></div>
      <div id="chatGlobalHint" style="display:none;padding:6px 10px;font-size:.75rem;color:var(--text-dim);text-align:center;border-top:1px solid var(--border-subtle)"><a href="/login" style="color:var(--sakura-pink);font-weight:600">Đăng nhập</a> để chat Global</div>`;
    document.body.appendChild(fab); document.body.appendChild(widget);
    const msgs=document.getElementById('chatMessages'), input=document.getElementById('chatInput'), send=document.getElementById('chatSend'), close=widget.querySelector('.chat-widget-close'), badge=document.getElementById('chatBadge'), tabAI=document.getElementById('chatTabAI'), tabGlobal=document.getElementById('chatTabGlobal'), hint=document.getElementById('chatGlobalHint');
    let mode='ai', unread=0, wsGlobal=null, globalLoaded=false;
    function toggle(open){
      const isOpen = open!==undefined? open : !widget.classList.contains('open');
      widget.classList.toggle('open', isOpen); if(isOpen){ badge.style.display='none'; unread=0; input.focus(); setTimeout(()=> msgs.scrollTop=msgs.scrollHeight,100); if(mode==='global') connectGlobal(); }
    }
    fab.addEventListener('click', ()=> toggle());
    close.addEventListener('click', ()=> toggle(false));
    function setMode(m){
      mode=m;
      tabAI.classList.toggle('active', m==='ai'); tabGlobal.classList.toggle('active', m==='global');
      tabAI.style.background=m==='ai'?'rgba(255,255,255,0.9)':'transparent'; tabAI.style.color=m==='ai'?'#d81b60':'#fff';
      tabGlobal.style.background=m==='global'?'rgba(255,255,255,0.9)':'transparent'; tabGlobal.style.color=m==='global'?'#d81b60':'#fff';
      input.placeholder=m==='ai'?'Nhập tin nhắn Sakura AI...':'Nhập tin nhắn Global... (cần login)';
      msgs.innerHTML='';
      if(m==='ai'){
        hint.style.display='none';
        append('Xin chào! Mình là Sakura 🌸 — hỏi gì mình cũng trả lời nhé!','bot');
        input.disabled=false; send.disabled=false;
      } else {
        const t=getToken();
        if(!t){ hint.style.display='block'; msgs.innerHTML='<div class="chat-bubble bot">Cần <a href="/login" style="color:var(--sakura-pink)">đăng nhập</a> để dùng Global Chat giữa các tài khoản 🌸</div>'; input.disabled=true; send.disabled=true; return; }
        hint.style.display='none'; input.disabled=false; send.disabled=false;
        msgs.innerHTML='<div class="chat-bubble bot">Đang tải Global Chat...</div>';
        loadGlobalHistory(); connectGlobal();
      }
      msgs.scrollTop=msgs.scrollHeight;
    }
    tabAI.addEventListener('click', ()=> setMode('ai'));
    tabGlobal.addEventListener('click', ()=> setMode('global'));
    function append(text, who='user', meta=''){
      const div=document.createElement('div'); div.className='chat-bubble '+who;
      const time=new Date().toLocaleTimeString('vi-VN');
      if(who==='global'){
        // text đã là HTML an toàn từ server (username + message)
        div.innerHTML=text+`<div class="chat-time">${meta}</div>`;
      } else {
        div.innerHTML=`${escapeHtml(text)}<div class="chat-time">${meta||time}</div>`;
      }
      msgs.appendChild(div); msgs.scrollTop=msgs.scrollHeight;
      if(!widget.classList.contains('open')){ unread++; badge.textContent=unread; badge.style.display='flex'; }
    }
    function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
    function appendGlobal(m){
      const isMe = m.username===(window._sakuraMe||'');
      const time = m.time||'';
      const wrap=document.createElement('div');
      wrap.style.cssText=`display:flex;flex-direction:column;gap:4px;max-width:82%;align-self:${isMe?'flex-end':'flex-start'}`;
      const head=document.createElement('div');
      head.style.cssText='display:flex;gap:8px;align-items:center';
      head.innerHTML=`<img src="${m.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:22px;height:22px;border-radius:50%;object-fit:cover;border:1px solid var(--border-subtle)" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'"><strong style="font-size:.82rem">${escapeHtml(m.username)}</strong><span style="font-size:.7rem;color:var(--text-dim)">${escapeHtml(time)}</span>`;
      const bubble=document.createElement('div');
      bubble.className='chat-bubble '+(isMe?'user':'bot');
      bubble.style.maxWidth='100%';
      bubble.textContent=m.message;
      wrap.appendChild(head); wrap.appendChild(bubble);
      msgs.appendChild(wrap); msgs.scrollTop=msgs.scrollHeight;
      if(!widget.classList.contains('open')){ unread++; badge.textContent=unread; badge.style.display='flex'; }
    }
    async function loadGlobalHistory(){
      const t=getToken(); if(!t) return;
      try{
        const r=await fetch('/api/global-chat',{headers:{'Authorization':'Bearer '+t}});
        const j=await r.json();
        msgs.innerHTML='';
        if(j.ok && j.messages.length){ j.messages.slice(-30).forEach(m=> appendGlobal(m)); }
        else append('Chưa có tin nhắn Global nào — hãy là người đầu tiên!','bot');
        // lấy tên mình
        try{ const me=await fetch('/api/auth/me',{headers:{'Authorization':'Bearer '+t}}); const mj=await me.json(); if(mj.ok) window._sakuraMe=mj.user.username; }catch{}
      }catch{ append('Lỗi tải Global Chat','bot'); }
    }
    function connectGlobal(){
      if(wsGlobal && wsGlobal.readyState===WebSocket.OPEN) return;
      const t=getToken(); if(!t) return;
      if(!globalLoaded){ globalLoaded=true; }
      const proto=location.protocol==='https:'?'wss:':'ws:';
      const url=`${proto}//${location.host}/ws/global-chat?token=${t}`;
      wsGlobal=new WebSocket(url);
      wsGlobal.onmessage=e=>{ try{ const j=JSON.parse(e.data); if(j.type==='global_chat'&&j.data){ appendGlobal(j.data); } }catch{} };
      wsGlobal.onclose=()=> setTimeout(()=>{ if(mode==='global' && widget.classList.contains('open')) connectGlobal(); },3000);
    }
    async function sendMsg(){
      const text=input.value.trim(); if(!text) return;
      if(mode==='ai'){
        append(text,'user'); input.value='';
        const typing=document.createElement('div'); typing.className='chat-bubble bot'; typing.id='typing'; typing.innerHTML='Sakura đang gõ<span class="dots">...</span>'; msgs.appendChild(typing); msgs.scrollTop=msgs.scrollHeight;
        try{
          const t=getToken(); const headers={'Content-Type':'application/json'}; if(t) headers['Authorization']='Bearer '+t;
          const r=await fetch('/api/chat',{method:'POST',headers, body: JSON.stringify({message:text})});
          const j=await r.json().catch(()=>({}));
          document.getElementById('typing')?.remove();
          if(j.ok && j.reply) append(j.reply,'bot'); else append(j.error||'Xin lỗi, chưa trả lời được. Thử lại nhé!','bot');
        }catch(e){ document.getElementById('typing')?.remove(); append('Lỗi kết nối: '+e.message,'bot'); }
      } else {
        // global
        const t=getToken(); if(!t){ showToast&&showToast('Cần đăng nhập để chat Global','warning'); return; }
        input.value='';
        if(wsGlobal && wsGlobal.readyState===WebSocket.OPEN){
          wsGlobal.send(JSON.stringify({type:'global_chat',message:text}));
        } else {
          try{ const r=await fetch('/api/global-chat',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+t}, body: JSON.stringify({message:text})}); const j=await r.json(); if(!j.ok) append(j.error||'Lỗi','bot'); }catch(e){ append('Lỗi: '+e.message,'bot'); }
        }
      }
    }
    send.addEventListener('click', sendMsg);
    input.addEventListener('keydown', e=>{ if(e.key==='Enter') sendMsg(); });
    if(!localStorage.getItem('sakura_chat_hint')){
      setTimeout(()=>{ if(!widget.classList.contains('open')){ badge.textContent='1'; badge.style.display='flex'; }}, 4000);
      localStorage.setItem('sakura_chat_hint','1');
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', createWidget); else createWidget();
})();
