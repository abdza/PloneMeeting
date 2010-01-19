/* Dropdown for selecting an annex type */
var ploneMeetingSelectBoxes = new Object();

function displayPloneMeetingSelectBox(selectName) {
  var box = document.getElementById(ploneMeetingSelectBoxes[selectName]["box"]);
  var button = document.getElementById(ploneMeetingSelectBoxes[selectName]["button"]);
  if (box.style.display!="block") {
    /* Button seems pressed */
    button.style.borderStyle = "inset";
    box.style.display = "block";
  }
  else {
    button.style.borderStyle = "outset";
    box.style.display= "none";
  }
}

function hidePloneMeetingSelectBox(selectName, idImage, msg, value, predefined_title) {
  var newImage = document.getElementById(idImage);

  var btnImage = document.getElementById(ploneMeetingSelectBoxes[selectName]["image"])
  var btnText = document.getElementById(ploneMeetingSelectBoxes[selectName]["buttonText"])

  document.getElementById(ploneMeetingSelectBoxes[selectName]["button"]).style.borderStyle = "outset";
  document.getElementById(ploneMeetingSelectBoxes[selectName]["box"]).style.display="none";
  btnText.innerHTML = msg;

  // Display
  btnImage.src = newImage.src;
  document.getElementById(ploneMeetingSelectBoxes[selectName]["hidden"]).value = value;
  document.annexForm.annex_title.value = predefined_title
}

function ploneMeetingSelectOnMouseOverItem(obj) {
  /* Set the "selected" style */
  obj.className = "ploneMeetingSelectItem ploneMeetingSelectItemUnselected";
}

function ploneMeetingSelectOnMouseOutItem(obj) {
  /* Set the default style  (unselected) */
  obj.className = "ploneMeetingSelectItem";
}

/* Function that, on the Annexes form, shows a popup that asks the user if he
   really wants to delete an annex. */
function confirmDeleteObject(theElement, objectType){
    var msg = window.plonemeeting_delete_confirm_message;
    if (objectType == 'wholeMeeting') {
      msg = window.plonemeeting_delete_meeting_confirm_message;
    }
    if (confirm(msg)) {
       theElement.parentNode.submit()
    }
}

/* The functions below are derived from Plone's dropdown.js for using a dropdown
   menu that is specific to the bock of icons showing annexes.
 * This is the code for the dropdown menus. It uses the following markup:
 *
 * <dl class="actionMenuAX" id="uniqueIdForThisMenu">
 *   <dt class="actionMenuHeaderAX">
 *     <!-- The following a-tag needs to be clicked to dropdown the menu -->
 *     <a href="some_destination">A Title</a>
 *   </dt>
 *   <dd class="actionMenuContentAX">
 *     <!-- Here can be any content you want -->
 *   </dd>
 * </dl>
 *
 * When the menu is toggled, then the dl with the class actionMenu will get an
 * additional class which switches between 'activated' and 'deactivated'.
 * You can use this to style it accordingly, for example:
 *
 * .actionMenuAX.activated {
 *   display: block;
 * }
 *
 * .actionMenuAX.deactivated {
 *   display: none;
 * }
 *
 * When you click somewhere else than the menu, then all open menus will be
 * deactivated. When you move your mouse over the a-tag of another menu, then
 * that one will be activated and all others deactivated. When you click on a
 * link inside the actionMenuContent element, then the menu will be closed and
 * the link followed.
 *
 * This file uses functions from register_function.js, cssQuery.js and
 * nodeutils.js.
 *
 */
function isAnnexMenu(node) {
    if (hasClassName(node, 'contentActionsAX')) {
        return true;
    }
    return false;
};

/* When several menubars are present on a page, when a menu is shown in a
   menubar, it may be displayed under another menu bar. This function solves
   this problem by assigning a special style "onTop" with a high z-style
   value to the menubar currently displayed.
*/
function bringForward(elem) {
    /* Put backward all annexes groups and popups
       (excepted the current one) */
    var annexGroups = cssQuery('div.contentActionsAX');
    var currentAnnexGroup = findContainer(elem, isAnnexMenu);
    for (var i=0; i < annexGroups.length; i++) {
        if (annexGroups[i] == currentAnnexGroup){
            removeClassName(annexGroups[i], 'onBottom')
            addClassName(annexGroups[i], 'onTop')
        }
        else {
            removeClassName(annexGroups[i], 'onTop')
            addClassName(annexGroups[i], 'onBottom')
        }
    }
}

function isActionMenuAX(node) {
    if (hasClassName(node, 'actionMenuAX')) {
        return true;
    }
    return false;
};

function hideAllMenusAX(node) {
    var menus = cssQuery('dl.actionMenuAX', node);
    for (var i=0; i < menus.length; i++) {
        replaceClassName(menus[i], 'activated', 'deactivated', true);
    }
};

function toggleMenuHandlerAX(event) {
    if (!event) var event = window.event; // IE compatibility

    // terminate if we hit a non-compliant DOM implementation
    // returning true, so the link is still followed
    if (!W3CDOM){return true;}

    var container = findContainer(this, isActionMenuAX);
    if (!container) {
        return true;
    }

    // check if the menu is visible
    if (hasClassName(container, 'activated')) {
        // it's visible - hide it
        replaceClassName(container, 'activated', 'deactivated', true);
    } else {
        // it's invisible - make it visible (and hide all others)
        hideAllMenusAX()
        bringForward(this);
        replaceClassName(container, 'deactivated', 'activated', true);
    }

    return false;
};

