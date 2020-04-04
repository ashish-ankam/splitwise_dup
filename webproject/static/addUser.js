function remove() {
    "use strict";
    var x = this.parentNode;
    x.parentNode.removeChild(x.nextSibling);
    x.removeChild(this);
    x.parentNode.removeChild(x);
}

function changeColor() {
    "use strict";
    this.style.backgroundColor="white";
}

function addTask() {
    "use strict";
    var task, list_ele, list, x_butt;   
    task = document.getElementById("new_task");
    list = document.getElementById("ul");
    
    list_ele = document.createElement('li');
    list_ele.addEventListener("click", changeColor);
    x_butt = document.createElement('span');
    x_butt.appendChild(document.createTextNode("\u00D7"));
    x_butt.className = "close";
    x_butt.addEventListener("click", remove);
    list_ele.appendChild(document.createTextNode(task.value));
    list.appendChild(list_ele);
    list_ele.appendChild(x_butt);
    list.appendChild(document.createElement('br')); 
}
