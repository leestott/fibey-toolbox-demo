# Fiber Splicing Procedures

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Purpose and Scope

- Use this guide during outside plant, feeder, distribution, and premises work where permanent or temporary fiber restoration is required.
- Default to fusion splicing for new construction, permanent repair, backbone restoration, and any circuit with strict optical budget.
- Mechanical splicing is acceptable for emergency restoration, low-count drops, short-term service recovery, or locations where fusion equipment cannot be stabilized.
- All splice work must be traceable to the work order, cable ID, buffer tube, fiber color, location reference, and technician badge number.
- If site conditions prevent a clean work surface, stop and relocate to a splice trailer, van, tent, or approved enclosure.

## Acceptance Criteria

| Item | Target | Action if Out of Spec |
| --- | --- | --- |
| Fusion splice estimated loss | < 0.1 dB | Re-prep and resplice immediately |
| Mechanical splice estimated loss | < 0.5 dB | Replace splice element and reterminate |
| Fusion splice tensile retention | Sleeve secure, no slip under tray handling | Rebuild splice and replace protector |
| Endface condition before splicing | No chips, hackles, lips, or contamination | Reclean and recleave |
| Fiber length left in tray | Service loop per closure design | Re-dress fibers before close-out |
| Documentation completeness | 100% fiber IDs recorded | Do not close work order until corrected |

## Approved Equipment and Consumables

| Category | Preferred | Alternate | Notes |
| --- | --- | --- | --- |
| Fusion splicer | Fujikura 90S+ (FSM-90S+) | Sumitomo TYPE-82C+ | Use core-alignment mode for single fibers |
| Single-fiber field splicer | Fujikura 41S+ | INNO View 7 | Acceptable for access and drop work |
| Ribbon splicer | Fujikura 70R+ | Sumitomo TYPE-72M12 | Use only when ribbon continuity is required |
| Mechanical splice | 3M Fibrlok II 2529 | Corning CamSplice | Verify fiber size compatibility before use |
| Cleaver | Fujikura CT50 | Sumitomo FC-8R | Rotate blade position per maintenance log |
| Alcohol | 99% IPA, reagent grade | Fiber cleaning cassette | Do not use denatured alcohol |
| Protection sleeve | 60 mm heat sleeve, FP-03 | 40 mm micro sleeve where tray supports it | Match tray and holder design |
| Inspection scope | VIAVI P5000i | EXFO FIP-435B | Use before every connectorized test handoff |

## Pre-Splice Preparation

1. Confirm work order, cable IDs, strand assignments, and whether the splice is planned or restoration-driven.
2. Check weather, shelter, and power availability; do not open closures in rain without a tent or vehicle workspace.
3. Set up a clean mat, sharps container, lint-free wipes, stripper set, cleaver, splicer, and splice tray layout sheet.
4. Verify the splicer has current arc calibration, correct fiber program, and electrode life remaining for the planned job size.
5. Inspect sheath entry points and ensure cable is secured before exposing buffer tubes or loose fibers.
6. Clean hands or change gloves before touching bare glass; contamination at this stage usually appears as bubbles or high-loss estimates later.
7. Stage only one fiber pair at a time unless using mass-fusion workflow and tray mapping has been double-checked by a second tech.

### Field Prep Checklist

- Verify cable jacket and closure labels match prints.
- Confirm fiber type on both sides: OS2 to OS2, OM4 to OM4, ribbon count to ribbon count.
- Strip enough buffer for comfortable routing without exceeding tray fill.
- Measure required bare fiber length for the specific splicer and holder.
- Place fiber scraps directly into the shard bottle; never on the work mat.
- Stabilize the work surface to prevent cleaver vibration.
- Allow splicer heaters and ovens to warm fully before first sleeve cycle.
- Record ambient temperature if below 0 C or above 35 C.

## Fiber Access and Jacket Removal

1. Open the cable per manufacturer instructions, preserving central strength members and ripcord paths.
2. Remove armor, binders, and flooding compound as required, using approved wipes and solvent sparingly.
3. Secure buffer tubes and strength members in the closure or panel before individual fibers are stripped.
4. Identify the correct buffer tube by print, color code, and count verification; never trust memory alone on a restoration job.
5. Cut damaged sections back to clean fiber. If the break is crushed or water-exposed, remove additional length until coating condition is normal.

