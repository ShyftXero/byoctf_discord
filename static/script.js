function addSpoilerTags() {
	const tableRows = document.querySelectorAll('tr');  
  
	tableRows.forEach((row) => {
	  const cells = row.querySelectorAll('td');  
  
	  cells.forEach((cell) => {
		let content = cell.innerHTML;
  
		const newContent = content.replace(/(?!<span class="spoiler">)FLAG{[^}]+}(?!<\/span>)/g, '<span class="spoiler">$&</span>');
		
		if (content !== newContent) {
		  cell.innerHTML = newContent;
		}
	  });
	});
  }
  
  document.addEventListener("mouseover", function(event) {
	if (event.target.classList.contains('spoiler')) {
	  event.target.style.color = "white"; 
	}
  });
  

  document.addEventListener("mouseout", function(event) {
	if (event.target.classList.contains('spoiler')) {
	  event.target.style.color = "black"; 
	}
  });

  setInterval(addSpoilerTags, 1000);
  