#!/bin/bash

# Usage: ./click_google_result.sh "part of result title"
TARGET_TEXT="$1"

if [ -z "$TARGET_TEXT" ]; then
  echo "Usage: $0 \"partial title text\""
  exit 1
fi

coords=$(osascript <<EOF
tell application id "com.google.Chrome"
  set js to "
  (function () {
    var TARGET_TEXT = '$TARGET_TEXT';

    // Find all <h3> titles inside <a> links (typical Google result titles)
    var titles = Array.from(document.querySelectorAll('a h3'));

    var title = titles.find(function(h3) {
      return h3.innerText.toLowerCase().includes(TARGET_TEXT.toLowerCase());
    });

    if (!title) return '';

    var link = title.closest('a');
    if (!link) return '';

    var rect = link.getBoundingClientRect();
    var winX = window.screenX;
    var winY = window.screenY;
    var chromeHeight = window.outerHeight - window.innerHeight;

    var x = Math.round(winX + rect.left + rect.width / 2);
    var y = Math.round(winY + chromeHeight + rect.top + rect.height / 2);

    return x + ',' + y;
  })();
  "
  set res to execute javascript js in active tab of front window
end tell
return res
EOF
)

if [ -z "$coords" ]; then
  echo "Link containing '$TARGET_TEXT' not found."
  exit 1
fi

echo "Clicking at $coords"
cliclick "c:$coords"
