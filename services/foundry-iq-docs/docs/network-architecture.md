# Network Architecture

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Purpose

- This overview is intended for field operations teams supporting passive optical network builds, activations, and fault isolation.
- Use it to understand where the field work sits relative to OLT ports, feeder plant, splitter stages, and ONT/ONU placement.
- For detailed design release values, defer to network engineering documents and vendor-specific OLT templates.

## PON Topology at a Glance


```
OLT port -> feeder fiber -> primary splitter -> distribution fiber -> secondary splitter or terminal -> drop fiber -> ONT/ONU
```
- The OLT lives in a central office, hub, headend, or cabinet and feeds one or more optical distribution networks.
- Passive splitters divide one optical port across many customers without powered electronics in the outside plant.
- ONT/ONU devices terminate the optical service at the customer or remote endpoint.

## Core Components

| Component | Function | Typical Placement |
| --- | --- | --- |
| OLT | PON headend electronics and service control | CO, hub, exchange, or cabinet |
| Feeder fiber | High-count fiber from OLT to serving area | CO to FDH/FDT or splitter hub |
| Primary splitter | First optical division stage | FDH, central splitter cabinet, or splice closure |
| Secondary splitter | Additional branch division where used | Terminal, smaller cabinet, pedestal |
| Distribution fiber | Fiber from primary split to serving area | OSP ducts/aerial/buried |
| Drop fiber | Final connection to subscriber or endpoint | Terminal to ONT/ONU |
| ONT/ONU | Customer or remote endpoint optical unit | Inside premise, MDU room, or external NID |

## OLT Considerations

- Each OLT PON port has a defined optical budget, split limit, and service profile that must align with the outside plant design.
- Field teams usually interact with OLT data through turn-up records, power readings, and assigned port maps rather than direct configuration.
- When multiple customers fail on one PON, always identify the shared OLT port and common feeder path first.

## Splitter Architecture

| Split Ratio | Nominal Split Loss | Typical Use |
| --- | --- | --- |
| 1:2 | 3.5 dB | Special business, protection, or staging use |
| 1:4 | 7.2 dB | Low-density serving areas |
| 1:8 | 10.5 dB | Small remote serving groups |
| 1:16 | 13.5 dB | Rural or lower-density distribution |
| 1:32 | 17.0 dB | Common GPON/XGS-PON access design |
| 1:64 | 20.5 dB | Higher density design where budget supports it |
| 1:128 | 24.0 dB | Only where optics class and engineering policy support it |

### Single-Stage vs Two-Stage Split

- Single-stage split places one splitter, often 1:32 or 1:64, near the serving area and keeps troubleshooting simpler.
- Two-stage split reduces feeder fiber count by placing a primary split upstream and a secondary split closer to customers.
- Two-stage architecture increases documentation importance because faults can hide behind multiple branch points.

## GPON Reference

| Parameter | Typical Value |
| --- | --- |
| Downstream rate | 2.488 Gb/s |
| Upstream rate | 1.244 Gb/s |
| Common wavelengths | 1490 nm downstream, 1310 nm upstream, 1550 nm video overlay where used |
| Common optical class | B+ 28 dB budget, C+ 32 dB budget |
| Typical split ratio | 1:32, sometimes 1:64 |
| Common use | Residential broadband and SMB access |

## XGS-PON Reference

| Parameter | Typical Value |
| --- | --- |
| Downstream rate | 9.953 Gb/s |
| Upstream rate | 9.953 Gb/s |
| Common wavelengths | 1577 nm downstream, 1270 nm upstream |
| Common optical class | N1 29 dB budget, N2 31 dB budget |
| Typical split ratio | 1:32 or 1:64 depending reach and service mix |
| Common use | Higher-speed residential, enterprise, and backhaul access |

## Typical Power Budget Thinking

- Budget starts with the optics class, then subtract splitter loss, connector loss, splice loss, fiber attenuation, and engineering margin.
- Field technicians should know whether the route is designed near the edge of budget because small workmanship issues matter more there.
- A clean 1:32 GPON design with 10 km of fiber often tolerates normal splices and connectors comfortably, while stacked splits and long rural routes may not.

| Budget Element | Typical Allowance |
| --- | --- |
| Fiber attenuation 1310 nm | 0.35 dB/km |
| Fiber attenuation 1490/1550 nm | 0.22 to 0.25 dB/km typical |
| Fusion splice | 0.05 to 0.1 dB each |
| Connector pair | 0.2 to 0.5 dB each |
| Engineering reserve | 1 to 3 dB depending policy |
| Mechanical splice | 0.2 to 0.5 dB each and usually avoided in permanent PON path |

## ONT and ONU Placement

