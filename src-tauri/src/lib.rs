use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread::sleep;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tauri::{Manager, State};

struct SidecarState {
    child: Mutex<Option<Child>>,
    local_capability: String,
}

struct LocalCapabilityState(String);

#[cfg(target_os = "windows")]
fn secure_local_capability() -> std::io::Result<String> {
    #[link(name = "bcrypt")]
    extern "system" {
        fn BCryptGenRandom(
            algorithm: *mut std::ffi::c_void,
            buffer: *mut u8,
            length: u32,
            flags: u32,
        ) -> i32;
    }
    const BCRYPT_USE_SYSTEM_PREFERRED_RNG: u32 = 0x00000002;
    let mut bytes = [0u8; 32];
    let status = unsafe {
        BCryptGenRandom(
            std::ptr::null_mut(),
            bytes.as_mut_ptr(),
            bytes.len() as u32,
            BCRYPT_USE_SYSTEM_PREFERRED_RNG,
        )
    };
    if status < 0 {
        return Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            "Windows CSPRNG could not create the local API capability",
        ));
    }
    Ok(bytes.iter().map(|byte| format!("{byte:02x}")).collect())
}

#[cfg(not(target_os = "windows"))]
fn secure_local_capability() -> std::io::Result<String> {
    use std::io::Read;
    let mut bytes = [0u8; 32];
    std::fs::File::open("/dev/urandom")?.read_exact(&mut bytes)?;
    Ok(bytes.iter().map(|byte| format!("{byte:02x}")).collect())
}

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

#[tauri::command]
fn close_app(app: tauri::AppHandle) {
    log_stabilization_debug("frontend", "close_app_requested", "");
    app.exit(0);
}

#[tauri::command]
fn local_api_capability(state: State<'_, LocalCapabilityState>) -> String {
    state.0.clone()
}

impl SidecarState {
    fn stop(&self) {
        log_debug("tauri", "sidecar_state_stop_called", "");
        if let Ok(mut child) = self.child.lock() {
            if let Some(mut child) = child.take() {
                let child_id = child.id();
                log_debug(
                    "tauri",
                    "sidecar_owned_child_shutdown_start",
                    &format!("pid={child_id}"),
                );
                request_sidecar_shutdown(&self.local_capability);
                sleep(Duration::from_millis(500));
                let _ = child.kill();
                let _ = child.wait();
                log_debug(
                    "tauri",
                    "sidecar_owned_child_shutdown_complete",
                    &format!("pid={child_id}"),
                );
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

fn sidecar_port_open() -> bool {
    TcpStream::connect_timeout(
        &"127.0.0.1:8766".parse().expect("valid sidecar address"),
        Duration::from_millis(250),
    )
    .is_ok()
}

fn sidecar_executable(resource_dir: Option<PathBuf>) -> std::io::Result<PathBuf> {
    let exe_dir = std::env::current_exe()?
        .parent()
        .map(PathBuf::from)
        .ok_or_else(|| {
            std::io::Error::new(std::io::ErrorKind::NotFound, "missing app exe directory")
        })?;
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
        .ok_or_else(|| {
            std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "selene sidecar executable not found",
            )
        })
}

fn spawn_hidden_sidecar(
    parent_pid: &str,
    resource_dir: Option<PathBuf>,
    local_capability: &str,
) -> std::io::Result<Child> {
    let exe = sidecar_executable(resource_dir)?;
    log_debug(
        "tauri",
        "sidecar_spawn_start",
        &format!("exe={}; parent_pid={parent_pid}", exe.display()),
    );
    let mut command = Command::new(exe);
    command
        .args(["--seed", "--port", "8766", "--parent-pid", parent_pid])
        .env("SELENE_LOCAL_API_CAPABILITY", local_capability)
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
        Ok(child) => log_debug(
            "tauri",
            "sidecar_spawn_complete",
            &format!("pid={}", child.id()),
        ),
        Err(err) => log_debug("tauri", "sidecar_spawn_failed", &err.to_string()),
    }
    child
}

fn request_sidecar_shutdown(local_capability: &str) {
    log_debug("tauri", "sidecar_shutdown_request_start", "");
    let address = "127.0.0.1:8766";
    if let Ok(mut stream) = TcpStream::connect_timeout(
        &address.parse().expect("valid sidecar address"),
        Duration::from_millis(500),
    ) {
        let _ = stream.set_write_timeout(Some(Duration::from_secs(2)));
        let request = format!(
            "POST /shutdown HTTP/1.1\r\nHost: 127.0.0.1:8766\r\nContent-Type: application/json\r\nX-Selene-Local-Capability: {local_capability}\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{{}}"
        );
        let _ = stream.write_all(request.as_bytes());
        log_debug("tauri", "sidecar_shutdown_request_sent", "");
    } else {
        log_debug("tauri", "sidecar_shutdown_request_connect_failed", "");
    }
}

pub fn run() {
    log_debug("tauri", "app_builder_start", "");
    let local_capability = secure_local_capability()
        .expect("secure local API capability generation failed");
    tauri::Builder::default()
        .manage(LocalCapabilityState(local_capability.clone()))
        .invoke_handler(tauri::generate_handler![
            log_transfer_ceremony_event,
            log_stabilization_event,
            read_transfer_ceremony_debug_log,
            close_app,
            local_api_capability
        ])
        .setup(move |app| {
            log_debug("tauri", "setup_start", &format!("pid={}", std::process::id()));
            if sidecar_port_open() {
                log_debug("tauri", "setup_sidecar_port_occupied_refused", "port=8766");
                return Err("Selene cannot verify ownership of the process already listening on port 8766. Close the existing Selene instance or sidecar before reopening the app.".into());
            }
            let parent_pid = std::process::id().to_string();
            let resource_dir = app.path().resource_dir().ok();
            let child = spawn_hidden_sidecar(
                parent_pid.as_str(),
                resource_dir,
                &local_capability,
            )?;
            app.manage(SidecarState {
                child: Mutex::new(Some(child)),
                local_capability: local_capability.clone(),
            });
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
