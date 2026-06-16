import React, { memo } from "react";
import { Cpu, HardDrive, Database, Square, RefreshCw, Sun, Moon } from "lucide-react";

function TopStatusBar({ telemetry, serverRunning, activeModel, onStopServer, isStoppingServer = false, theme, setTheme }) {
  const formatGb = (value) => {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number.toFixed(number >= 10 ? 0 : 1) : "--";
  };

  const getStatusText = () => {
    if (serverRunning) return "Server Active";
    return "Local Mode";
  };

  const getStatusClass = () => {
    if (serverRunning) return "status-indicator busy";
    return "status-indicator offline";
  };

  return (
    <div className="top-status-bar">
      <div className="current-model-info">
        <div className={getStatusClass()}></div>
        <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
          {getStatusText()}
        </span>
        {activeModel && (
          <>
            <span style={{ color: "var(--md-sys-color-outline-variant)" }}>|</span>
            <span style={{ color: "var(--md-sys-color-primary)", fontWeight: 700 }}>
              {activeModel}
            </span>
          </>
        )}
      </div>

      <div className="telemetry-group">
        <button
          className="theme-toggle-btn"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {serverRunning && (
          <button
            className="m3-btn m3-btn-error"
            style={{ height: "34px", padding: "0 14px" }}
            onClick={onStopServer}
            disabled={isStoppingServer}
            title="Stop local model server"
          >
            {isStoppingServer ? <RefreshCw className="progress-spinner" size={14} /> : <Square size={14} />}
            <span>{isStoppingServer ? "Stopping" : "Stop Server"}</span>
          </button>
        )}

        {/* CPU Telemetry Chip */}
        <div className="telemetry-chip" title="CPU Utilization">
          <Cpu className="telemetry-chip-icon" style={{ color: "var(--md-sys-color-primary)" }} />
          <span>CPU: {Number.isFinite(Number(telemetry.cpu_usage)) ? telemetry.cpu_usage : "--"}%</span>
        </div>

        {/* RAM Telemetry Chip */}
        <div className="telemetry-chip" title="System Memory Usage">
          <HardDrive className="telemetry-chip-icon" style={{ color: "var(--md-sys-color-secondary)" }} />
          <span>RAM: {formatGb(telemetry.ram_used_gb)} / {formatGb(telemetry.ram_total_gb)} GB</span>
        </div>

        {/* GPU VRAM Telemetry Chip */}
        {telemetry.vram_total_gb > 0 && (
          <div className="telemetry-chip" title={`${telemetry.gpu_name} VRAM`}>
            <Database className="telemetry-chip-icon" style={{ color: "var(--md-sys-color-tertiary)" }} />
            <span>VRAM: {formatGb(telemetry.vram_used_gb)} / {formatGb(telemetry.vram_total_gb)} GB</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(TopStatusBar);
