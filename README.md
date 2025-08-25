# Nextlayersec-lab
Documented home lab with Microsoft Defender, OPNsense, Cloudflare Gateway, VLAN segmentation, and SIEM integration. Designed for full visibility, layered defense, and hands-on cybersecurity engineering.
# 🛡️ NextLayerSec Home Lab Infrastructure

This project documents the build-out of my secured home lab environment using enterprise-grade tooling for threat detection, segmentation, and DNS filtering. It serves as the foundation for a personal SOC-style architecture with full documentation and visibility into each security layer.

---

## 🔐 Security Components

### • Microsoft Defender for Business
- Endpoint protection (Windows + macOS)
- Email filtering via Microsoft 365
- Policy-based protection for IoT zones

### • Cloudflare Gateway
- DNS-level threat filtering
- Custom rules for content and malware control

### • Wi-Fi Upgrade: Eero Pro 7 Mesh System
- Wi-Fi 7, VLAN support, and high-throughput
- Isolated guest network and lab subnet

### • Firewall Appliance (planned: OPNsense or pfSense)
- Layer 7 filtering and traffic inspection
- Segmenting IoT, lab, and family traffic

### • Managed Switch
- VLAN tagging and port security
- Full network visibility and isolation

---

## 🧠 Why This Matters

This isn’t just about better Wi-Fi. It’s about building a **mini SOC** at home — with segmentation, DNS intelligence, endpoint protection, and full logging capability. This project demonstrates how to apply blue team principles in a practical, residential environment.

---

## 🗂️ Folder Structure
/infra-sec-lab

├── README.md

├── diagrams/

├── configs/

│ ├── firewall/

│ ├── switch/

│ └── cloudflare-gateway/

├── defender-setup/

├── siem-setup/

├── lessons-learned/

└── logs/

---

## 📘 Lessons Learned

Real-world issues and misconfigurations are documented in `/lessons-learned`. These entries provide insight into debugging, configuration tweaks, and implementation strategy.

Sample entries:
- Eero DNS conflicts with Cloudflare Gateway
- VLAN misrouting due to unmanaged switch behavior
- Defender policy sync delays
- Firewall interface misconfiguration

---

## 🛠️ Roadmap

- [ ] Finalize OPNsense deployment and rule tuning
- [ ] Launch Wazuh or Graylog SIEM integration
- [ ] Configure full DNS log forwarding + alerting
- [ ] Implement VLAN-based policy enforcement
- [ ] Write blog post breakdown at [nextlayersec.dev](https://blackvectra.substack.com/p/home-lab-pro-security-my-layered)

---

## 📬 Contact

Built and maintained by [Matthew Levorson](https://nextlayersec.dev)  
📫 `matthew@nextlayersec.dev`  
🌐 [nextlayersec.io](https://nextlayersec.io)

