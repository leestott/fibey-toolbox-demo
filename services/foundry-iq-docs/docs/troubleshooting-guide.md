# Troubleshooting Guide

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## How to Use This Guide

- Start with the symptom observed by the customer, NOC, or acceptance test.
- Move from least invasive checks to plant-invasive actions: inspect, clean, test, isolate, repair.
- Do not cut or resplice until connector condition, patching, and test setup have been ruled out.
- Save before-and-after evidence for every corrective action.

## Decision Tree

1. Is the issue affecting one service, one fiber, one cable, or multiple customers behind a common splitter?
2. Is there light loss, intermittent service, total outage, or test failure only?
3. Are connectors confirmed clean and fully seated?
4. Does OTDR show a localized event, a distributed loss pattern, or no useful data because of dead zone or splitter complexity?
5. Can the fault be isolated from both ends or from a mid-span access point?
6. After the suspected correction, was the route retested with the same method used to identify the fault?

| Symptom | First Check | Second Check | Escalate When |
| --- | --- | --- | --- |
| High end-to-end loss | Inspect/clean connectors | Review OTDR for localized event | Loss still exceeds budget after connector remediation |
| One customer down on PON | Verify ONT power and drop continuity | Check branch budget at splitter | Common feeder event appears |
| Multiple customers down | Check OLT/FDH/common splitter path | OTDR feeder route | Break or cabinet damage found |
| Intermittent alarms | Patch cord strain and connector seating | Look for bend-sensitive section | Problem persists after patch replacement |
| No OTDR end event | Range/pulse/launch setup | Possible hard break or wrong fiber | Repeated traces inconsistent |

## High Loss at Splice Points

- Typical indicators: OTDR non-reflective step above threshold, rising BER after recent construction, or power meter results outside design with no connector issue found.
- Most common causes are poor cleaves, contamination, fiber type mismatch, incorrect splicer program, or stress introduced while loading the tray.
- For fusion splices, any estimate above 0.1 dB requires immediate rework unless the work order includes an approved exception.
- For mechanical splices, anything above 0.5 dB should be rebuilt and logged as temporary until stabilized.

1. Confirm event location matches the expected closure or tray.
2. Open the tray and inspect sleeve position, fiber routing, and whether the bare glass transition is stressed.
3. If recent work used mixed G.652/G.657 fibers, verify the correct program and bidirectional test interpretation.
4. Cut back to fresh coated fiber, clean, recleave, and resplice.
5. Retest from both directions if route length or design criticality warrants it.

## Dirty Connectors

- Dirty connectors are the most common cause of avoidable loss and reflectance faults.
- Never mate first and inspect later; every connection used for testing or service handoff must be inspected and cleaned.
- Contamination can transfer from adapter sleeves, dirty test jumpers, or improperly capped ports.

| Observation | Likely Cause | Action |
| --- | --- | --- |
| Random loss changes after reconnect | Particulate contamination | Inspect-clean-inspect both sides |
| High reflectance at panel port | Dirty UPC/APC interface | Clean port and jumper, replace damaged ferrule |
| Scope fail with oily film | Solvent residue or skin oils | Use dry/wet-dry cleaning process |
| Repeated contamination after cleaning | Dirty adapter sleeve | Replace adapter |

## Macrobend Loss

- Macrobend loss usually increases at 1550 nm more than at 1310 nm on single-mode fiber.
- Common field locations include tight slack storage, cabinet doors pinching a jumper, customer wall plates, and tray exits with undersized loops.
- Bend-insensitive fiber reduces but does not eliminate poor routing issues.

1. Compare loss at 1310 and 1550 nm.
2. Inspect slack loops, tray corners, cabinet hinges, and drop entrances.
3. Relieve stress and increase bend radius to at least the installation standard for that cable.
4. Retest immediately after rerouting to confirm the fault signature disappears.

## Fiber Breaks

- Complete breaks usually show strong reflection at the end unless submerged, crushed, or terminated in debris.
- Field breaks often occur at handhole lids, aerial hardware, rodent-damaged spans, construction cuts, and customer staple damage on drops.
- Before dispatching civil work, confirm the OTDR distance with route prints, slack loops, and both-end traces when available.

| Break Scenario | Clue | Preferred Action |
| --- | --- | --- |
| Clean cut by dig-in | Strong reflection and total outage | Dispatch to measured route location |
| Crush/pinch | Short high-loss section before break | Inspect closures, lids, or conduit transitions |
| Aerial storm damage | Distance near span hardware | Visual patrol before climbing |
| Customer drop severed | Loss isolated to single ONT/drop | Replace drop or splice approved repair section |

## OTDR Dead Zones

- Dead zones hide events that occur too close to a strong reflection or too close to the test port.
- The fix is usually test setup, not plant repair.
- Near-end connector issues are commonly misdiagnosed because a launch cord was omitted or too short.

1. Install the correct launch reel and, if needed, a receive reel.
2. Reduce pulse width and shorten range for near-end analysis.
3. Inspect the first reflective connector because a dirty or damaged launch connection can create an oversized dead zone.
4. Retest before opening any closure within the hidden region.

## Connector Endface Defects

