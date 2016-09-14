var main = function() {
	$('input[type="checkbox"]').click(function(){
		cur_btn = $(this).attr("value");
		cur_btn.toggle();
	});
	$('.close').click(function() {
		$(this).parents('.info').toggle();
		var button = $(this).parents('.info').attr("value");
		$('input[type="checkbox"][value="' + button + '"]').prop('checked', false);
	});
}

$(document).ready(main);