const electron = require('electron');
const {app, Menu, Tray, BrowserWindow, ipcMain} = require('electron');
const path = require('path');
let mainWindow = null;

let tray = null;

console.log(`Platform: ${process.platform}`);

ipcMain.on('test', console.log);

app.on('ready', () => {
    if (process.platform === 'linux') tray = new Tray(path.join(__dirname,'./img/roschat5.png'));
    else tray = new Tray(path.join(__dirname,'../img/roschat5.ico'));
    // 
  const contextMenu = Menu.buildFromTemplate([
      { label: 'Выход', type: 'normal', click: () => process.exit(0) }

  ]);
    tray.setToolTip('Росчат');
    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    });
    
    // tray.on('click', () => {console.log('click')});
    // tray.on('double-click', () => {
    //     console.log('double-click');
    //     mainWindow.show();
    // });
    // tray.on('right-click', () => {console.log('right-click')});
    // contextMenu.items[1].on('click', () => {'item-click'});
});


app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('ready', () => {
    const { width, height } = electron.screen.getPrimaryDisplay().workAreaSize;
    mainWindow = new BrowserWindow({
        width: Math.round(width*0.8),
        height: Math.round(height*0.8),
        icon: path.join(__dirname,'./img/roschat5.png'),
        backgroundThrottling: false
    });
    mainWindow.on('show', () => {
        tray.setHighlightMode('always');
    });
    mainWindow.on('hide', () => {
        tray.setHighlightMode('never');
    });
    // mainWindow.webContents.openDevTools();
    mainWindow.loadURL(path.join('file://', __dirname,'/wlan.html'));
    // mainWindow.on('closed', function() {
    //     mainWindow = null;
    // });
    mainWindow.on('close', function (event) {
        if(!app.isQuiting){
            event.preventDefault();
            mainWindow.hide();
        }

        return false;
    });
});


//Отключаю проверку сертификатов для поддержки самоподписных сертификатов
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    event.preventDefault();
    callback(true);
});

