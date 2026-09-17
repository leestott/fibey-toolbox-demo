# Installation Standards

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Purpose and Application

- These standards apply to new builds, restoration work that becomes permanent, cabinet rework, and customer-facing drop installations.
- When manufacturer instructions are more restrictive than this guide, follow the manufacturer.
- Any approved deviation must be documented in the work order and as-built package.

## Minimum Bend Radius

| Cable Condition | Default Minimum | Notes |
| --- | --- | --- |
| Static installed cable | 10 x cable OD | Applies when no pull load is present unless manufacturer specifies larger |
| Cable under tension during pull | 20 x cable OD | Use larger value for micro cable or specialty designs |
| Drop cable at ONT/NID | Per manufacturer, usually 10 x OD or better | Do not flatten under staples or clips |
| Patch cords/jumpers | Follow jumper spec; avoid cabinet door pinch points | APC cords especially sensitive to side load |

- Measure bend radius at the inside curve, not the outside jacket line.
- Do not force loops smaller just to make a tray or slack basket appear neat.
- Use bend-limiting guides where cabinet layout creates repeated technician contact.

## Cable Pulling Tension Limits

| Cable Type | Typical Field Reference | Rule |
| --- | --- | --- |
| Indoor premises fiber | 100 to 200 lbf common | Follow exact cable data sheet |
| OSP loose tube dielectric | Up to 600 lbf / 2700 N common | Use manufacturer pulling eye and monitor tension |
| Drop cable | Much lower than feeder cable | Do not assume feeder limits apply |
| Micro cable/blown fiber | Per microduct system design | Use only approved blowing parameters |

- Use pulling lubricant only when approved for the cable jacket and conduit system.
- Do not pull by buffer tubes or fiber units.
- Record pull tension when the project requires QA evidence or when route conditions were difficult.

## Splice Closure Installation

1. Verify closure model, tray count, cable port kit, and grommet size before cutting the cable.
2. Prepare the cable sheath and strength members per closure instructions, keeping sealing surfaces clean.
3. Bond or isolate metallic components per closure design and grounding requirements.
4. Dress tubes and fibers so the closure can be reopened later without crossing or trapped loops.
5. Torque hardware to manufacturer guidance and perform seal inspection before burial or lash-up.

### Closure Sealing Rules

- Seal around the actual cable OD; oversized grommets are not acceptable.
- Remove gel, dirt, and jacket flash from sealing surfaces before final assembly.
- Do not stack multiple cables in a port unless the closure kit explicitly supports it.
- Pressure-test or visually inspect per closure design and customer standard.

## Fiber Routing and Tray Standards

- Maintain natural fiber lay with no sharp crossovers over tray hinges or latches.
- Leave enough slack for one re-entry cycle without stripping the entire tube back again.
- Keep tray counts balanced; avoid overfilling one tray while others remain empty.
- Separate temporary restoration splices from permanent splices and label them clearly.

| Item | Standard |
| --- | --- |
| Fusion splice protection | Use approved heat sleeve in correct holder |
| Mechanical splice placement | Use dedicated holder; no loose placement in tray |
| Buffer tube support | Anchored before bare fiber enters tray |
| Shard control | No loose glass in closure or cabinet |
| Tray label | Cable IDs, tray number, date or work order reference |

## Labeling Conventions

- Every cable entry, closure, patch panel, FDH, FDT, splitter module, and ONT drop handoff must be labeled to match the print and OSS record.
- Use machine-printed labels whenever the environment allows; handwriting is for temporary restoration only.
- Label format should include route or site code, cable ID, fiber range or port range, and direction/origin-destination.
- Replace faded or missing labels encountered during maintenance and note the action in the work order.

| Location | Minimum Label Content |
| --- | --- |
| Closure exterior | Closure ID, route, fiber count, date/work order |
| Tray interior | Tray number and cable pairing |
| Patch panel | Panel ID, port, origin/destination |
| Splitter module | Splitter ratio, input fiber, output range |
| Drop demarc | Customer/site ID and service reference |

## Documentation Requirements

1. Update as-built redlines the same day as field changes when possible.
2. Capture photos of closure interior, labels, cabinet layout, and any non-standard condition.
3. Record fiber assignments, split ratios, port mappings, and spare counts.
4. Attach OTDR and loss results to the job package where testing was required.
5. Note any temporary conditions, inaccessible structures, or planned return work.

## Fiber Count Verification

