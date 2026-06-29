use std::fs::{create_dir_all, OpenOptions};
use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread::sleep;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tauri::Manager;

struct SidecarState(Mutex<Option<Child>>);

fn local_log_path(file_name: &str) -> PathBuf {
    if let Some(local) = std::env::var_os("LOCALAPPDATA") {
        return PathBuf::from(local)
            .join("Selene")
            .join("logs")
            .join(file_name);
    }
    std::env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join(".selene_logs")
        .join(file_name)
}

fn debug_log_path() -> PathBuf {
    local_log_path("transfer-ceremony-debug.log")
}

fn stabilization_log_path() -> PathBuf {
    local_log_path("system-stabilization-debug.log")
}

fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_else(|_| Duration::from_secs(0))
        .as_millis()
}

fn log_debug(source: &str, event: &str, detail: &str) {
    write_debug_log(debug_log_path(), source, event, detail);
}

fn log_stabilization_debug(source: &str, event: &str, detail: &str) {
    write_debug_log(stabilization_log_path(), source, event, detail);
}

fn write_debug_log(path: PathBuf, source: &str, event: &str, detail: &str) {
    if let Some(parent) = path.parent() {
        let _ = create_dir_all(parent);
    }
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let safe_detail = detail.replace('\r', "\\r").replace('\n', "\\n");
        let _ = writeln!(
            file,
            "{{\"ts_ms\":{},\"source\":\"{}\",\"event\":\"{}\",\"detail\":\"{}\"}}",
            now_ms(),
            source,
            event,
            safe_detail.replace('"', "\\\"")
        );
    }
}

#[tauri::command]
fn log_transfer_ceremony_event(event: String, detail: String) {
    log_debug("frontend", &event, &detail);
}

#[tauri::command]
fn log_stabilization_event(event: String, detail: String) {
    log_stabilization_debug("frontend", &event, &detail);
}

#[tauri::command]
fn read_transfer_ceremony_debug_log() -> String {
    std::fs::read_to_string(debug_log_path()).unwrap_or_default()
}

impl SidecarState {
    fn stop(&self) {
        log_debug("tauri", "sidecar_state_stop_called", "");
        if let Ok(mut child) = self.0.lock() {
            if let Some(mut child) = child.take() {
                let child_id = child.id();
                log_debug("tauri", "sidecar_owned_child_shutdown_start", &format!("pid={child_id}"));
                request_sidecar_shutdown();
                sleep(Duration::from_millis(500));
                let _ = child.kill();
                let _ = child.wait();
                log_debug("tauri", "sidecar_owned_child_shutdown_complete", &format!("pid={child_id}"));
            } else {
                log_debug("tauri", "sidecar_state_no_owned_child", "");
            }
        } else {
            log_debug("tauri", "sidecar_state_lock_failed", "");
        }
    }
}

impl Drop for SidecarState {
    fn drop(&mut self) {
        log_debug("tauri", "sidecar_state_drop", "");
        self.stop();
    }
}

fn sidecar_health_ok() -> bool {
    log_debug("tauri", "sidecar_health_check_start", "");
    let mut stream = match TcpStream::connect_timeout(
        &"127.0.0.1:8766".parse().expect("valid sidecar address"),
        Duration::from_millis(500),
    ) {
        Ok(stream) => stream,
        Err(err) => {
            log_debug("tauri", "sidecar_health_check_connect_failed", &err.to_string());
            return false;
        }
    };
    let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(2)));
    let request = concat!(
        "GET /health HTTP/1.1\r\n",
        "Host: 127.0.0.1:8766\r\n",
        "Connection: close\r\n",
        "\r\n"
    );
    if let Err(err) = stream.write_all(request.as_bytes()) {
        log_debug("tauri", "sidecar_health_check_write_failed", &err.to_string());
        return false;
    }
    let mut response = String::new();
    let ok = stream.read_to_string(&mut response).is_ok()
        && response.starts_with("HTTP/1.0 200")
        && response.contains("\"status\":\"ok\"");
    log_debug("tauri", "sidecar_health_check_complete", &format!("ok={ok}; bytes={}", response.len()));
    ok
}

fn sidecar_port_open() -> bool {
    TcpStream::connect_timeout(
        &"127.0.0.1:8766".parse().expect("valid sidecar address"),
        Duration::from_millis(250),
    )
    .is_ok()
}

