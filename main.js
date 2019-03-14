const {app, BrowserWindow} = require('electron');
const path = require('path');
let mainWindow = null;

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('ready', () => {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600
    });
    mainWindow.loadURL(path.join('file://', __dirname, 'dist/','/wlan.html'));
    mainWindow.on('closed', function() {
        mainWindow = null;
    });
});


//Отключаю проверку сертификатов для поддержки самоподписных сертификатов
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    event.preventDefault();
    callback(true);
});
