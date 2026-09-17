# Equipment Specifications

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Purpose

- Use this reference to match field tools to the job, check whether a device is appropriate for acceptance testing, and confirm maintenance intervals.
- Always prefer the exact manufacturer manual for firmware-specific menus or service actions.
- If a unit is past calibration or missing a current asset tag, remove it from acceptance work until cleared.

## Fusion Splicer Reference

| Model | Alignment Type | Typical Use | Notes |
| --- | --- | --- | --- |
| Fujikura 90S+ (FSM-90S+) | Core alignment | Backbone and feeder fusion splicing | Preferred for tight budgets and mixed backscatter conditions |
| Sumitomo TYPE-82C+ | Core alignment | OSP and central office splicing | Strong for low-loss SM work |
| Fujikura 41S+ | Clad/alignment optimized field unit | Access and drop work | Compact, suitable for general construction |
| Signal Fire AI-9 | V-groove/class entry level | Emergency or low-volume work only | Not preferred for acceptance on critical plant |
| Fujikura 70R+ | Ribbon mass fusion | High-count ribbon backbone | 12-fiber ribbon capable |

- Core-alignment splicers actively align fiber cores and generally provide the best performance on single-mode outside plant work.
- V-groove or basic clad-alignment splicers are acceptable for lower-criticality jobs but are more sensitive to fiber geometry differences and contamination.
- Match holders, sleeves, and fiber programs to the actual fiber coating and type.

### Fusion Splicer Operating Targets

| Item | Target |
| --- | --- |
| Estimated fusion splice loss | < 0.1 dB |
| Arc calibration | At start of day, after electrode change, and when environment changes |
| Electrode replacement | Per manufacturer life counter or if repeated bubbles/offset occur |
| Proof test | Enabled where program and cable design require it |
| Heater cycle | Per sleeve type and oven program |

## OTDR Reference

| Model | Wavelengths | Use | Notes |
| --- | --- | --- | --- |
| EXFO MAX-730C | 1310/1550 | General OSP acceptance | Good balance of portability and detail |
| VIAVI SmartOTDR | 1310/1550, options vary | Construction and troubleshooting | Auto map features should not replace raw trace review |
| Yokogawa AQ7280 | Module dependent | Longer reach and lab/CO work | High-quality averaging and reports |
| EXFO FTBx-735C | PON/high dynamic range options | Split architecture analysis | Best used by senior field techs or test group |

| OTDR Capability | Field Minimum |
| --- | --- |
| Event dead zone | < 1 m preferred for near-end work |
| Attenuation dead zone | As low as possible, review spec by pulse |
| Dynamic range | Sufficient for route length and splitter design |
| Trace storage | Native SOR export supported |
| Battery health | Enough for full job without field shutdown |

## Optical Power Meters and Light Sources

| Model | Type | Use |
| --- | --- | --- |
| EXFO FPM-600 | Optical power meter | Loss and receive power checks |
| VIAVI OLP-38 | Optical power meter/PON option | PON service verification |
| EXFO FLS-600 | Light source | Tier-1 insertion loss when paired with power meter |
| Fluke Networks CertiFiber Pro | OLTS set | Premises certification |

- Meters used for acceptance must carry current calibration labels and the correct wavelength selection.
- A power meter reading without a referenced source setup is not insertion loss; it is only absolute power.
- Keep detector caps on when not in use; scratched detectors skew results and fail calibration.

## Visual Fault Locators (VFL)

| Model | Output | Use | Caution |
| --- | --- | --- | --- |
| AFL VFI4 | Red visible laser | Short-range continuity and break indication | Class 3R eye hazard |
| Fluke Networks VisiFault | Red visible laser | Premises and patch field checks | Class 3R eye hazard |
| Generic 1 mW pen VFL | Red visible laser | Basic continuity | Do not rely on low-cost units for formal acceptance |

- VFLs are best for short links, patch fields, and visible break indication on drops.
- VFL light does not validate loss performance; it only confirms continuity or leakage points.
- Use APC-compatible accessories to avoid ferrule damage.

## Fiber Cleavers

| Model | Typical Cleave Length | Notes |
| --- | --- | --- |
| Fujikura CT50 | Adjustable for most holders | Preferred companion to 90S+/41S+ |
| Sumitomo FC-8R | Field standard lengths | Reliable single-fiber OSP use |
| INNO V7 cleaver | General field range | Use only with approved splicer combinations |
| Ribbon cleaver sets | Ribbon-specific | Required for ribbon mass fusion |

- Rotate the blade position according to the maintenance counter or sooner if cleave defects increase.
- Keep the waste bin emptied and the clamp pads clean.
- A high-end splicer cannot compensate for poor cleaves.

## Inspection Microscopes and Probes

