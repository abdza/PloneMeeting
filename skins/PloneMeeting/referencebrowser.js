// function to open the popup window
function referencebrowser_openBrowser(path, fieldName, at_url, fieldRealName) {
  if (window.screen) {
    var w = window.screen.availWidth - 100;
    var h = window.screen.availHeight - 100;
    var left = parseInt((window.screen.availWidth/2) - (w/2));
    var top = parseInt((window.screen.availHeight/2) - (h/2));
  }
  else {
    var w = 700;
    var h = 550;
    var left = 50;
    var top = 50;
  }
  var windowAttrs = 'width=' + w + ',height=' + h + ',left=' +
    left + ',top=' + top + ',screenX=' + left + ',screenY=' + top +
    ',toolbar=no,menubar=no,scrollbars=yes,status=no,resizable=yes';
  // Popup will appear at the center of the screen
  atrefpopup = window.open(path + '/referencebrowser_popup?fieldName=' +
    fieldName + '&fieldRealName=' + fieldRealName +'&at_url=' + at_url,
    'referencebrowser_popup', windowAttrs);
}

// function to return a reference from the popup window back into the widget
function referencebrowser_setReference(widget_id, uid, label, multi)
{
    // differentiate between the single and mulitselect widget
    // since the single widget has an extra label field.
    if (multi==0) {
        element=document.getElementById(widget_id)
        label_element=document.getElementById(widget_id + '_label')
        element.value=uid
        label_element.value=label
     }  else {
         list=document.getElementById(widget_id)
         // check if the item isn't already in the list
          for (var x=0; x < list.length; x++) {
            if (list[x].value == uid) {
              return false;
            }
          }         
          // now add the new item
          theLength=list.length;
          list[theLength] = new Option(label);
          list[theLength].selected='selected';
          list[theLength].value=uid
     }
}

// function to clear the reference field or remove items
// from the multivalued reference list.
function referencebrowser_removeReference(widget_id, multi)
{
    if (multi) {
        list=document.getElementById(widget_id)
        for (var x=list.length-1; x >= 0; x--) {
          if (list[x].selected) {
            list[x]=null;
          }
        }
        for (var x=0; x < list.length; x++) {
            list[x].selected='selected';
          }        
    } else {
        element=document.getElementById(widget_id);
        label_element=document.getElementById(widget_id + '_label');
        label_element.value = "";
        element.value="";
    }
}


