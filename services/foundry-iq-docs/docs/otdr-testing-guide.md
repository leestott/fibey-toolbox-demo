# OTDR Testing Guide

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Purpose and Use Cases

- Use OTDR testing for acceptance, restoration, fault isolation, distance-to-event measurement, and splice trending over time.
- OTDR is not a direct replacement for insertion loss testing; use it to locate and characterize events, then validate service budget with OLTS when required.
- For PON work, test from the OLT side when possible and use the correct split-aware range and pulse settings.
- Always save native trace files and PDF exports to the job package before leaving the site.

## Common Field Platforms

| Instrument | Typical Use | Notes |
| --- | --- | --- |
| EXFO MAX-730C-SM1 | 1310/1550 OSP testing | Good baseline unit for feeder and distribution |
| VIAVI SmartOTDR | Construction and service turn-up | Use SmartLinkMapper only after reviewing raw trace |
| Yokogawa AQ7280 | Longer routes and central office work | Strong averaging and reporting options |
| EXFO FTBx-735C | PON and high dynamic range work | Useful on split architectures |
| Launch reel 1 km OS2 | Near-end event separation | Required for accurate first connector analysis |
| Receive reel 500 m OS2 | Far-end connector visibility | Use when end connector loss matters |

## Pre-Test Planning

1. Confirm fiber type, expected route length, expected splitter stages, and known closures from prints.
2. Identify whether the test is dark-fiber only or if live traffic could be present; never connect an OTDR directly to unknown live PON without approved filtering and process.
3. Inspect and clean all launch cords, receive cords, adapters, and panel ports before test setup.
4. Decide the wavelengths required: 1310/1550 nm for most single-mode OSP, 1625/1650 nm only with out-of-band live-fiber procedures and proper filters.
5. Determine whether bidirectional traces are needed for splice acceptance.

### Planning Inputs to Capture

- Cable segment names and expected lengths.
- Number of connectors, splitters, and splice closures expected.
- Design attenuation coefficient for the cable type.
- Maximum allowed end-to-end loss or PON class budget.
- Access limitations that may prevent far-end testing.

## Setup and Calibration

1. Allow the OTDR to reach operating temperature if brought from a cold vehicle into a warm hut or cabinet.
2. Verify date, time, operator name, and cable ID settings so saved files are traceable.
3. Run the instrument self-check if the platform provides it.
4. Zero or verify the launch and receive reels are correctly identified in the report template.
5. Confirm the index of refraction (IOR) for the fiber under test; wrong IOR produces wrong distance-to-event values.
6. Set acquisition wavelength, pulse width, range, averaging time, and event thresholds before connection.

| Parameter | Typical Starting Point | When to Change |
| --- | --- | --- |
| IOR OS2 | 1.4677 to 1.4682 | Use manufacturer data if provided |
| Range short access route | 2 to 10 km | Reduce for better near-end resolution |
| Range feeder route | 20 to 80 km | Increase if route is longer than expected |
| Pulse width short link | 5 to 30 ns | Use shortest pulse that still reaches end |
| Pulse width long link | 100 ns to 1 µs | Increase for splitter or high-loss routes |
| Averaging time | 15 to 60 s | Increase in noisy or long-range testing |
| Event threshold | 0.05 to 0.1 dB | Tighten for acceptance, loosen for noisy spans |
| Reflectance threshold | -55 to -35 dB | Adjust if low-reflectance APC connectors are used |

## Standard Test Procedure

1. Connect the launch reel to the OTDR and verify the first connection is clean and seated.
2. Connect the far end of the launch reel to the fiber under test using the correct adapter type; avoid unnecessary hybrid adapters.
3. If possible, install a receive reel at the far end to expose the last connector event.
4. Start with a short-range, short-pulse scan to inspect the near end and first few events.
5. Run a second scan with a longer pulse or range to confirm end-of-fiber and total span behavior.
6. For acceptance work, save traces at all required wavelengths and both directions where mandated.
7. Add manual markers at major closures, splitters, cabinets, and customer demarc locations.
8. Name files consistently: route_cable_fiber_direction_wavelength_date.sor.