| Model | Type | Use |
| --- | --- | --- |
| VIAVI P5000i | Digital inspection scope | Connector pass/fail analysis |
| EXFO FIP-435B | Digital inspection scope | Port and jumper inspection in OSP and CO |
| AFL FOCIS Flex | Handheld video probe | Patch panel inspection |
| Basic optical microscope | Manual view | Only where pass/fail program is not required |

- Digital scopes with automated grading are preferred because they reduce subjective calls on contamination.
- Use the correct probe tip for the connector type and access geometry.
- Never inspect a connector with a scope that is not safe for live-fiber procedures if there is any chance the port is energized.

## Calibration and Maintenance Schedule

| Equipment | Routine Field Check | Formal Calibration/Service |
| --- | --- | --- |
| Fusion splicer | Daily arc calibration and electrode inspection | Annual service or per asset policy |
| OTDR | Self-test before use, verify connectors and launch cords | 12 months typical |
| Power meter | Reference check before job | 12 months typical |
| Light source | Output stability check before job | 12 months typical |
| VFL | Function check each use | 12 months typical or asset policy |
| Cleaver | Blade position and clamp cleaning daily | Service as needed; blade rotation per count |
| Inspection scope | Tip condition and focus check daily | Annual verification if required by asset policy |

### Asset Control Rules

- Do not use expired assets for acceptance testing.
- Attach calibration certificate references in the quality package when customer contract requires it.
- Record firmware version when a device behavior issue is suspected.
- Spare batteries, chargers, and probe tips are part of the calibrated tool kit readiness check.

## Selection Guidance by Job Type

| Job Type | Minimum Tool Set |
| --- | --- |
| Backbone splice closure | Core-alignment splicer, cleaver, OTDR, power meter, inspection scope |
| Emergency drop restoration | Field splicer or approved mechanical splice kit, VFL, power meter |
| PON turn-up | PON-safe power meter/OLTS, OTDR if dark-fiber validation allowed, inspection scope |
| Data center MM certification | OLTS/Certifier, scope, polarity kit |
| High-count ribbon build | Ribbon splicer, ribbon cleaver, mass-fusion trays, OTDR |

## Retirement and Replacement Triggers

- Repeated inability to hold calibration.
- Damaged ports, stripped clamps, or cracked displays that affect test integrity.
- Battery runtime too short for a normal shift.
- Obsolete firmware or unsupported file export that blocks customer deliverables.
- Repair cost exceeding replacement threshold set by asset management.

## Readiness Appendix

### Pre-Shift Kit Check

- Splicer batteries charged and spare pack present.
- Cleaver waste bin emptied.
- OTDR launch and receive cords inspected and capped.
- Power meter reference cord identified and clean.
- VFL output verified on a dark test jumper.
- Inspection probe tips for SC/APC, SC/UPC, LC, and hardened ports available as needed.
- Charger inventory confirmed for all battery-powered tools.

### Common Equipment Failure Indicators

| Device | Indicator | Typical Action |
| --- | --- | --- |
| Fusion splicer | Frequent bubble/offset alarms | Clean, recalibrate, inspect electrodes |
| Cleaver | Rising hackle or angled cleaves | Rotate blade, clean clamps, verify setup |
| OTDR | Noisy trace on known-good route | Clean ports, inspect launch cord, increase averaging |
| Power meter | Unstable readings | Check detector cleanliness and battery state |
| Scope | Blurry or inconsistent grading | Clean tip and verify focus/calibration |
| VFL | Weak or intermittent emission | Replace batteries and inspect output port |

### Recommended Spares by Crew

| Spare Item | Minimum Carry |
| --- | --- |
| Fusion electrodes | 1 set |
| Heat sleeves | One full sleeve pack |
| Cleaver blade reserve position or spare blade | 1 |
| Launch jumper | 1 spare |
| APC/UPC adapters | As required for route types |
| Probe tips | 1 spare per common connector family |

### Asset Record Fields

- Manufacturer and model.
- Serial number and asset tag.
- Current firmware revision.
- Calibration due date.
- Last repair or service note.
- Assigned crew or depot location.
- Battery health or replacement date for critical handheld tools.

### Storage and Transport Notes

- Keep digital scopes capped during transport.
- Do not store splicers loose in truck beds or unsecured compartments.
- Protect OTDR and meter ports from dust using capped adapters.
- Allow instruments to acclimate when moving between extreme temperatures.
- Keep alcohol and chemical supplies separated from optics cases.

## Calibration Evidence Checklist

- Calibration label visible and in date.
- Asset number matches the tool record.
- Correct accessories present for the measurement type.
- Latest service issue closed before return to field use.
- Operator verified basic function on a known-good jumper before deployment.

## Cleaning Rules by Device

- Clean OTDR and meter ports with approved one-click or lint-free methods only.
- Keep splicer v-grooves and clamps free of coating fragments.
- Never use excessive solvent inside microscopes or electronic ports.
- Store all dust caps with the device so clean ports do not get recontaminated.
