use std::io::Write;
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread::sleep;
use std::time::Duration;
use tauri::Manager;

struct SidecarState(Mutex<Option<Child>>);

impl SidecarState {
    fn stop(&self) {
        if let Ok(mut child) = self.0.lock() {
            if let Some(mut child) = child.take() {
                request_sidecar_shutdown();
                sleep(Duration::from_millis(500));
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

impl Drop for SidecarState {
    fn drop(&mut self) {
        self.stop();
    }
}

fn sidecar_port_open() -> bool {
    TcpStream::connect_timeout(
        &"127.0.0.1:8766".parse().expect("valid sidecar address"),
        Duration::from_millis(250),
    )
    .is_ok()
}

fn stop_stale_sidecars() {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;

        for image_name in [
            "selene-sidecar.exe",
            "selene-sidecar-x86_64-pc-windows-msvc.exe",
        ] {
            let _ = Command::new("taskkill")
                .args(["/F", "/IM", image_name])
                .creation_flags(CREATE_NO_WINDOW)
                .output();
        }

        let _ = Command::new("powershell")
            .args([
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "$ownerPids = @(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); foreach ($ownerPid in $ownerPids) { Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue }",
            ])
            .creation_flags(CREATE_NO_WINDOW)
            .output();
        sleep(Duration::from_millis(750));
    }
}

fn sidecar_executable() -> std::io::Result<PathBuf> {
    let exe_dir = std::env::current_exe()?
        .parent()
        .map(PathBuf::from)
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "missing app exe directory"))?;
    let current_dir = std::env::current_dir()?;
    let candidates = [
        exe_dir.join("selene-sidecar.exe"),
        exe_dir.join("selene-sidecar-x86_64-pc-windows-msvc.exe"),
        current_dir.join("dist-sidecar").join("selene-sidecar.exe"),
        current_dir
            .join("dist-sidecar")
            .join("selene-sidecar-x86_64-pc-windows-msvc.exe"),
        current_dir
            .join("src-tauri")
            .join("target")
            .join("release")
            .join("selene-sidecar.exe"),
    ];

    candidates
        .into_iter()
        .find(|path| path.exists())
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "selene sidecar executable not found"))
}

fn spawn_hidden_sidecar(parent_pid: &str) -> std::io::Result<Child> {
    let mut command = Command::new(sidecar_executable()?);
    command
        .args(["--seed", "--port", "8766", "--parent-pid", parent_pid])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    command.spawn()
}

fn request_sidecar_shutdown() {
    let address = "127.0.0.1:8766";
    if let Ok(mut stream) = TcpStream::connect_timeout(
        &address.parse().expect("valid sidecar address"),
        Duration::from_millis(500),
    ) {
        let _ = stream.set_write_timeout(Some(Duration::from_secs(2)));
        let request = concat!(
            "POST /shutdown HTTP/1.1\r\n",
            "Host: 127.0.0.1:8766\r\n",
            "Content-Type: application/json\r\n",
            "Content-Length: 2\r\n",
            "Connection: close\r\n",
            "\r\n",
            "{}"
        );
        let _ = stream.write_all(request.as_bytes());
    }
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if sidecar_port_open() {
                request_sidecar_shutdown();
                sleep(Duration::from_millis(250));
                stop_stale_sidecars();
            }
            let parent_pid = std::process::id().to_string();
            let child = spawn_hidden_sidecar(parent_pid.as_str())?;
            app.manage(SidecarState(Mutex::new(Some(child))));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let state = window.state::<SidecarState>();
                state.stop();
                stop_stale_sidecars();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Selene vessel");
}
