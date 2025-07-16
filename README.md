# infra-sec-lab
Documented home lab with Microsoft Defender, OPNsense, Cloudflare Gateway, VLAN segmentation, and SIEM integration. Designed for full visibility, layered defense, and hands-on cybersecurity engineering.
# 🏠 NextLayerSec Home Lab Infrastructure

This project documents the build-out of my secured home lab environment using enterprise-grade tooling for threat detection, segmentation, and DNS filtering.

## 🔐 Components

- **Microsoft Defender for Business**
  - Endpoint protection (Windows + macOS)
  - Email filtering via Microsoft 365
  - Policy-based protection for IoT zones

- **Cloudflare Gateway**
  - DNS-level threat filtering
  - Custom rules for content and malware control

- **Wi-Fi Upgrade: Eero Pro 7 Mesh System**
  - Wi-Fi 7, VLAN support, and high-throughput
  - Isolated guest network and lab subnet

- **Firewall Appliance**
  - Layer 7 filtering (planned: pfSense or OPNsense)
  - Segmenting IoT, lab, and family traffic

- **Managed Switch**
  - VLAN tagging and port security
  - Full network visibility

## 🧠 Why This Matters

This isn’t just about better Wi-Fi. It’s about building a **mini SOC** at home — with segmentation, DNS intelligence, endpoint control, and alerting all layered together.

## 📸 Diagrams

- Full network topology with VLANs and interfaces
- Cloudflare policy flow
- Microsoft Defender endpoint coverage

## 🚧 Roadmap

- [ ] Add dynamic dashboard with Grafana or ELK
- [ ] Add port mirror for packet capture
- [ ] Enable DNS logging to SIEM
