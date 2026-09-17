# Safety Protocols

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## Field Safety Principles

- No production target overrides stop-work authority.
- Complete the job hazard analysis before unloading ladders, opening handholes, or exposing live fiber routes.
- Use the buddy system where confined spaces, traffic exposure, or aerial work is involved.
- Report near misses the same day so hazards can be corrected before the next crew arrives.
- Maintain housekeeping at the work area; loose fiber shards, wipes, and tie wrap tails are safety defects.

## Minimum PPE Requirements

| Task | Required PPE | Notes |
| --- | --- | --- |
| General field work | Safety glasses, gloves, high-visibility vest, safety boots | Upgrade to cut-resistant gloves when handling armor |
| Splicing trailer or van | Safety glasses and shard bottle | Bare glass handling requires eye protection at all times |
| Pole or aerial work | Hard hat with chin strap, fall arrest, gloves, boots | Use utility-approved climbing kit |
| Trenching and handhole work | Hard hat, gloves, vest, boots | Add hearing protection when using saws or vac systems |
| Solvent or epoxy use | Chemical-resistant gloves and eye protection | Follow SDS ventilation requirements |
| Near energized lines | Arc-rated PPE as required by utility/customer rules | Observe approach boundaries |

## Laser Safety

- Treat every fiber as potentially live until verified otherwise with approved test equipment.
- Never look into the end of a connector, bare fiber, coupler, splitter port, or transceiver.
- Use a power meter or fiber identifier to determine live status; do not rely on service outage reports alone.
- Class 1 products are considered safe during normal enclosed operation, but unsafe conditions can still exist if connectors are disconnected.
- Class 3R visible fault locators require controlled handling because direct eye exposure can cause injury.

| Laser Class | Common Field Example | Required Controls |
| --- | --- | --- |
| Class 1 | Installed PON/ethernet optics in enclosed system | Do not bypass covers or look into disconnected fibers |
| Class 3R | 1-5 mW red VFL | Do not stare into beam; prevent beam path toward others |
| Service test sets | OTDR or light source output | Use correct ports and caps; verify dark-fiber procedure |
| Unknown source | Unlabeled customer equipment | Treat as hazardous until measured |

### Laser Safety Checklist

- Cap unused ports immediately.
- Announce before energizing or tracing fibers with a VFL.
- Use APC adapters where specified; mismatched adapters can leak light and damage ferrules.
- Keep inspection scopes with integrated pass/fail safety features up to date.
- Post warning signs when working in shared telecom rooms.

## Working at Heights

1. Inspect ladders, hooks, harnesses, lanyards, bucket controls, and pole gear before use.
2. Verify the structure is safe to climb or access; do not climb compromised poles, rusted ladders, or unapproved mounts.
3. Use 100% tie-off whenever the fall plan requires it.
4. Secure tools and small hardware to prevent dropped-object hazards below.
5. Set exclusion zones beneath the work area and keep the public out of the drop zone.
6. Stop aerial work during lightning, high wind, icy surfaces, or poor visibility.

| Hazard | Control |
| --- | --- |
| Ladder slip | 4:1 angle, tied off, stable footing, spotter when needed |
| Dropped tools | Use tool lanyards and toe boards where possible |
| Overreach | Reposition ladder or bucket; keep belt buckle between rails |
| Weather | Suspend work when conditions exceed company or utility limits |
| Traffic strike risk | Use cones, signs, and approved traffic control plan |

## Trench, Handhole, and Underground Safety

- Call for utility locates before any dig, bore, pothole, or hand excavation.
- Use vacuum excavation or hand tools inside the tolerance zone around marked utilities.
- Inspect lids, frames, and vault walls before entry; damaged structures can fail under load.
- Test atmosphere in vaults, manholes, and other confined or poorly ventilated spaces before entry and as conditions change.
- Provide shoring, shielding, or sloping in trenches as required by depth, soil, and regulation.
- Keep spoil piles, equipment, and vehicles back from trench edges.

### Underground Work Rules

- Maintain egress ladders in trenches when required.
- Do not enter a trench with standing water unless the hazard has been evaluated and controlled.
- Treat all unidentified conduits as live until proven otherwise.
- Use gas monitoring in enclosed splice pits or utility vaults.
- Never work alone in a permit-required confined space.

## Chemical Safety

- Review SDS information for epoxies, cleaning solvents, cable flooding compounds, and battery chemicals before field use.
- Use only approved solvents such as high-purity IPA in the quantities required for the task.
- Do not use open solvent containers inside poorly ventilated vehicles or vaults.
- Avoid skin contact with epoxy and anaerobic sealants; sensitization can develop over repeated exposure.
- Dispose of wipes, empty solvent containers, and contaminated absorbents per local environmental rules.

