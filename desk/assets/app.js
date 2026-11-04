'use strict';
const input=document.querySelector('input[type="search"]');
const status=document.getElementById('filter-status');
if(input){input.addEventListener('input',()=>{const query=input.value.trim().toLocaleLowerCase();let visible=0;const rows=document.querySelectorAll('tbody tr');rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase().includes(query);if(!row.hidden)visible++;});status.textContent=query?`${visible} of ${rows.length} table rows match. Clear search to show all rows.`:'';});}
