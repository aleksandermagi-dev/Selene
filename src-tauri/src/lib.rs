use std::io::{Read, Write};
use std::net::TcpStream;
use std::process::Command;
use std::sync::Mutex;
use std::thread::sleep;
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

fn sidecar_compatible() -> bool {
    let address = "127.0.0.1:8766".parse().expect("valid sidecar address");
    let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(500)) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(750)));
    let request = b"GET /health HTTP/1.1\r\nHost: 127.0.0.1:8766\r\nConnection: close\r\n\r\n";
    if stream.write_all(request).is_err() {
        return false;
    }
    let mut response = String::new();
    if stream.read_to_string(&mut response).is_err() {
        return false;
    }
    response.contains("\"status\": \"ok\"")
        && response.contains("\"continuity_calibration\"")
        && response.contains("\"sidecar_version\"")
}

fn stop_stale_sidecars() {
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("taskkill")
            .args(["/F", "/IM", "selene-sidecar.exe"])
            .output();
        sleep(Duration::from_millis(750));
    }
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if sidecar_compatible() {
                app.manage(SidecarState(Mutex::new(None)));
            } else {
                if sidecar_port_open() {
                    stop_stale_sidecars();
                }
                let parent_pid = std::process::id().to_string();
                let (_rx, child) = app
                    .shell()
                    .sidecar("selene-sidecar")?
                    .args(["--seed", "--port", "8766", "--parent-pid", parent_pid.as_str()])
                    .spawn()?;
                app.manage(SidecarState(Mutex::new(Some(child))));
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Selene vessel");
}