- Place ONTs where power, battery backup policy, environmental protection, and technician access are acceptable.
- For single-family homes, ONTs are commonly inside utility spaces or in hardened exterior NIDs.
- For MDUs, ONTs or ONUs may be centralized in telecom rooms with Ethernet distribution beyond that point.
- For business services, confirm whether the ONU is customer-managed, carrier-managed, or part of a demarc cabinet.

## Field Architecture Scenarios

| Scenario | Typical Architecture | Field Notes |
| --- | --- | --- |
| Suburban FTTH | OLT -> 1:32 primary split -> terminal -> drops | Most common, straightforward restoration |
| Rural long-reach | OLT -> 1:4 -> 1:8 staged split | Watch cumulative loss and route length |
| MDU | OLT -> splitter cabinet -> riser distribution -> ONT/ONU closet | Labeling and floor mapping are critical |
| Business overlay | Dedicated or low split PON | Lower contention, tighter service expectations |
| Migration area | Coexistence GPON and XGS-PON | Wavelength plans and splitter sharing must be known |

## Fault Isolation by Architecture Layer

1. If one customer is affected, start at the drop, terminal port, and assigned splitter output.
2. If a cluster of customers on one street is affected, check the local terminal, secondary splitter, and distribution segment.
3. If all customers behind one FDH or common port are affected, suspect feeder fiber, primary splitter, or OLT port issue.
4. If only high-speed XGS subscribers are affected in a coexistence area, verify the optics class and wavelength-specific path rather than assuming a general fiber break.

## Documentation Needed for Field Success

- OLT shelf/slot/port assignment.
- Splitter locations and ratios by serving area.
- Input and output fiber mapping for every splitter stage.
- Feeder, distribution, and drop cable IDs.
- Power budget summary and acceptance thresholds.
- Customer-to-port or ONT-to-splitter association.

## Common Architecture Failure Points

- Mispatched splitter outputs during augments.
- Undocumented spare fiber use during restoration.
- Common feeder closures with repeated re-entry damage.
- Oversubscribed split ratios after growth without budget review.
- Cabinet contamination or damaged adapters affecting multiple branches.

## Turn-Up Checklist

- Verify assigned OLT port and splitter output before moving the customer drop.
- Inspect and clean all connectors in the service path.
- Confirm ONT optical receive level falls inside service window.
- Validate loss against budget and save evidence to the activation record.
- Update port mapping if any field change occurred during install.

## Operations Appendix

### Typical Split Planning Notes

- 1:32 is the operational sweet spot for many GPON and XGS-PON builds where margin and growth are balanced.
- 1:64 requires tighter loss control and cleaner records because faults affect more subscribers.
- Two-stage split plans reduce feeder count but increase the need for exact branch labeling.
- Business or premium services may reserve lower split ratios for extra budget margin.
- Any design close to the optical limit needs especially clean connector and splice workmanship.

### Class Reference Table

| Technology/Class | Budget Reference | Common Use |
| --- | --- | --- |
| GPON B+ | 28 dB | Standard residential access |
| GPON C+ | 32 dB | Longer reach or higher split situations |
| XGS-PON N1 | 29 dB | Common 10G access deployments |
| XGS-PON N2 | 31 dB | Higher margin designs |

### Field Records That Matter Most

| Record | Why it Matters |
| --- | --- |
| OLT shelf/slot/port | Identifies the common service domain |
| Splitter input/output map | Critical for isolating affected branches |
| FDH/FDT/terminal IDs | Connects optical events to physical structures |
| ONT assignment | Prevents porting and activation errors |
| Budget summary | Tells field techs how much margin exists |
| Migration notes | Clarifies coexistence and upgrade areas |

### Coexistence Notes

- GPON and XGS-PON may share portions of the passive plant when the wavelength plan allows it.
- Field teams should verify service records before assuming one technology fault affects the other.
- Mixed-service cabinets need especially clear port labels and patch discipline.
- A clean optical path can still fail activation if the ONT is mapped to the wrong logical service profile.

### Common Service-Affecting Errors

- Wrong splitter output assigned to the drop.
- Undocumented spare fiber use during restoration.
- Mixed GPON and XGS-PON records in a coexistence area.
- Connector contamination at a common splitter cabinet.
- Port map not updated after augments or migrations.
- Splitter replacement performed without updating ratio or output numbering in records.

## Activation Handoff Checks

- Port assignment in records matches the actual ONT service path.
- Splitter output and terminal port labels match the install sheet.
- Receive power and loss results are stored with the activation record.
- Any spare-fiber reassignment or field patch change is reflected in OSS and as-builts.

## Growth Planning Reminders

- Adding customers to a nearly full split requires both port capacity review and optical budget review.
- Augments should preserve logical grouping so future outages can be isolated quickly.
- Document any staged dark splitters so future crews do not mistake them for active customer paths.
