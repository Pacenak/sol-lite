# Cross-platform command catalog

Commands below describe fixed adapter templates, not a free-form shell interface. Each check executes separately with broker deadlines and sanitized structured extraction. Angle-bracket placeholders mean broker-resolved resources, never shell substitution. Reads are autonomous only when unprivileged, scoped, supported and known not to expose secrets; administrative reads require approval. No whole-file configuration or log output reaches the model.

| OS | Category | Approved Command Purpose | Idempotent Check Syntax |
|---|---|---|---|
| Ubuntu / Debian | Identity | Kernel identity; distro fields parsed separately | `uname -s`; `uname -r` |
| Ubuntu / Debian | Addresses | Inspect links and addresses | `ip -j link show`; `ip -j address show` |
| Ubuntu / Debian | Routes | Inspect IPv4 / IPv6 routes | `ip -j -4 route show`; `ip -j -6 route show` |
| Ubuntu / Debian | DNS | Inspect resolver when systemd-resolved is active | `resolvectl status` (extract DNS fields only) |
| Ubuntu / Debian | Sockets | Inspect listeners without process arguments | `ss -lntu` |
| Ubuntu / Debian | Service | Inspect one approved service | `systemctl is-active <unit>`; `systemctl is-enabled <unit>` |
| Ubuntu / Debian | Capacity | Inspect space and uptime | `df -Pk`; `uptime` |
| Ubuntu / Debian | Package | Inspect selected package version | `dpkg-query -W -f=${Version} <package>` (literal format argv, no shell expansion) |
| Ubuntu / Debian | NetworkManager | Inspect selected nonsecret properties | `nmcli -g GENERAL.STATE device show <interface>` |
| Ubuntu / Debian | Firewall (privileged read) | Inspect rules via approved summary adapter | `nft list ruleset`; legacy `iptables -S`; `ip6tables -S` |
| macOS | Identity | Inspect product/kernel release | `sw_vers -productVersion`; `uname -r` |
| macOS | Addresses | Inspect discovered interface | `ifconfig <interface>` |
| macOS | Routes | Inspect routing tables / default route | `netstat -rn`; `route -n get default` |
| macOS | DNS | Inspect resolver / service DNS | `scutil --dns`; `networksetup -getdnsservers <service>` |
| macOS | Service discovery | Map service IDs to exact names | `networksetup -listallnetworkservices`; `networksetup -listallhardwareports` |
| macOS | Network state | Inspect service address configuration | `networksetup -getinfo <service>` |
| macOS | Sockets | Inspect listening TCP sockets without process command lines | `netstat -an -p tcp` (extract LISTEN records) |
| macOS | Capacity | Inspect space and uptime | `df -Pk`; `uptime` |
| macOS | Firewall (privileged read) | Inspect PF rules | `pfctl -sr` (sanitized summary only) |
| Both | Config metadata | Verify ownership, mode, size; broker hashes content | Linux `stat -c '%a %u %g %s' <resource>`; macOS `stat -f '%Lp %u %g %z' <resource>` |

Expected nonzero statuses such as `systemctl is-active` reporting inactive are typed state, not triggers for automatic repair. Missing commands return `UNSUPPORTED`; no installs. Read-only status commands can still update OS audit logs; autonomous classification means no intended configuration or administrative side effect.

## Configuration operations: always human-approved plans

These examples require reviewed adapters, typed parameters, preconditions and independent postchecks. They are never in the autonomous read catalog.

| OS | Category | Approved Command Purpose | Idempotent Check Syntax |
|---|---|---|---|
| Ubuntu / Debian | Persistent networking | Render candidate for detected Netplan/networkd/ifupdown owner; validate, atomically replace and activate | Compare normalized managed fields and file digest, then `ip -j address show` / `ip -j route show` |
| Ubuntu with Netplan | Candidate activation | Approved adapter may use `netplan generate`, `netplan try --timeout 60` or `netplan apply`; generation and trial both change state | Compare candidate and persistent state; independently verify address, routes and controller reachability; verify any rollback actually completed |
| Ubuntu / Debian with NetworkManager | Connection change | Exact approved `nmcli connection modify <connection> …` and activation through typed adapter | Compare selected nonsecret connection fields and live interface state |
| Ubuntu / Debian | Runtime route | Approved typed `ip route replace <prefix> via <gateway> dev <interface>`; persistence is a separate planned step | Compare exact prefix/gateway/interface in `ip -j route show` before and after |
| Ubuntu / Debian | DNS | Update the detected manager's persistent DNS configuration | Compare sanitized manager DNS state, `resolvectl status` if available, and an approved resolver probe |
| Ubuntu / Debian | Firewall | Validate and apply scoped nftables rules transaction; legacy iptables requires its own adapter | Compare canonical rule summaries and test management reachability; never flush as a reset |
| Ubuntu / Debian | Packages | Exact version `apt-get install <package>=<version>` through approved adapter; dependency effects included in plan | `dpkg-query` desired version before/after; no autonomous `apt-get update` |
| Ubuntu / Debian | Services | Exact approved `systemctl reload <unit>` / restart only where required | Compare configuration digest and service state; validate health after activation |
| macOS | DNS | `networksetup -setdnsservers <service> <address> …` through typed adapter | `networksetup -getdnsservers <service>` before/after; verify effective `scutil --dns` |
| macOS | Static addressing | `networksetup -setmanual <service> <address> <mask> <gateway>` | Compare `networksetup -getinfo <service>`, interface state and routes |
| macOS | DHCP | `networksetup -setdhcp <service>` | Compare DHCP mode and resulting address/routes; an approved address change may disconnect SSH |
| macOS | Firewall | Approved managed PF rules with scoped reload; no blanket flush | Compare ruleset digest and safe `pfctl -sr` summary; test reachability |
| Both | File changes | Approved atomic managed-resource replacement, backup and restore | Broker-held before/after digest, owner, mode and platform metadata |
| Both | Reboot | Dedicated approved disruptive operation with recovery plan | Verify boot identity changes, services, persistent config and controller reachability after reconnect |

Do not automate macOS security/UI-managed settings, package installers, or launchd changes without a separately registered version-specific adapter. Never disable SIP, host verification, auditing or approval controls as a fallback. Refer to [primary documentation](architecture.md#primary-references) and the detected release before implementing any template.