### PON-Specific Notes

- Expect a large loss step at the splitter; compare measured splitter loss to design allowance, not to splice thresholds.
- A 1:32 PLC splitter typically contributes about 17 dB insertion loss plus connector and excess loss.
- Use longer pulses to see through splitter branches, but return to shorter pulses when examining near-end connectors or splices.
- Branch resolution after a splitter is limited; field acceptance still requires engineering judgment and in some cases selective branch isolation.

## Interpreting the Trace

| Trace Pattern | Meaning | Typical Cause | Action |
| --- | --- | --- | --- |
| Sharp reflective spike + drop | Reflective connector or mechanical event | UPC connector, open port, poor mating | Inspect and clean connection |
| Small non-reflective step | Fusion splice | Normal splice loss | Accept if within threshold |
| Large non-reflective step | High-loss splice or splitter | Bad splice or splitter stage | Verify location and expected design |
| Gradual slope increase | Fiber attenuation | Normal cable loss | Compare against wavelength coefficient |
| Sudden end with strong reflection | Open fiber end or break | Cut fiber, disconnected port | Dispatch to distance shown |
| Rounded dip and recovery | Macrobend or stress event | Tight loop or pinched cable | Inspect routing and bend radius |
| Broad noisy near-end region | Dead zone | Pulse too wide or launch too short | Use shorter pulse and longer launch reel |
| High backscatter mismatch event | Ghost or gainer risk | Different fiber backscatter coefficients | Use bidirectional averaging |

### Events, Reflections, Breaks, and Bends

- Connectors usually show reflectance; APC connectors reduce the spike compared with UPC but still require review.
- Fusion splices should appear as small, mostly non-reflective events. A reflective splice is a red flag for bad cleave or contamination.
- Mechanical splices often show higher event loss and may show modest reflectance depending on design and condition.
- Complete breaks create an end-of-fiber style reflection unless the endface is crushed or submerged, in which case the reflection may be muted.
- Macrobends often worsen at 1550 nm relative to 1310 nm; compare wavelengths before cutting into the cable.
- Microbends may present as distributed excess loss or unstable attenuation rather than one clean event.

## Typical Loss Budget References

| Element | Typical Allowance | Notes |
| --- | --- | --- |
| OS2 fiber @1310 nm | 0.35 dB/km | Use route design value if stricter |
| OS2 fiber @1550 nm | 0.22 dB/km | Higher bend sensitivity helps locate stress |
| Fusion splice | 0.05 to 0.1 dB | Field acceptance uses <0.1 dB |
| Mechanical splice | 0.2 to 0.5 dB | Field acceptance uses <0.5 dB |
| Mated connector pair | 0.2 to 0.5 dB | APC preferred for PON |
| 1:2 splitter | 3.5 dB nominal | Allow for excess loss |
| 1:4 splitter | 7.2 dB nominal | Allow for excess loss |
| 1:8 splitter | 10.5 dB nominal | Allow for excess loss |
| 1:16 splitter | 13.5 dB nominal | Allow for excess loss |
| 1:32 splitter | 17.0 dB nominal | Common GPON access design |
| 1:64 splitter | 20.5 dB nominal | Common high-density access design |

### Common Fault Signatures

- High-loss splice point: abrupt non-reflective event greater than design loss, often after recent construction or restoration.
- Dirty connector: inconsistent reflectance and loss at the same panel port across repeated tests.
- Unseated APC jumper: reflectance worse than expected and sometimes intermittent when the panel is touched.
- Macrobend in slack tray: added loss at 1550 nm with little change at 1310 nm.
- Splitter branch issue: budget failure on a specific branch even though feeder trace to the splitter is clean.
- Crushed cable: attenuation increase over a short section, sometimes with multiple small events rather than one break.

## Identifying Common Faults in the Field

