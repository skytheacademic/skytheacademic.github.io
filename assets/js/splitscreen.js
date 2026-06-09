/* Split-screen redesign - behavior: mesh + two-axis research explorer */
(function () {
  'use strict';
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  (function mesh() {
    var c = document.getElementById('mesh');
    if (!c || !c.getContext) return;
    var ctx = c.getContext('2d');
    function size(){ c.width=c.clientWidth; c.height=c.clientHeight; }
    size(); window.addEventListener('resize', size);
    var N=24, pts=[];
    for (var k=0;k<N;k++) pts.push({x:Math.random(),y:Math.random(),vx:(Math.random()-0.5)*0.0005,vy:(Math.random()-0.5)*0.0005});
    function draw(move){
      var W=c.width,H=c.height; if(!W){size();W=c.width;H=c.height;if(!W)return;}
      ctx.clearRect(0,0,W,H);
      if(move) pts.forEach(function(p){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>1)p.vx*=-1;if(p.y<0||p.y>1)p.vy*=-1;});
      for(var i=0;i<N;i++)for(var j=i+1;j<N;j++){var a=pts[i],b=pts[j],dx=(a.x-b.x)*W,dy=(a.y-b.y)*H,d=Math.sqrt(dx*dx+dy*dy);
        if(d<140){ctx.strokeStyle='rgba(8,24,48,'+(0.55*(1-d/140))+')';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(a.x*W,a.y*H);ctx.lineTo(b.x*W,b.y*H);ctx.stroke();}}
      pts.forEach(function(p){ctx.fillStyle='rgba(210,178,104,0.6)';ctx.beginPath();ctx.arc(p.x*W,p.y*H,1.7,0,7);ctx.fill();});
    }
    if(prefersReduced){requestAnimationFrame(function(){size();draw(false);});}
    else {(function frame(){draw(true);requestAnimationFrame(frame);})();}
  })();

  (function research() {
    var grid=document.getElementById('grid'); if(!grid) return;
    var tabs=[].slice.call(document.querySelectorAll('#tabs button'));
    var clearBtn=document.getElementById('clear');
    var cards=[].slice.call(grid.querySelectorAll('.card'));
    var current='', lastKey=null;
    function matches(c){ return current==='' || (' '+c.dataset.topic+' ').indexOf(' '+current+' ')>-1; }
    function applyFilter(){
      if(current===lastKey) return; lastKey=current;
      var shownNow=cards.filter(function(c){return c.style.display!=='none';});
      var first=new Map(); shownNow.forEach(function(c){first.set(c,c.getBoundingClientRect());});
      var willLeave=shownNow.filter(function(c){return !matches(c);});
      willLeave.forEach(function(c){c.classList.add('leaving');});
      setTimeout(function(){
        willLeave.forEach(function(c){c.style.display='none';c.classList.remove('leaving');});
        var newlyEnter=cards.filter(function(c){return matches(c)&&c.style.display==='none';});
        cards.forEach(function(c){if(matches(c))c.style.display='';});
        var staying=cards.filter(function(c){return c.style.display!=='none'&&first.has(c);});
        staying.forEach(function(c){
          var last=c.getBoundingClientRect(),fr=first.get(c);var dx=fr.left-last.left,dy=fr.top-last.top;
          if(dx||dy){c.style.transform='translate('+dx+'px,'+dy+'px)';c.classList.remove('flip-move');
            requestAnimationFrame(function(){c.classList.add('flip-move');c.style.transform='';});
            c.addEventListener('transitionend',function(){c.classList.remove('flip-move');},{once:true});}
        });
        newlyEnter.forEach(function(c,i){c.classList.add('entering');
          requestAnimationFrame(function(){setTimeout(function(){c.classList.add('enter-active');},60+i*70);});
          setTimeout(function(){c.classList.remove('entering','enter-active');},60+i*70+460);});
      }, willLeave.length?180:0);
    }
    function setFilter(f){
      if(f===current) f='';
      current=f;
      tabs.forEach(function(t){ t.classList.toggle('on', current!=='' && t.dataset.f===current); });
      if(clearBtn) clearBtn.hidden = (current==='');
      applyFilter();
    }
    tabs.forEach(function(t){ t.addEventListener('click',function(){ setFilter(t.dataset.f); }); });
    if(clearBtn) clearBtn.addEventListener('click',function(){ setFilter(''); });
    function toggleCard(c){ var w=c.classList.contains('open'); cards.forEach(function(x){x.classList.remove('open');}); if(!w)c.classList.add('open'); }
    cards.forEach(function(c){ c.setAttribute('tabindex','0'); c.setAttribute('role','button');
      c.addEventListener('click',function(e){ if(e.target.closest('.links a'))return; toggleCard(c); });
      c.addEventListener('keydown',function(e){ if(e.target.closest('.links a'))return; if(e.key==='Enter'||e.key===' '){e.preventDefault();toggleCard(c);} }); });
  })();

  (function fieldshow(){
    var shows=[].slice.call(document.querySelectorAll('.fieldshow'));
    if(!shows.length) return;
    var reduce=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    shows.forEach(function(el){
      var imgs=(el.getAttribute('data-imgs')||'').split(',').map(function(s){return s.trim();}).filter(Boolean);
      var img=el.querySelector('img'); if(!img||!imgs.length) return;
      var dotsWrap=el.nextElementSibling;
      if(dotsWrap && !dotsWrap.classList.contains('fsdots')) dotsWrap=null;
      var i=0, dots=[], t=null;
      function paint(){ for(var k=0;k<dots.length;k++) dots[k].classList.toggle('on', k===i); }
      function set(n){ i=(n+imgs.length)%imgs.length;
        if(reduce){ img.src=imgs[i]; }
        else { img.style.opacity='0'; var pre=new Image(); pre.onload=function(){ img.src=imgs[i]; img.style.opacity='1'; }; pre.src=imgs[i]; }
        paint(); }
      function play(){ if(imgs.length>1) t=setInterval(function(){ set(i+1); },5000); }
      function reset(){ if(t) clearInterval(t); play(); }
      if(dotsWrap){ imgs.forEach(function(_,k){ var b=document.createElement('button'); b.className='fsdot'; b.type='button'; b.setAttribute('aria-label','Show item '+(k+1)); b.addEventListener('click',function(){ set(k); reset(); }); dotsWrap.appendChild(b); dots.push(b); }); }
      set(0); play();
    });
  })();
})();
