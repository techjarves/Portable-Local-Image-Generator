import React, { memo } from "react";
import { Image, FolderDown, Sliders, Shield, Terminal } from "lucide-react";

function Sidebar({ activeTab, setActiveTab, specs }) {
  return (
    <div className="sidebar">
      <div>
        {/* Sidebar Header */}
        <div className="sidebar-logo">
          <Shield className="sidebar-logo-icon" />
          <span className="sidebar-logo-text">Local AI Studio</span>
        </div>

        {/* Sidebar Navigation Links (Material 3 style) */}
        <div className="nav-list">
          <div
            className={`nav-item ${activeTab === "generator" ? "active" : ""}`}
            onClick={() => setActiveTab("generator")}
          >
            <Image size={20} />
            <span>Image Generator</span>
          </div>

          <div
            className={`nav-item ${activeTab === "models" ? "active" : ""}`}
            onClick={() => setActiveTab("models")}
          >
            <FolderDown size={20} />
            <span>Model Manager</span>
          </div>

          <div
            className={`nav-item ${activeTab === "constraints" ? "active" : ""}`}
            onClick={() => setActiveTab("constraints")}
          >
            <Sliders size={20} />
            <span>Image Constraints</span>
          </div>
        </div>
      </div>

      {/* Sidebar Footer with Host Telemetry System Specs */}
      <div className="sidebar-footer">
        <div className="sidebar-specs-header">
          <Terminal size={12} />
          <span>Host Specifications</span>
        </div>
        <div className="sidebar-specs-item" title={specs.cpu_name}>
          CPU: {specs.cpu_name}
        </div>
        <div className="sidebar-specs-item" title={specs.gpu_name}>
          GPU: {specs.gpu_name}
        </div>
        <div className="sidebar-specs-item">
          Memory: {specs.ram_total_gb.toFixed(0)} GB RAM ({specs.cpu_cores_physical} Cores)
        </div>
        <div className="sidebar-specs-os">
          OS: {specs.os_name}
        </div>
      </div>
    </div>
  );
}

export default memo(Sidebar);
