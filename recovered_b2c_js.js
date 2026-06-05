function switchB2CTab(tabName, event) {


<truncated 7985 bytes>
             renderB2CHotelResults(data.hotels);

} else {

container.innerHTML = `

<div style="text-align: center; color: #64748b; padding: 60px 0; grid-column: 1 / -1;">

<i class="fa-solid fa-circle-exclamation" style="font-size: 40px; color: #ef4444; margin-bottom: 15px;"></i>

<p style="font-size: 16px; font-weight: 600;">No hotels found matching "${location}".</p>

<p style="font-size: 14px; margin-top: 5px; color: #94a3b8;">Try searching for 'London', 'Dubai', or 'Maldives'.</p>

</div>

`;

}

})

.catch(err => {

console.error("Hotel search error:", err);

container.innerHTML = `

<div style="text-align: center; color: #64748b; padding: 60px 0; grid-column: 1 / -1;">

<i class="fa-solid fa-triangle-exclamation" style="font-size: 40px; color: #ef4444; margin-bottom: 15px;"></i>

<p style="font-size: 16px; font-weight: 600;">An error occurred while searching for hotels.</p>

</div>

`;

});

}



function renderB2CHotelResults(hotels) {

const container = document.getElementById("b2c-hotel-results-container");

container.innerHTML = "";



hotels.forEach(h => {

let starsHTML = "";

for (let i = 0; i < h.rating; i++) {

The above content does NOT show the entire file contents. If you need to view any lines of the file which were not shown to complete your task, call this tool again to view those lines.