1. If the first event is bad, inspect connectors, launch leads, and adapters before suspecting the installed plant.
2. If the event aligns with a closure or panel shown on the print, check workmanship first: tray routing, splice sleeves, and adapter cleanliness.
3. If the event appears between known structures, compare measured distance to slack loops, handholes, and route markers before digging.
4. If loss worsens significantly at 1550 nm only, prioritize bend inspection.
5. If the far-end event disappears with a longer pulse, confirm the route is not ending inside a dead zone caused by a preceding reflection.
6. If a gainer appears in one direction, do not report a negative splice loss; collect reverse-direction trace and average results.

## Dead Zones and Resolution Limits

- Event dead zone is the minimum distance after a reflective event where another event can be detected.
- Attenuation dead zone is longer; it is the distance required after reflection before accurate loss measurement resumes.
- Use the shortest practical pulse and a sufficiently long launch fiber to resolve the first connector and first splice.
- Do not over-range short links; excessive range settings can flatten detail and hide workmanship issues near the test point.

| Problem | Likely Setting Issue | Correction |
| --- | --- | --- |
| Near-end trace saturated | Pulse width too wide | Reduce pulse width |
| Cannot see first connector loss | Launch reel too short | Use longer launch reel |
| End of route not reached | Range too short or pulse too narrow | Increase range or pulse |
| Trace noisy | Averaging too short | Increase averaging time |
| Wrong event distance | IOR incorrect | Set proper IOR and retest |

## Reporting and Close-Out

- Save native SOR files, PDF summaries, and trace screenshots for any abnormal event called out in the narrative.
- Document pulse width, range, wavelength, IOR, launch length, and receive length in the test notes.
- Mark any inaccessible suspected fault location with GPS, route marker, and nearest structure ID.
- When a fault is corrected, retest and attach before/after traces to the same work order.
- Do not leave an OTDR-only conclusion where service acceptance required OLTS or power meter verification.

## Field Settings Appendix

### Starting Settings by Route Type

| Route Type | Range | Pulse Width | Averaging | Notes |
| --- | --- | --- | --- | --- |
| Drop or short inside plant | 2-5 km | 5-10 ns | 15-30 s | Focus on near-end detail |
| Distribution route | 10-20 km | 10-30 ns | 30 s | Good for closure-level analysis |
| Feeder route | 20-80 km | 30-100 ns | 30-60 s | Increase range only as needed |
| Split PON route | 20-80 km | 100 ns-1 µs | 60 s+ | Use shorter pulse for near-end recheck |

### OTDR Report Notes to Include

- Direction tested and far-end location.
- Launch and receive reel lengths.
- Wavelengths used.
- IOR used for distance calculation.
- Any inaccessible event locations or route assumptions.

### Common Trace Review Mistakes

- Reporting a gainer as negative loss without reverse-direction averaging.
- Misidentifying a splitter as a bad splice when the measured distance matches design.
- Chasing a first-event problem in the plant when the launch connection was dirty.
- Using a pulse width wide enough to hide two adjacent events inside one dead zone.

### Escalate to Engineering When

- Measured route length differs materially from prints.
- Splitter loss exceeds expected allowance across multiple branches.
- Event signatures suggest undocumented branch architecture.
- Budget margin is effectively zero after otherwise clean repairs.
- Coexistence GPON/XGS-PON behavior does not match the service record.

## Bidirectional Averaging Reminder

- Use forward and reverse traces when the splice result will be used for acceptance or dispute resolution.
- Average event loss for gainers and for routes where backscatter mismatch is obvious.
- Keep both source traces in the work package; do not save only the averaged report.
- Note the direction names clearly so later reviewers can align events to route markers.

## Live-Fiber Handling Notes

- Do not connect standard OTDR ports to unknown live service without approved filters and procedure.
- Verify whether the network uses in-service monitoring wavelengths before attaching any test gear.
- If live-fiber testing is not explicitly authorized, isolate the fiber or use passive verification methods first.
