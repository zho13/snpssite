var main = function() {

	/* for check box and description box synchronization */

	// clicking on checkbox displays corresponding box of info
	$('input[type="checkbox"]').click(function(){
		cur_btn = "." + $(this).attr("value");
		$(cur_btn).toggle();
	});

	// clicking the "x" closes the box and unchecks the corresponding checkbox
	$('.close').click(function() {
		$(this).parents('.info').toggle();
		var button = $(this).parents('.info').attr("value");
		$('input[type="checkbox"][value="' + button + '"]').prop('checked', false);
	});
	$(".close").click(function(){
      $(".instr").hide();
    });

}

$(document).ready(main);