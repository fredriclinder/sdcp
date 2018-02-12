// Tools created using javascript
//
// Version: 17.11.17GA
// Author:  Zacharias El Banna
// 

//
// Button functions - accepts proper JScript object:
//  Set attribute log=true to log operation
//
// - [load]   div url [spin=true/div] [msg = for confirmation] [frm = if doing a post] [input = True if populating input]
// - redirect url
// - iload    iframe url
// - logout   url/div
// - toggle   div
// - hide     div
// - single   div select
// - empty    div
// - submit   frm
//

function btn(e) {
 var op  = $(this).attr("op");
 var div = $("#"+$(this).attr("div"));
 var url = $(this).attr("url");
 var log = $(this).attr("log");

 if (log)
  console.log("Log OP:"+op);

 if (!op || op == 'load') {
  if (this.getAttribute("msg") && !confirm(this.getAttribute("msg"))) return;
  var spin = this.getAttribute("spin");
  if (spin){
    spin = (spin.toLowerCase() == 'true') ? div : $("#"+spin);
    spin.scrollTop(0);
    spin.css("overflow-y","hidden");
    spin.append("<DIV CLASS='overlay'><DIV CLASS='loader'></DIV></DIV>");
  }
  var frm  =  this.getAttribute("frm");
  var input = this.getAttribute("input");
  if(frm)
   $.post(url, $("#"+frm).serializeArray() , function(result) { loadresult(div,spin,input,result);  });
  else
   $.get(url, function(result) { loadresult(div,spin,input,result); });

 } else if (op == 'redirect') {
  location.replace(url);
 } else if (op == 'submit') {
  $("#"+ this.getAttribute("frm")).submit();
 } else if (op == 'iload') {
  $("#"+ this.getAttribute("iframe")).attr('src',url);
 } else if (op == 'logout') {
  if (this.getAttribute("cookie")) {
   console.log('Expiring cookie:' + this.getAttribute("cookie"));
   document.cookie = this.getAttribute("cookie") + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
  } else {
   var cookies = document.cookie.split("; ");
   for(var i=0; i < cookies.length; i++) {
    var equals = cookies[i].indexOf("=");
    var name = equals > -1 ? cookies[i].substr(0, equals) : cookies[i];
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
   }
  }
  if(url)
   location.replace(url);
  else
   div.html('');
 } else if (op == 'single') {
  $(this.getAttribute("selector")).hide();
  div.show();
 } else if (op == 'toggle') {
  div.toggle();
 } else if (op == 'hide') {
  div.hide();
 } else if (op == 'empty') {
  div.html('');
 }
};

//
// Callback for loading result
//
function loadresult(div,spin,input,result){
 if (input)
  div.val(result);
 else
  div.html(result);
 if (spin) {
  $(".overlay").remove();
  spin.css("overflow-y","auto");
 }
}

//
//
function focus(e){
 if (e.originalEvent.type == 'focus')
  $(this).addClass('highlight');
 else if (e.originalEvent.type == 'blur')
  $(this).removeClass('highlight');
};

//
// Drag-n'-drop
// - updating a list of element id's on attribute "dest" on drop element
//
function dragndrop(){
 $(".drag").off();
 $(".drop").off();
 $(".drag").attr("draggable","true");
 $(".drag").on("dragstart", dragstart);
 $(".drag").on("dragend", dragend);
 $(".drop").on("dragover", dragover);
 $(".drop").on("drop", drop);
 $(".drop").on("dragenter", dragenter);
 $(".drop").on("dragleave", dragleave);
}

//
function dragend(e){
 this.style.opacity = '';
}

//
function dragstart(e){
 console.log("Drag " + this.id + " FROM " + this.parentElement.id);
 this.style.opacity = '0.4';
 e.originalEvent.dataTransfer.setData("Text",this.id);
 e.originalEvent.dataTransfer.effectAllowed = 'move';
}

//
function dragover(e){
 if(e.preventDefault)
  e.preventDefault();
 return false;
}
function dragenter(e){ this.classList.add('highlight'); }
function dragleave(e){ this.classList.remove('highlight'); }

//
function drop(e){
 e.preventDefault();
 var el_id = e.originalEvent.dataTransfer.getData("Text");
 var el    = document.getElementById(el_id);
 var parent= el.parentElement;
 this.appendChild(el);
 console.log("Drop " + el_id + " INTO " + this.id + " FROM " + parent.id);
 updatelist(this);
 updatelist(parent);
 this.classList.remove('highlight');
}

//
function updatelist(obj){
 var list = [];
 for (i = 0; i < obj.children.length; i++){ list.push(obj.children[i].id); }
 $("#" + obj.getAttribute("dest")).attr("value",list);
}
