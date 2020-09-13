$(document).ready(function(){
    $('.signup-content').fadeOut();
    $('.panel-to-slide').css('background-image','linear-gradient(to right, #ef462e , #ef462e)');
});

// click events
$('.custom-login').on('click',function(){
    $('.panel-to-slide').addClass('right-log');
    $('.panel-to-slide').css('background-image','linear-gradient(to right, #ef404b , #ef3b61)');
    $('.login-content').css('display','none');
    $('.login-content').fadeOut();
    $('.signup-content').fadeIn();

})

$('.custom-signup').on('click',function(){
    $('.panel-to-slide').removeClass('right-log');
    $('.panel-to-slide').css('background-image','linear-gradient(to right, #ef462e , #ef462e)');
    $('.signup-content').css('display','none');
    $('.signup-content').fadeOut();
    $('.login-content').fadeIn();

})

//contact form validation
  $('input').click(function(){
    $('#email').removeClass("error");
    $('#password').removeClass("error");
    $('#reg_name').removeClass("error");
    $('#reg_email').removeClass("error");
    $('#reg_password').removeClass("error");
  });

function validate(val_form){
  if (val_form=='in') {

    if ($('#email').val()=="") {
      $('#email').addClass( "error" );
      return false;
    }else if ($('#password').val()=="") {
      $('#password').addClass( "error" );
      return false;
    }else{
      alert('Login Successful');
    }

  }else{

      if ($('#reg_name').val()=="") {
        $('#reg_name').addClass( "error" );
        return false;
      }else if ($('#reg_email').val()=="") {
        $('#reg_email').addClass( "error" );
        return false;
      }else if ($('#reg_password').val()=="") {
        $('#reg_password').addClass( "error" );
        return false;
      }else{
        alert('Sign-up Successful'); 
      }

  }
}