'use strict';
document.querySelectorAll('.table-tools').forEach(tools => {
 const input=tools.querySelector('input');
 const table=tools.nextElementSibling.querySelector('table');
 const rows=[...table.tBodies[0].rows];
 input.addEventListener('input',()=>{
  const q=input.value.toLocaleLowerCase().trim(); let visible=0;
  rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase().includes(q); if(!row.hidden)visible++;});
  tools.querySelector('.row-count').textContent=`${visible} / ${rows.length} rows`;
 });
});
