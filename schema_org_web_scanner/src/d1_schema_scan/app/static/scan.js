let scanSocket;
let doScroll = true;
let scanId_;

function connectSocket(scanId) {
  scanId_ = scanId;

  let protocol = window.location.host.startsWith("127.0.0.1") ? "ws" : "wss";

  scanSocket = new WebSocket(
      protocol + '://' + window.location.host +
      '/ws/' + scanId + '/');

  scanSocket.onmessage = function (e) {
    const msg_dict = JSON.parse(e.data);

    if ('log_line_list' in msg_dict) {
      add_log_line_list(msg_dict['log_line_list']);
    }

    if ('scan_completed' in msg_dict) {
      $("#end_ts").text(msg_dict["scan_end"]);
      $("#exit_code").text(msg_dict["exit_code"]);
      // $("#but-stop-scan").addClass('round-button-disabled');
      // $("#but-stop-scan").css('pointer-events', 'none');
      $("#but-stop-scan").text('View', 'none');
    }

    scrollToBottom();
  };

  scanSocket.onclose = function (e) {
    // console.log('scanSocket closed');
  };
}

function add_log_line_list(log_line_list) {
  log_line_list.forEach(function (item, index) {
    let el = document.createElement("div");
    if (item.includes('ERROR')) {
      el.className = 'log-err';
    }
    else if (item.includes('WARN')) {
      el.className = 'log-warn';
    }
    let node = document.createTextNode(item);
    el.appendChild(node);
    document.getElementById("scan-log").appendChild(el);
  });
}

function closeSocket() {
  // scanSocket.close()
}

function scrollToBottom() {
  if (doScroll) {
    const scrollingElement = (document.scrollingElement || document.body);
    scrollingElement.scrollTop = scrollingElement.scrollHeight;
  }
}

function toTop() {
  doScroll = false;
  const scrollingElement = (document.scrollingElement || document.body);
  scrollingElement.scrollTop = 0;
}

function copy_to_clipboard() {
  let el = document.getElementById("scan-uuid");
  el.select();
  document.execCommand('copy');
  window.close()
}

function doubleenc(v) {
  return encodeURIComponent(encodeURIComponent(v))
}

$(document).ready( function() {
  $(function () {
    $("form").submit(function (event) {
      const url_input = $("#url-input").val();
      const format_id = $("#format-id-input").val();
      let enc_url = doubleenc(url_input);
      console.log('');
      console.log(url_input);
      console.log(format_id);
      if(typeof format_id === "undefined") {
        console.log('sitemap');
        window.location.href = '../new/sitemap/' + enc_url + '/';
      }
      else {
        console.log('xmlschema');
        window.location.href = '../new/xmlschema/' + enc_url + '/' + doubleenc(format_id) + '/'
      }
      event.preventDefault();
    });
  });
});
