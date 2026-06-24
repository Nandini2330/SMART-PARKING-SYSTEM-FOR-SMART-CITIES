console.log('Smart Parking (AJAX)');

// Auto refresh slots every 10 seconds
setInterval(function(){
    if(typeof refreshSlots === 'function') refreshSlots();
},10000);

function searchVehicle(){
    const q = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('table tbody tr').forEach(row=>{
        const v = (row.children[3].innerText||'').toLowerCase();
        row.style.display = v.indexOf(q) > -1 ? '' : 'none';
    });
}

function filterSlots(){
    // kept for dashboard search compatibility
    const q = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('#slotContainer .card').forEach(card=>{
        const slot = card.getAttribute('data-slot-number') || '';
        const vehicle = card.getAttribute('data-vehicle') || '';
        const owner = card.getAttribute('data-owner') || '';
        const text = `${slot} ${vehicle} ${owner}`.toLowerCase();
        card.parentElement.style.display = text.indexOf(q) > -1 ? '' : 'none';
    });
}