### Coating and Buffer Removal

- Use the proper 250 µm or 900 µm stripper opening; oversized stripper use causes scoring and later breaks.
- Strip in one smooth pull. If the coating necks down or snags, cut back and try again.
- Leave enough coated fiber to route through the tray and sleeve holder without stress at the bare glass transition.
- Wipe stripped fiber from coating toward the end using a lint-free wipe saturated with 99% IPA.
- Repeat cleaning until the glass squeaks on the wipe and no residue appears.

## Cleaving Procedure

1. Inspect the cleaned bare glass under task light before placing it in the cleaver.
2. Set cleave length to the splicer program, typically 8-16 mm depending on holder style.
3. Place the fiber flat in the cleaver clamp; do not twist or force it into the fiber guide.
4. Close the clamp gently, execute the cleave, and transfer the fiber without touching the endface.
5. Reject any cleave showing angle, lip, hackle, misting, or coating debris.

| Cleave Defect | Likely Cause | Corrective Action |
| --- | --- | --- |
| Angular cleave | Blade wear or fiber not seated | Rotate blade, recleave, verify clamp pressure |
| Hackle | Dirty fiber or abrupt stripping damage | Cut back to fresh coated section and re-strip |
| Lip | Improper tension setting | Check cleaver setup and operator technique |
| Shattered end | Fiber under side load | Stabilize fiber path and recleave |
| Short cleave length | Incorrect scale setting | Reset cleaver gauge before continuing |

## Fusion Splicing Procedure

1. Select the correct splicer profile: SM G.652/G.657 for OS2, MM 50/125 for OM3/OM4/OM5, or ribbon program as required.
2. Install the left and right fibers in holders with clean cleaved ends centered in the v-grooves or sheath clamps.
3. Close the wind protector and start the automated alignment sequence.
4. Review the camera image for dirt, severe cleave angle, or bubbles before accepting the arc.
5. Allow the splicer to perform pre-fuse, alignment, and main fusion arc; do not bump the table during the cycle.
6. Read the estimated splice loss. For internal acceptance, target less than 0.1 dB and resplice anything above the threshold unless engineering approves otherwise.
7. Perform a proof test if the splicer supports it and the cable design requires confirmation of tensile retention.
8. Transfer the completed splice carefully into the heat sleeve without bending the bare glass.

### Fusion Alignment Notes

- Use core-alignment on Fujikura 90S+ or TYPE-82C+ for feeder and backbone work where budgets are tight.
- Use clad-alignment or auto mode only when the cable design, fiber type, or field program explicitly allows it.
- For G.657 drop fiber, verify the program accounts for bend-insensitive fiber to avoid false high-loss estimates.
- If two successive splices fail with bubbles, replace electrodes or recalibrate arc before proceeding.
- If the estimated loss is low but the image shows offset, trust the image and resplice.

## Mechanical Splicing Procedure

1. Use mechanical splicing only where approved by the job plan, restoration plan, or supervisor direction.
2. Confirm the splice body matches fiber size and coating diameter; 3M Fibrlok II 2529 is commonly used for 250 µm field restoration.
3. Prepare both fibers with the strip-clean-cleave process described above.
4. If the splice element uses an index-matching gel, verify the gel is present and uncontaminated before insertion.
5. Insert the first fiber to the alignment stop, then insert the second fiber until visual confirmation or stop contact is achieved.
6. Actuate the splice body latch or crimp lever fully; partial closure is a frequent source of intermittent loss.
7. Check for visible gap under the viewer window if the model provides one.
8. Route the mechanical splice into the approved holder and avoid tight bends immediately on either side.

### Mechanical Splice Notes

- Mechanical splice acceptance is less than 0.5 dB estimated or measured loss for internal field handoff.
- Do not reuse a mechanical splice body after the latch has been set unless the manufacturer explicitly allows re-entry.
- Mechanical splices are more sensitive to temperature cycling; move permanent plant repairs to fusion at the first maintenance window.
- Label any mechanical restoration in the closure notes so the permanent repair crew can find it quickly.

## Splice Protection and Tray Management

1. Slide the heat sleeve so the bare glass is centered under the strength member rod.
2. Place the sleeve in the heater with the splice centered and the fiber fully supported.
3. Allow the full heat and cool cycle; do not remove the sleeve while still soft.
4. Route the protected splice into the tray with natural fiber lay, no crossovers over tray hinges, and no sharp turns at holder entry.
5. Maintain the tray fiber count and holder spacing shown on the closure drawing.

