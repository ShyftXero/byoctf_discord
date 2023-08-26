function addSpoilerTags() {
	const tableRows = document.querySelectorAll('tr');  // Replace 'tr' with the actual selector of your rows
  
	tableRows.forEach((row) => {
	  const cells = row.querySelectorAll('td');  // Replace 'td' with the actual selector of your cells
  
	  cells.forEach((cell) => {
		const content = cell.innerHTML;
		const regex = /FLAG{[^}]+}/g;
		let newContent = content;
		let match;
		
		while (match = regex.exec(content)) {
		  const spoilerTag = `<span class="spoiler" onclick="revealSpoiler(this)">[Click to reveal]</span><span class="hidden-flag" style="display:none;">${match[0]}</span>`;
		  newContent = newContent.replace(match[0], spoilerTag);
		}
  
		if (content !== newContent) {
		  cell.innerHTML = newContent;
		}
	  });
	});
  }
  
  function revealSpoiler(element) {
	const hiddenFlag = element.nextElementSibling;
	hiddenFlag.style.display = 'inline';
	element.style.display = 'none';
  }
  
  // Run addSpoilerTags every 1 second (1000 milliseconds)
  setInterval(addSpoilerTags, 1000);
  