function hideMenusHandlerAX(event) {
    if (!event) var event = window.event; // IE compatibility

    hideAllMenusAX();

    // we want to follow this link
    return true;
};

function actionMenuDocumentMouseDownAX(event) {
    if (!event) var event = window.event; // IE compatibility

    if (event.target)
        targ = event.target;
    else if (event.srcElement)
        targ = event.srcElement;

    var container = findContainer(targ, isActionMenuAX);
    if (container) {
        // targ is part of the menu, so just return and do the default
        return true;
    }

    hideAllMenusAX();

    return true;
};

function actionMenuMouseOverAX(event) {
    if (!event) var event = window.event; // IE compatibility

    if (!this.tagName && (this.tagName == 'A' || this.tagName == 'a')) {
        return true;
    }

    var container = findContainer(this, isActionMenuAX);
    if (!container) {
        return true;
    }
    var menu_id = container.id;

    var switch_menu = false;
    // hide all menus
    var menus = cssQuery('dl.actionMenuAX');
    for (var i=0; i < menus.length; i++) {
        var menu = menus[i]
        // check if the menu is visible
        if (hasClassName(menu, 'activated')) {
            switch_menu = true;
        }
        // turn off menu when it's not the current one
        if (menu.id != menu_id) {
            replaceClassName(menu, 'activated', 'deactivated', true);
        }
    }

    if (switch_menu) {
        var menu = cssQuery('#'+menu_id)[0];
        if (menu) {
            bringForward(this);
            replaceClassName(menu, 'deactivated', 'activated', true);
        }
    }

    return true;
};

function initializeMenusAXStartingAt(node) {
  // Initializes menus starting at a given node in the page.
  // First, terminate if we hit a non-compliant DOM implementation
  if (!W3CDOM) {return false;}
  document.onmousedown = actionMenuDocumentMouseDownAX;
  hideAllMenusAX(node);

  // Add toggle function to header links
  var menu_headers = cssQuery('dl.actionMenuAX > dt.actionMenuHeaderAX > a', node);
  for (var i=0; i < menu_headers.length; i++) {
    var menu_header = menu_headers[i];
    menu_header.onclick = toggleMenuHandlerAX;
  }
  // Add hide function to all links in the dropdown, so the dropdown closes
  // when any link is clicked
  var menu_contents = cssQuery('dl.actionMenuAX > dd.actionMenuContentAX', node);
  for (var i=0; i < menu_contents.length; i++) {
    menu_contents[i].onclick = hideMenusHandlerAX;
  }
}

function initializeMenusAX() {
  initializeMenusAXStartingAt(document);
};

registerPloneFunction(initializeMenusAX);

var wrongTextInput = '#ff934a none';
function gotoItem(inputWidget, totalNbOfItems, meetingUid) {
  // Go to meetingitem_view for the item whose number is in p_inputWidget
  try {
    var itemNumber = parseInt(inputWidget.value);
    if (!isNaN(itemNumber)) {
      if ((itemNumber>=1) && (itemNumber<=totalNbOfItems)) {
        var theForm = document.forms["formGotoItem"];
        theForm.objectId.value = itemNumber;
        theForm.meetingUid.value = meetingUid;
        theForm.submit();
      }
      else inputWidget.style.background = wrongTextInput;
    }
    else inputWidget.style.background = wrongTextInput;
  }
  catch (err) { inputWidget.style.background = wrongTextInput; }
}

function computeStartNumberFrom(itemNumber, totalNbOfItems, batchSize) {
  // Here, we compute the start number of the batch where to find the item
  // whose number is p_itemNumber.
  var startNumber = 1;
  var res = startNumber;
  while (startNumber <= totalNbOfItems) {
    if (itemNumber < startNumber + batchSize) {
      res = startNumber;
      break;
    }
    else startNumber += batchSize;
  }
  return res;
}

// Function that, depending on parameter mustShow, shows or hides the descriptions.
function setDescriptionsVisiblity(mustShow) {
  // First, update every description of every item
  var pmDescriptions = cssQuery('#pmDescription');
  for (var i=0; i<pmDescriptions.length; i++) {
    var elem = pmDescriptions[i];
    if (mustShow) { // Show the descriptions
      addClassName(elem, 'pmExpanded');
      elem.style.display = 'inline';
    }
    else { // Hide the descriptions
      removeClassName(elem, 'pmExpanded');
      elem.style.display = 'none';
    }
  }
  // Then, change the action icon and update the cookie
  var tdIcon = document.getElementById('icon-toggleDescriptions');
  if (mustShow) {
    tdIcon.src = 'collapseDescrs.png';
    createCookie('pmShowDescriptions', 'true');
  }
  else {
    tdIcon.src = 'expandDescrs.png';
    createCookie('pmShowDescriptions', 'false');
  }
};

// Function that toggles the descriptions visibility
function toggleMeetingDescriptions() {
  if (readCookie('pmShowDescriptions') == 'true') setDescriptionsVisiblity(false);
  else setDescriptionsVisiblity(true);
};
