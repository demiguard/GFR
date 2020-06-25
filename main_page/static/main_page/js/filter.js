console.log('Hello World');

$(".delete_button").bind('click', function(){
  console.log(this.name)

  $("#Filter_" + this.name).remove();


  $.ajax({
    url: "api/procedure_mapping/" + this.name,
    type: 'DELETE',
    success: function(data){
      console.log(data);
    },
    error: function(data){
      console.log("ERROR");
      console.log(data);
    }
  });
});