| Defect | Appearance | Risk | Disposition |
| --- | --- | --- | --- |
| Contamination | Dust, film, residue, opaque spots | High loss or ferrule damage | Clean and reinspect |
| Scratch | Linear mark across core or cladding | Permanent loss and reflectance issue | Replace if in core or severe |
| Pit | Small crater or void | Scatter and reliability risk | Replace connector |
| Chip | Edge fracture | Can damage mating connector | Replace immediately |
| Hackle on field-polished end | Jagged fractured appearance | Unstable performance | Re-terminate or replace |

- Do not use connectors that fail IEC-style inspection criteria in the core zone.
- A scratched APC ferrule can pass light one moment and fail badly after remating; replace it rather than chasing intermittent symptoms.
- Document recurring defects by panel or jumper batch if a quality issue is suspected.

## Symptom-to-Cause Matrix

| Symptom | Likely Causes | Primary Tools |
| --- | --- | --- |
| Low optical power only | Dirty connectors, patch issue, splitter over-budget | Power meter, inspection scope |
| High reflectance alarm | UPC/APC mismatch, dirty connector, cracked ferrule | OTDR, inspection scope |
| 1550 nm worse than 1310 nm | Macrobend or stress | OTDR dual wavelength |
| All services behind splitter impacted | Feeder issue, splitter fault, common cabinet event | OTDR from OLT side |
| Single strand outage after closure work | Mispatch, wrong tray, bad splice | Continuity, OTDR, splice records |
| Intermittent after door closes | Pinched jumper or bend at hinge | Visual inspection, live power meter |

## Recommended Troubleshooting Sequence

1. Verify the correct fiber, circuit ID, and service path; misidentification wastes hours.
2. Inspect and clean all accessible connectors on both ends.
3. Run insertion loss or live power checks to confirm the symptom quantitatively.
4. Run OTDR with proper launch/receive configuration.
5. Correlate the event location to route structures and recent work history.
6. Repair the most likely local issue first, then retest before proceeding deeper into the plant.
7. Escalate to civil or aerial repair only after the optical evidence supports a physical route fault.

## When to Replace Instead of Rework

- Replace connector jumpers with repeat contamination, loose boots, or ferrule damage.
- Replace mechanical splices used as temporary restoration during the next maintenance window.
- Replace drop cable with multiple staple or crush points rather than stacking patch repairs.
- Replace adapters that repeatedly contaminate cleaned ferrules.
- Replace closures or trays that cannot maintain fiber routing without pinch or stress.

## Documentation Requirements

- Capture the original symptom, test method, and baseline readings.
- Attach scope images for any failed endface and note whether the defect was contamination or damage.
- Attach before/after OTDR traces whenever a field splice or route repair is performed.
- Log exact closure, tray, port, splitter, or customer address impacted.
- Note whether service was restored via permanent fix or temporary restoration method.

## Escalation Appendix

### Quick Isolation Guide

| If this is true | Then do this next |
| --- | --- |
| Only one ONT is down | Check drop, connector cleanliness, and assigned splitter output |
| Entire splitter leg is down | Inspect common terminal, splitter, and feeder event history |
| Trouble started after closure entry | Audit tray routing and recent splice work first |
| Loss changes after remating | Treat connector contamination as primary suspect |
| OTDR trace is ambiguous | Retest from opposite end or change setup before repair |
| Trouble follows a jumper move | Replace the jumper and reinspect adapters |

### No-Cut Checks Before Plant Repair

- Confirm the correct strand and service record.
- Inspect and clean all accessible connectors.
- Replace suspect patch cords or jumpers.
- Verify test setup with known-good launch leads.
- Check whether the reported issue is confined to one wavelength or service profile.

### Evidence Package Minimum

- Before-and-after OTDR traces when plant was repaired.
- Scope images for any failed connector endface.
- Photos of damaged cable, tray, or cabinet condition.
- Recorded power levels or insertion loss values.
- Exact event distance and nearest structure ID.
- Customer or NOC symptom reference and time observed.

### Escalate Beyond Field Repair When

- Repeated failures occur on the same closure or adapter population.
- Route records do not match actual field topology.
- A civil dig, bore, or utility conflict is likely.
- Budget remains out of tolerance after clean connectors and verified resplices.
- Service impact spans multiple cabinets, OLT ports, or network domains.
- Hidden infrastructure cannot be safely accessed with current permits or traffic control.

## Dispatch Preparation Notes

- Bring the closure print, current assignment map, and the latest accepted trace if available.
- Stage both connector-cleaning supplies and splice-repair supplies so the crew does not assume the failure mode too early.
- Confirm permit, traffic, or access constraints before sending a repair crew to a suspected route location.
- Advise the crew whether the site is likely drop-only, terminal-level, or feeder-level based on current evidence.

## Final Validation Checklist

- Service restored and alarm cleared.
- Optical measurements repeated with the same method used to identify the problem.
- Temporary conditions tagged for follow-up.
- Before/after evidence attached to the work order.
- Customer, NOC, or project contact notified of restoration status.

## Closure Notes

- If repeated faults occur at one structure, flag it for proactive rebuild review.
- Record exact temporary restoration location and owner for follow-up.