- Verify cable count before first cut by jacket print and by opening enough construction to confirm tube and fiber count.
- For ribbon cables, confirm ribbon count and orientation before mass fusion.
- For distribution cabinets, verify splitter outputs and spare ports against the printed assignment.
- Do not assume a cable is fully populated based solely on outer jacket marking on legacy plant.

| Verification Method | Use Case |
| --- | --- |
| Visual tube/fiber count | Loose tube and drop cable confirmation |
| Ribbon count check | Mass fusion preparation |
| Continuity/VFL | Single strand identification on short dark sections |
| OTDR distance correlation | Confirm expected strand path on longer routes |
| Tone/ID tools as approved | Panel and port identification |

## Cabinet and Panel Standards

- Maintain front-to-back cable routing with separate paths for feeder, distribution, and drop where hardware supports it.
- Leave service loops tidy and accessible; no loops should obstruct door closure or fan/filter service.
- Protect APC connectors from cross-mating with UPC hardware by clear port identification.
- Remove abandoned jumpers when the change record confirms they are no longer in service.

## Outside Plant Installation Notes

- Respect conduit fill limits and pulling sequences on multi-cable routes.
- Use cable socks, swivels, and pulling eyes as required; do not improvise with tape on production pulls.
- At handholes, secure slack so lids cannot compress cable when reinstalled.
- On aerial plant, verify sag, hardware torque, bond points, and drip loops before signoff.

## Customer Premises Notes

- Protect finished surfaces and document the customer-approved pathway before drilling or clipping.
- Use firestop materials at penetrations where required by code or site standard.
- Avoid stapling drops so tightly that the jacket flattens or the buffer is stressed.
- Leave accessible slack at the ONT/NID and label the demarc clearly.

## Final Acceptance Checklist

- All labels installed and legible.
- Closure or cabinet sealed and hardware torqued.
- Fiber count and assignments match prints or approved redline.
- Loss and OTDR results within budget where required.
- Photos and test files attached to work order.
- Site restored and housekeeping complete.

## Audit Appendix

### Common Nonconformances

- Closure grommet oversized for the installed cable.
- Cabinet door pinches jumpers when closed.
- Labels missing direction or destination information.
- Slack loop stored below minimum bend radius.
- Unused ports left uncapped in dirty environments.
- Temporary restoration left undocumented.
- Fiber count on tray does not match the splice matrix.

### Closure Audit Table

| Check | Pass Condition |
| --- | --- |
| Port sealing | No visible gap, correct grommet, jacket clean |
| Strength member securement | Anchored per closure design |
| Tray routing | No pinch, no sharp crossover, no exposed bare glass |
| Labels | Match print and work order |
| Exterior condition | Closure ID visible and hardware secure |
| Re-entry readiness | Enough slack left for future maintenance |

### Labeling Example Format

- Closure: `CL-214 / FDR-12 / 288F / WO-58317`
- Tray: `TRAY-03 / Cable A to Cable B / Fibers 25-36`
- Panel port: `FDH-07 / Splitter 1:32 / Out 17 / 123 Main St`
- Drop demarc: `ONT-Address-Unit / Port / Date`

### As-Built Package Minimum

- Updated route or cabinet redline.
- Fiber assignment matrix.
- Photos of labels and finished workmanship.
- OTDR/loss files where required.
- Note of any spare fibers consumed or reassigned.
- Record of any deviations approved in the field.

### Rejection Examples

- Closure hardware cannot be tightened to maintain seal.
- Cable jacket cut extends into strength elements without an approved repair path.
- Bend radius violation cannot be corrected within the installed hardware.
- Label set is incomplete and the route cannot be safely maintained later.
- Work package does not reflect field changes to splitter or port mapping.

## Pull and Placement Notes

- Use intermediate pulls or figure-eight staging where conduit friction or route length demands it.
- Protect cable at vault rims, cabinet entries, and building penetrations during placement.
- Do not leave cable under sustained pull tension longer than necessary before securement.
- Confirm messenger clamps, dead-ends, and snowshoes match the installed aerial cable design.
- Verify innerduct color and occupancy records when multiple fibers share a common pathway.

## Post-Install Verification

- Confirm all access points are reclosed and secured.
- Check that lids, doors, and panels close without disturbing fiber routing.
- Verify any temporary traffic control damage or site restoration issue is documented for follow-up.
- Ensure the final route condition matches photos captured in the close-out package.

## Supervisor Release Notes

- Confirm deviations, if any, are approved and documented.
- Confirm permanent labels are installed where temporary tags were used during work.
- Confirm spare material and abandoned debris have been removed from the structure.
- Confirm customer-facing areas are restored and photographed where required.
