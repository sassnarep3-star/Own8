
document.querySelectorAll('input.filter').forEach(function(inp){
  inp.addEventListener('input',function(){
    var t=document.getElementById(inp.dataset.target); if(!t) return;
    var q=inp.value.toLowerCase();
    Array.prototype.forEach.call(t.tBodies[0].rows,function(r){
      r.style.display = r.textContent.toLowerCase().indexOf(q)>-1 ? '' : 'none';
    });
  });
});
