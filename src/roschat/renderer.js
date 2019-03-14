const {ipcRenderer} = require('electron');

document.body.onblur = function() {
    ipcRenderer.send('body-focus', false);
};

document.body.onfocus = function() {
    ipcRenderer.send('body-focus', true);
};
