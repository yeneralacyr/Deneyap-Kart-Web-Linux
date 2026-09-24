var serialMonitorOpen = false;
window.responseWaiting = false;
window.Alert = new CustomAlert();
window.alertClosed = false;
window.connectionActive = false;

function mainWebsocket() {
  if ("WebSocket" in window) {
    window.mainWs = new WebSocket("ws://localhost:49182");

    window.mainWs.onopen = function () {
      getVersion();
      getCoreVersion();
      closePopup2();
      refreshBoards();
    };

    window.mainWs.onmessage = function (evt) {
      messageParser(evt.data);
    };

    window.mainWs.onclose = function () {
      window.connectionActive = false;
      document.getElementById("port").innerHTML = "";
    };
  } else {
    alert("WebSocket NOT supported by your Browser!");
  }
}

function serialWebsocket() {
  if ("WebSocket" in window) {
    window.serialWs = new WebSocket("ws://localhost:49183");
    window.responseWaiting = false;

    window.serialWs.onopen = function () {};

    window.serialWs.onmessage = function (evt) {
      messageParser(evt.data);
    };

    window.serialWs.onclose = function () {
      closeSerialMonitor();
    };
  } else {
    alert("WebSocket NOT supported by your Browser!");
  }
}

function messageParser(received_msg) {
  var body = JSON.parse(received_msg);
  if (body.command == "cleanConsoleLog") {
    var textArea = document.getElementById("consoleLog");
    textArea.replaceChildren();
    var txt = document.createTextNode(body.log);
    textArea.appendChild(txt);
  }
  if (body.command == "cleanSerialLog") {
    var textArea = document.getElementById("serialLog");
    textArea.replaceChildren();
    var txt = document.createTextNode(body.log);
    textArea.appendChild(txt);
  }

  if (body.command == "consoleLog") {
    var textArea = document.getElementById("consoleLog");
    var txt = document.createTextNode(body.log);
    textArea.appendChild(txt);
    document.getElementById("consoleLog").scrollTop =
      document.getElementById("consoleLog").scrollHeight;
  }

  if (body.command == "serialLog") {
    var textArea = document.getElementById("serialLog");
    var txt = document.createTextNode(body.log);
    textArea.appendChild(txt);
    document.getElementById("serialLog").scrollTop =
      document.getElementById("serialLog").scrollHeight;
  }

  if (body.command == "response") {
    window.responseWaiting = false;
  }

  if (body.command == "closeSerialMonitor") {
    closeSerialMonitor();
  }

  if (body.command == "returnBoards") {
    window.responseWaiting = false;
    document.getElementById("port").innerHTML = "";
    for (var i = body.boards.length - 1; i >= 0; i--) {
      const newOption = document.createElement("option");
      newOption.value = body.boards[i].port;
      newOption.text =
        body.boards[i].port + "(" + body.boards[i].boardName + ")";
      document.getElementById("port").appendChild(newOption);
    }
  }

  if (body.command == "returnVersion") {
    if (body.version != getLastVersion()) {
      openVersionPopup();
    }
  }

  if (body.command == "returnCoreVersion") {
    document.getElementById("coreVersionSelect").value = body.version;
  }

  if (body.command == "versionChangeStatus") {
    versionChangeStatus(body.success);
  }

  if (body.command == "searchLibraryResult") {

    var libraries = JSON.parse(body.libraries);
    if ("libraries" in libraries) {
      libraries = libraries.libraries;
      libraries.sort((a, b) => (a.name > b.name ? 1 : -1));
      createList(libraries);
    } else {
      $("#libraryCards").html("");
    }
  }

  if (body.command == "downloadLibraryResult") {
    var textArea = document.getElementById("consoleLog");
    var txt = document.createTextNode(body.result);
    textArea.appendChild(txt);
  }
}

function getLastVersion() {
  return "1.0.2";
}

