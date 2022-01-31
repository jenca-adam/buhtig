
	var navlis=document.querySelectorAll('nav ul li');
	navlis.forEach(function(me){
		if(me.querySelector('a').getAttribute('href')===window.location.pathname){
			me.className='active';
			};
		}
	)
