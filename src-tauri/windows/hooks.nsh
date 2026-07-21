; Privacy-safe upgrade cleanup for legacy local packages.
; This removes only obsolete packaged analysis data inside the application
; install directory. Selene's configured data directory is not touched.
!macro NSIS_HOOK_PREINSTALL
  RMDir /r "$INSTDIR\_up_\dist-sidecar\selene-sidecar\_internal\analysis"
!macroend