fn wait_for_sidecar_port_close(timeout: Duration) -> bool {
    let mut waited = Duration::from_millis(0);
    while waited < timeout {
        if !sidecar_port_open() {
            return true;
        }
        sleep(Duration::from_millis(200));
        waited += Duration::from_millis(200);
    }
    !sidecar_port_open()
}

fn stop_stale_sidecars() {
    log_debug("tauri", "stop_stale_sidecars_start", "");
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
    log_debug("tauri", "stop_stale_sidecars_complete", "");
}

fn sidecar_executable(resource_dir: Option<PathBuf>) -> std::io::Result<PathBuf> {
    let exe_dir = std::env::current_exe()?
        .parent()
        .map(PathBuf::from)
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "missing app exe directory"))?;
    let current_dir = std::env::current_dir()?;
    let mut candidates = vec![];
    if let Some(resource_dir) = resource_dir {
        candidates.push(
            resource_dir
                .join("selene-sidecar")
                .join("selene-sidecar.exe"),
        );
        candidates.push(
            resource_dir
                .join("dist-sidecar")
                .join("selene-sidecar")
                .join("selene-sidecar.exe"),
        );
    }
    candidates.push(
        exe_dir
            .join("_up_")
            .join("dist-sidecar")
            .join("selene-sidecar")
            .join("selene-sidecar.exe"),
    );
    candidates.extend([
        exe_dir.join("selene-sidecar.exe"),
        exe_dir.join("selene-sidecar").join("selene-sidecar.exe"),
        exe_dir.join("selene-sidecar-x86_64-pc-windows-msvc.exe"),
        current_dir
            .join("dist-sidecar")
            .join("selene-sidecar")
            .join("selene-sidecar.exe"),
        current_dir.join("dist-sidecar").join("selene-sidecar.exe"),
        current_dir
            .join("dist-sidecar")
            .join("selene-sidecar-x86_64-pc-windows-msvc.exe"),
        current_dir
            .join("src-tauri")
            .join("target")
            .join("release")
            .join("selene-sidecar.exe"),
    ]);

    candidates
        .into_iter()
        .find(|path| path.exists())
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "selene sidecar executable not found"))
}

fn spawn_hidden_sidecar(parent_pid: &str, resource_dir: Option<PathBuf>) -> std::io::Result<Child> {
    let exe = sidecar_executable(resource_dir)?;
    log_debug("tauri", "sidecar_spawn_start", &format!("exe={}; parent_pid={parent_pid}", exe.display()));
    let mut command = Command::new(exe);
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

    let child = command.spawn();
    match &child {
        Ok(child) => log_debug("tauri", "sidecar_spawn_complete", &format!("pid={}", child.id())),
        Err(err) => log_debug("tauri", "sidecar_spawn_failed", &err.to_string()),
    }
    child
}

fn request_sidecar_shutdown() {
    log_debug("tauri", "sidecar_shutdown_request_start", "");
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
        log_debug("tauri", "sidecar_shutdown_request_sent", "");
    } else {
        log_debug("tauri", "sidecar_shutdown_request_connect_failed", "");
    }
}

pub fn run() {
    log_debug("tauri", "app_builder_start", "");
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            log_transfer_ceremony_event,
            log_stabilization_event,
            read_transfer_ceremony_debug_log
        ])
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            log_debug("tauri", "setup_start", &format!("pid={}", std::process::id()));
            if sidecar_port_open() {
                log_debug("tauri", "setup_sidecar_port_open", "");
                if sidecar_health_ok() {
                    log_debug("tauri", "setup_reuse_healthy_sidecar", "");
                    app.manage(SidecarState(Mutex::new(None)));
                    return Ok(());
                } else {
                    log_debug("tauri", "setup_unhealthy_sidecar_restart", "");
                    request_sidecar_shutdown();
                    if !wait_for_sidecar_port_close(Duration::from_secs(3)) {
                        stop_stale_sidecars();
                    }
                }
            }
            let parent_pid = std::process::id().to_string();
            let resource_dir = app.path().resource_dir().ok();
            let child = spawn_hidden_sidecar(parent_pid.as_str(), resource_dir)?;
            app.manage(SidecarState(Mutex::new(Some(child))));
            log_debug("tauri", "setup_complete", "");
            Ok(())
        })
        .on_window_event(|_window, event| {
            log_debug("tauri", "window_event", &format!("{event:?}"));
        })
        .build(tauri::generate_context!())
        .expect("error while building Selene vessel")
        .run(|_app_handle, event| {
            log_debug("tauri", "run_event", &format!("{event:?}"));
        });
}