| Material | Primary Risk | Control |
| --- | --- | --- |
| 99% isopropyl alcohol | Flammable, eye irritation | Use away from ignition sources and close cap after each use |
| Fiber optic epoxy | Skin and respiratory sensitizer | Use gloves and follow cure instructions |
| Cable gel/flooding compound | Slip hazard and skin contact | Wipe immediately and bag waste |
| Adhesive promoter/primer | Flammable vapor | Use with ventilation and sealed storage |

## Electrical Safety Near Power Lines

- Maintain minimum approach distances required by the serving utility and applicable regulation; if no specific rule is provided, use at least 10 ft for lines up to 50 kV and increase from there.
- Assume messenger wires, guy wires, and adjacent metallic structures can become energized.
- Use non-conductive ladders and fiberglass tools where required.
- Do not lash, cut, or move telecom plant that has sagged into the electrical space without utility coordination.
- Stop work immediately if a cable, pole, or cabinet shows evidence of electrical damage, arcing, or stray voltage.

### Cabinet and Power Room Safety

- De-energize circuits before replacing power supplies unless live work is explicitly authorized and controlled.
- Use insulated tools around DC distribution panels.
- Remove metal jewelry when working around batteries or energized buswork.
- Respect battery short-circuit hazards in cabinets with UPS or backup power.

## Vehicle, Traffic, and Site Control

- Park to protect the crew without blocking emergency access or creating blind spots for motorists.
- Deploy cones, signs, and arrow boards per the approved traffic control plan.
- Use spotters when backing near trenches, cabinets, or pedestrians.
- Secure trailers, generators, and ladders against roll or shift on sloped terrain.
- Keep ignition keys controlled when a vehicle is used as a barrier vehicle.

## Fiber Scrap and Housekeeping

1. Collect all glass shards in a labeled shard bottle or approved tape pad immediately after each cleave.
2. Do not place bare scraps in pockets, cups, worktops, or floor mats.
3. Seal and dispose of shard containers according to local policy when full.
4. Vacuum or wipe the work area before leaving the site, especially in customer premises.
5. Inspect gloves and sleeves for embedded glass if multiple breaks occurred during the job.

## Emergency Response

- For eye exposure to laser light or embedded glass, stop work and seek immediate medical evaluation.
- For solvent splash, follow SDS first-aid steps and flush as directed.
- For electrical contact, do not touch the victim until the source is isolated; call emergency services immediately.
- For trench collapse, activate emergency response, do not perform an unplanned rescue, and secure the area.
- For falls from height, keep the scene stable, preserve equipment for investigation, and notify supervision immediately.

### Stop-Work Triggers

- Unidentified live fiber or electrical hazard.
- Missing PPE or failed fall protection inspection.
- Unstable trench, vault, ladder, pole, or aerial support condition.
- No utility locate or route verification before excavation.
- Weather or traffic conditions outside the approved work plan.
- Crew fatigue or impairment affecting safe execution.

## Daily Supervisor Review Points

| Review Item | Expectation |
| --- | --- |
| JHA complete | Signed before work starts |
| PPE verified | Crew meets task-specific requirements |
| Rescue plan | Available for aerial/confined work |
| Traffic plan | Devices deployed and maintained |
| Housekeeping | No exposed shards or waste at close-out |
| Incident reporting | Near misses and injuries reported same day |

## Field Execution Appendix

### Weather Hold Triggers

| Condition | Minimum Response |
| --- | --- |
| Lightning in the area | Suspend aerial and exposed outside work |
| High wind affecting ladder or bucket stability | Stand down until limits are back inside plan |
| Heavy rain with open closures | Move to tent, trailer, or delay work |
| Ice on poles, lids, or ladders | Do not climb or access until controlled |
| Extreme heat | Increase hydration/rest cycles and monitor crew condition |
| Extreme cold reducing dexterity | Slow work pace and warm hands before bare-fiber handling |

### Confined Space Red Flags

- Unknown atmosphere history.
- Water intrusion or sewage odor.
- Damaged ladder rungs or vault structure.
- Inadequate rescue plan or no attendant.
- Gas monitor not available or out of date.
- Uncontrolled traffic or public access above the entry point.

### Chemical and Spill Response Reminders

- Keep absorbent pads in the vehicle or splice trailer.
- Bag contaminated wipes separately from standard trash when required by local policy.
- Never pour solvents into storm drains or onto soil.
- Close all chemical containers before moving the vehicle between sites.
- Wash exposed skin promptly after epoxy or gel contact.
- Report spills immediately if quantity or location triggers environmental notification rules.

### Near-Power Quick Rules

- Treat sagging communications plant near power as energized until cleared.
- Keep ladders and lift booms outside minimum approach boundaries.
- Use a utility spotter when required by the serving power company.
- Stop if wind or span motion could swing work into the electrical space.

### End-of-Day Safety Review

- All fiber shards accounted for and secured.
- PPE inspected and replaced if damaged.
- Incident and near-miss reporting completed.
- Traffic control devices collected without entering live lanes unsafely.
- Vehicles and trailers restocked for the next shift.
- Site left without open vaults, loose lids, or unsecured ladders.