function getLastVersionLink() {
  return "DeneyapKartWebSetupv1.0.2.exe";
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function sendMessage(body, to) {
  body = JSON.stringify(body);
  var delay = 1500;

  if (to == "main") {
    window.responseWaiting = true;
    while (window.responseWaiting) {
      window.mainWs.send(body);
      await sleep(delay);
    }
  }

  if (to == "serial") {
    window.responseWaiting = true;
    while (window.responseWaiting) {
      window.serialWs.send(body);
      await sleep(delay);
    }
  }

  if (to == "both") {
    window.responseWaiting = true;
    while (window.responseWaiting) {
      window.serialWs.send(body);
      await sleep(delay);
    }

    window.responseWaiting = true;
    while (window.responseWaiting) {
      window.mainWs.send(body);
      await sleep(delay);
    }
  }
}
function uploadCode() {
  $("#toggleConsole").slideDown();
  $("#toggleSerial").slideUp();
  $("#toggle").slideUp();

  var selectedPort = document.getElementById("port").value;
  var selectedBoard = document.getElementById("boards").value;
  var textArea = document.getElementById("consoleLog");
  textArea.replaceChildren();
  var txt = document.createTextNode("Compiling Code...");
  textArea.appendChild(txt);
  var partition = document.getElementById("partitions").value;
  code = getCode();

  var uploadOptions = getOptions();

  body = {
    command: "upload",
    board: selectedBoard,
    port: selectedPort,
    code: code,
    uploadOptions: uploadOptions,
  };
  sendMessage(body, "both");
  closeSerialMonitor();
}
function compileCode() {
  $("#toggleConsole").slideDown();
  $("#toggleSerial").slideUp();
  $("#toggle").slideUp();

  var selectedPort = document.getElementById("port").value;
  var selectedBoard = document.getElementById("boards").value;
  var textArea = document.getElementById("consoleLog");
  textArea.replaceChildren();
  var txt = document.createTextNode("Compiling Code...");
  textArea.appendChild(txt);
  var partition = document.getElementById("partitions").value;

  var uploadOptions = getOptions();

  code = getCode();
  body = {
    command: "compile",
    board: selectedBoard,
    port: selectedPort,
    code: code,
    uploadOptions: uploadOptions,
  };
  sendMessage(body, "main");
}

function getVersion() {
  body = {
    command: "getVersion",
  };
  sendMessage(body, "main");
}

function getCoreVersion() {
  body = {
    command: "getCoreVersion",
  };
  sendMessage(body, "main");
}

function refreshBoards() {
  body = {
    command: "getBoards",
  };
  sendMessage(body, "main");
}

function toggleSerialMonitor() {
  document.getElementById("serialLog").replaceChildren();

  if (serialMonitorOpen == false) {
    openSerialMonitor();
  } else {
    closeSerialMonitor();
  }
}

function openSerialMonitor() {
  if (!serialMonitorOpen) {
    var selectedPort = document.getElementById("port").value;
    var selectedBaud = document.getElementById("baudRate").value;
    document.getElementById("serialLed").style.background = "green";
    body = {
      command: "openSerialMonitor",
      port: selectedPort,
      baudRate: selectedBaud,
    };
    serialMonitorOpen = true;
    sendMessage(body, "serial");
  }
}

function closeSerialMonitor() {
  if (serialMonitorOpen) {
    serialMonitorOpen = false;
    var selectedPort = document.getElementById("port").value;
    var selectedBaud = document.getElementById("baudRate").value;
    document.getElementById("serialLed").style.background = "gray";
    body = {
      command: "closeSerialMonitor",
      port: selectedPort,
      baudRate: selectedBaud,
    };
    sendMessage(body, "serial");
  }
}

function getCode() {
  var code = "";

  if (window.localStorage.content == "on") {
    spans = document.getElementById("pre_previewArduino").childNodes;
    for (var i = 0; i <= spans.length - 1; i++) {
      code += spans[i].innerText;
    }
  } else {
    code = editor.getValue();
  }

  return code;
}

function serialWrite() {
  var text = document.getElementById("serialWriteInput").value;
  if (text == "") return;
  body = {
    command: "serialWrite",
    text: text,
  };
  sendMessage(body, "serial");
}

function CustomAlert() {
  this.render = function () {
    let popUpBox = document.getElementById("popUpBox");
    popUpBox.style.display = "block";
  };
}

function closePopup() {
  document.getElementById("popUpBox").style.display = "none";
  window.alertClosed = true;
}

function closePopup2() {
  document.getElementById("popUpBox").style.display = "none";
  window.connectionActive = true;
}
function closePopup3() {
  document.getElementById("popUpBoxLoading").style.display = "none";
  window.connectionActive = true;
}

function closeVersionPopup() {
  document.getElementById("popUpBox2").style.display = "none";
}

function openVersionPopup() {
  document.getElementById("popUpBox2").style.display = "block";
}

function showDownload() {
  window.Alert.render();
}

function changeVersion() {
  body = {
    command: "changeVersion",
    version: document.getElementById("coreVersionSelect").value,
  };
  let popUpLoading = document.querySelector("#popUpBoxLoading");
  popUpLoading.style.display = "block";

  sendMessage(body, "main");
}

function versionChangeStatus(success) {
  if (success) {
    let loadingStatus = document.querySelector("#loadingStatus");
    loadingStatus.innerHTML = "Versiyon Değiştirme Başarılı";
    let qwqwqw = document.querySelector("#popUpBoxLoading #box div");
    qwqwqw.innerHTML = "<img src='./media/loadingdone.png' width='30px'>";

  } else {
    let loadingStatus = document.querySelector("#loadingStatus");
    loadingStatus.innerHTML = "Versiyon Değiştirme Başarısız";
    let qwqwqw = document.querySelector("#popUpBoxLoading #box div");
    qwqwqw.innerHTML = "<img src='./media/loadingerror.png' width='30px'>";
  }
  setTimeout(closePopup3, 2000);

}

function connections() {
  if (window.mainWs == undefined) {
    mainWebsocket();
    if (!window.alertClosed && !window.connectionActive) {
      showDownload();
    }
  } else if (window.mainWs.readyState == 3) {
    mainWebsocket();
    if (!window.alertClosed && !window.connectionActive) {
      showDownload();
    }
  }

  if (window.serialWs == undefined) {
    serialWebsocket();
  } else if (window.serialWs.readyState == 3) {
    serialWebsocket();
  }
}

function searchLibrary(searchTerm) {
  body = {
    command: "searchLibrary",
    searchTerm: searchTerm,
  };
  sendMessage(body, "main");
}

function downloadLibrary(libName, libVersion) {
  body = {
    command: "downloadLibrary",
    libName: libName,
    libVersion: libVersion,
  };
  sendMessage(body, "main");
}

connections();
setInterval(connections, 5000);
document.getElementById("downloadLink").href = getLastVersionLink();
document.getElementById("downloadLink2").href = getLastVersionLink();
