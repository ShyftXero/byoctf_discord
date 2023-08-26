function addSpoilerTags() {
	const tableRows = document.querySelectorAll('tr');  // Replace 'tr' with the actual selector of your rows
  
	tableRows.forEach((row) => {
	  const cells = row.querySelectorAll('td');  // Replace 'td' with the actual selector of your cells
  
	  cells.forEach((cell) => {
		const content = cell.innerHTML;
		const newContent = content.replace(/FLAG{[^}]+}/g, '<span class="spoiler">FLAG{hidden}</span>');
  
		if (content !== newContent) {
		  cell.innerHTML = newContent;
		}
	  });
	});
  }
  
  // Run addSpoilerTags every 1 second (1000 milliseconds)
  setInterval(addSpoilerTags, 1000);
   