| Tray Check | Pass Condition |
| --- | --- |
| Sleeve position | Centered, fully recovered, no air bubbles |
| Fiber routing | No twist, no pinch, no lid interference |
| Slack storage | Even loops, no microbends at entry points |
| Tray fill | Within manufacturer limit |
| Closure sealing surfaces | Clean before lid installation |

## Quality Checks and Test Handoff

- Review every splice estimate before closing the tray; do not assume a later OTDR will sort it out.
- If the route is testable from both ends, compare splice events after completion to catch swapped fibers or hidden high-loss joints.
- Use bidirectional OTDR averaging for acceptance on long routes or whenever the two connected fibers have different backscatter coefficients.
- Inspect any connectorized jumpers used for test launch or restoration patching before power meter or OTDR work.
- Document abnormal but accepted conditions, such as temporary mechanical repair or unavailable opposite-end testing.

| Check Type | Method | Expected Result |
| --- | --- | --- |
| Splice estimate | Splicer screen | < 0.1 dB fusion, < 0.5 dB mechanical |
| Continuity | VFL or light source as applicable | Correct strand and polarity confirmed |
| Event verification | OTDR | Event distance matches tray/closure location |
| End-to-end loss | OLTS or power meter/light source | Within design budget |
| Photo evidence | Work order attachment | Tray map and closure label visible |

## Common Rework Triggers

- Estimated loss above threshold.
- Visible bubble, line, or shadow in fusion image.
- Cracked or partially recovered protection sleeve.
- Fiber snaps during tray placement.
- Unexpected OTDR reflectance or high event loss at closure.
- Tray lid pinches a fiber during close-out.
- Field notes do not match actual splice order.

## Documentation and Close-Out

1. Update the splice matrix with cable A, cable B, tray number, fiber colors, splice method, and pass/fail result.
2. Attach OTDR traces, loss results, tray photos, and any restoration notes to the work package.
3. Record equipment used when troubleshooting is likely later, especially splicer model and last arc calibration date.
4. Seal the closure, torque hardware per manufacturer guidance, and verify all external labels are legible.
5. Leave the site only after loose glass has been collected and the shard bottle is secured.

## Field QA Appendix

### Recommended Splicer Programs

| Fiber Type | Typical Program | Notes |
| --- | --- | --- |
| G.652.D / OS2 | SM Auto or SM Fast with core alignment | Default for feeder and distribution |
| G.657.A1 / A2 | Bend-insensitive SM profile | Verify arc offset guidance if vendor provides it |
| OM3 / OM4 / OM5 | MM 50/125 profile | Clean v-grooves before changing from single-mode work |
| Ribbon SM | Ribbon 12 or configured count | Check ribbon order before every mass fusion cycle |

### Splice Loss Troubleshooting Short List

- High loss plus visible bubble usually indicates contamination or incorrect arc conditions.
- High loss plus offset image usually indicates poor cleave, dirty clamp, or incorrect holder seating.
- Acceptable estimate but later OTDR issue often points to tray stress or fiber routing after the splice was made.
- Repeated failures on one side only often trace back to a worn stripper, dirty holder, or damaged coating near the work point.

### Daily Tool Readiness Check

- Confirm cleaver blade position and rotate if the counter or defect trend requires it.
- Verify splicer electrodes are clean and not near end of life.
- Check heater channels for residue from old sleeves.
- Confirm backup battery is charged before entering a remote site.
- Carry spare sleeves, alcohol, wipes, and a second shard bottle.

### Fiber Identification Reminder

| Position | Standard Color |
| --- | --- |
| 1 | Blue |
| 2 | Orange |
| 3 | Green |
| 4 | Brown |
| 5 | Slate |
| 6 | White |
| 7 | Red |
| 8 | Black |
| 9 | Yellow |
| 10 | Violet |
| 11 | Rose |
| 12 | Aqua |

### Supervisor Sign-Off Points

- Loss thresholds met and recorded.
- Temporary mechanical repairs flagged for follow-up.
- Closure labels installed and legible.
- Photos attached to the job package.
- Site left free of glass shards and consumable waste.
