use std::sync::Mutex;
use std::net::TcpStream;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct SidecarState(Mutex<Option<CommandChild>>);

impl Drop for SidecarState {
    fn drop(&mut self) {
        if let Ok(mut child) = self.0.lock() {
            if let Some(child) = child.take() {
                let _ = child.kill();
            }
        }
    }
}

fn sidecar_port_open() -> bool {
    TcpStream::connect_timeout(&"127.0.0.1:8766".parse().expect("valid sidecar address"), Duration::from_millis(250)).is_ok()
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if sidecar_port_open() {
                app.manage(SidecarState(Mutex::new(None)));
            } else {
                let (_rx, child) = app
                    .shell()
                    .sidecar("selene-sidecar")?
                    .args(["--seed", "--port", "8766"])
                    .spawn()?;
                app.manage(SidecarState(Mutex::new(Some(child))));
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Selene vessel");
}
