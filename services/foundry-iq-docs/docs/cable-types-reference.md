# Cable Types Reference

- Last Updated: 2026-05-22
- Document Owner: Field Operations Engineering
- Classification: Internal Operations Reference

## How to Use This Reference

- Use this document when selecting repair materials, validating as-built records, or confirming whether a cable type is appropriate for the route environment.
- Always follow the manufacturer data sheet for the exact cable installed; this guide provides field reference values, not design release authority.
- When the print and the jacket marking disagree, escalate before splicing or testing.

## Quick Comparison Table

| Type | Core/Cladding | Typical Reach | Common Use |
| --- | --- | --- | --- |
| OS2 single-mode | 9/125 µm | 10 km to 80+ km depending on optics | OSP backbone, PON, metro |
| OM1 multimode | 62.5/125 µm | 1 Gb to 275 m, 10 Gb to 33 m | Legacy building backbone |
| OM2 multimode | 50/125 µm | 1 Gb to 550 m, 10 Gb to 82 m | Older campus links |
| OM3 multimode | 50/125 µm | 10 Gb to 300 m, 40/100 Gb to 100 m | Modern LAN backbone |
| OM4 multimode | 50/125 µm | 10 Gb to 550 m, 40/100 Gb to 150 m | High-density data centers |
| OM5 multimode | 50/125 µm | SWDM support, similar base reach to OM4 | Newer shortwave multiplexing deployments |

## Single-Mode Fiber Reference

| Standard | Core/Cladding | Key Attribute | Typical Application |
| --- | --- | --- | --- |
| ITU-T G.652.D / OS2 | 9/125 µm | Low water peak, standard long-haul SMF | Feeder, distribution, backbone |
| ITU-T G.657.A1 | 9/125 µm | Improved bend performance, G.652-compatible | FTTx drops and inside plant transitions |
| ITU-T G.657.A2 | 9/125 µm | Higher bend tolerance | Tight routing in MDU or cabinet work |
| ITU-T G.657.B3 | 9/125 µm | Very high bend tolerance, less universal splicing preference | Specialty compact routing only |

- OS2 is the standard field default for outside plant and PON environments.
- Use low-bend variants for customer drops, indoor cabinets, and restoration paths with tight radius constraints.
- Mixing G.652 and G.657 is usually splice-compatible, but verify program and routing because bend-insensitive fibers can mask poor workmanship.

## Multimode Fiber Reference

| Grade | Core/Cladding | Laser Optimized | Notes |
| --- | --- | --- | --- |
| OM1 | 62.5/125 µm | No | Legacy orange jacket, avoid for new builds |
| OM2 | 50/125 µm | No | Older orange jacket, limited 10G reach |
| OM3 | 50/125 µm | Yes | Typically aqua, common enterprise backbone |
| OM4 | 50/125 µm | Yes | Aqua or violet, preferred for modern data halls |
| OM5 | 50/125 µm | Yes + wideband | Lime green, supports SWDM channels |

- Do not splice or patch OM1 62.5 µm fibers into 50 µm multimode without engineering approval.
- Multimode is typically confined to short campus, building, and data center applications rather than OSP access networks.
- Document multimode polarity carefully; many complaints on short links are polarity or cassette issues rather than fiber faults.

## Cable Construction Types

| Construction | Environment | Typical Features | Field Notes |
| --- | --- | --- | --- |
| Indoor riser | Inside buildings | Flame-rated jacket, aramid strength | Do not direct-bury or expose to standing water |
| Indoor plenum | Air handling spaces | Low smoke jacket | Required in plenum spaces |
| Outdoor loose tube | OSP ducts and aerial | Gel or dry water block, buffer tubes | Preferred for feeder/distribution |
| Indoor/Outdoor | Building entry + short OSP exposure | Dual-rated jacket | Useful for demarc transitions |
| Armored | Rodent or crush risk | Interlocking or corrugated armor | Bond/ground metallic armor when required |
| Aerial ADSS | Pole line, all-dielectric | No metallic messenger, track-resistant jacket | Observe span and hardware limits |
| Figure-8 aerial | Pole line with messenger | Integrated steel messenger | Messenger handling and bonding required |
| Direct-buried | Buried OSP | Heavy jacket, armor or strength package | Use only where print and utility policy allow |
| Ribbon cable | High-count backbone | Mass-fusion friendly ribbon units | Strict ribbon management required |
| Micro cable | Microduct systems | Small OD, blown-fiber compatible | Observe pressure and bend specs |

## Indoor vs Outdoor Selection Notes

- Outdoor cable typically carries water-blocking elements and wider operating temperature ratings.
- Indoor cable emphasizes flame performance and flexibility but usually has lower crush and moisture tolerance.
- Dual-rated indoor/outdoor cable simplifies building entrance transitions but still must meet local fire code in occupied spaces.
- Never leave standard indoor riser cable exposed on rooftops or in conduit runs that flood.

## Armored Cable Notes

- Use armored construction in rodent-prone duct banks, industrial plants, direct-buried segments, and harsh customer sites.
- Interlocking armor is common for indoor/outdoor premises cable; corrugated steel armor is common in OSP designs.
- Cut armor with approved tools only; uncontrolled cutting can nick tubes or fibers.
- Verify grounding and bonding requirements whenever metallic armor or messenger is present.

| Armored Option | Benefit | Trade-Off |
| --- | --- | --- |
| Interlocking armor | Flexibility and mechanical protection | Larger OD than non-armored |
| Corrugated steel armor | High crush and rodent resistance | Heavier and less flexible |
| Dielectric armor yarns | No bonding needed | Lower crush protection than steel |

## Aerial Cable Notes

- ADSS cable is preferred where electrical isolation from power distribution is needed.
- Figure-8 cable includes an integral messenger and is common on communications-only plant.
- Match cable to span length, wind/ice loading zone, and hardware rating.
- Observe sag, tension, and minimum bend limits during mid-span access and lash operations.

## Direct-Buried Cable Notes

- Direct-buried cable is designed for soil contact but still requires depth, marker, and route protection per local standards.
- Use caution around rocky soil and utility crossings; damage is often external compression rather than optical fatigue.
- In restoration work, document any exposed armor breaches or jacket cuts even if fibers still test clean.

## Ribbon Cable Notes

- Ribbon cable allows 4, 8, or 12-fiber mass fusion and speeds high-count backbone work.
- Fiber order control is critical; a ribbon roll or twist can create multiple customer impacts at once.
- Use ribbon-capable strippers, holders, and protectors; do not improvise with single-fiber tools on a major build.

| Ribbon Format | Typical Use | Common Equipment |
| --- | --- | --- |
| 12-fiber ribbon | Long-haul and metro backbone | Fujikura 70R+, AFL 12-fiber trays |
| Rollable ribbon | High-count compact cable | Mass-fusion plus fan-out kits |
| SpiderWeb ribbon | Reduced cable diameter designs | Verify tray and holder compatibility |

## Typical Applications by Cable Type

| Application | Recommended Type | Why |
| --- | --- | --- |
| GPON feeder | OS2 loose tube | Low attenuation over long outside plant distances |
| XGS-PON drop to MDU | OS2 G.657.A2 drop cable | Tolerates tighter routing near customers |
| Data center leaf-spine | OM4 or OS2 depending optics strategy | Short reach high density or longer future-proof runs |
| Industrial plant floor | Armored indoor/outdoor OS2 | Crush and chemical exposure resistance |
| Campus conduit backbone | OS2 loose tube or armored as risk dictates | Balances reach and outdoor durability |
| High-count hub route | OS2 ribbon cable | Efficient splicing and count density |

## Jacket Marking and Color Cues

- Yellow is typically single-mode OS2.
- Orange is typically OM1 or OM2 legacy multimode.
- Aqua is typically OM3 or OM4.
- Lime green is typically OM5.
- Black jackets are common for outdoor cable regardless of fiber type, so always read the print line on the jacket.

## Field Verification Checklist

1. Read the jacket print for fiber count, fiber type, flame rating, and manufacturer part number.
2. Verify the cable construction matches the environment: duct, aerial, direct-buried, indoor, or indoor/outdoor.
3. Confirm the intended splice hardware, closures, and strain-relief parts support the actual cable OD and strength members.
4. Check if the route requires bend-insensitive drop cable at cabinets or customer turns.
5. Log discrepancies between prints and field conditions before cutting.

## Common Manufacturer Examples

| Manufacturer Example | Category | Reference Use |
| --- | --- | --- |
| Corning ALTOS | Outdoor loose tube OS2 | Feeder/distribution |
| CommScope LazrSPEED 550 | OM4 multimode | Campus/data center |
| Prysmian FlexRibbon | High-count ribbon OS2 | Backbone |
| AFL EZ-Bend | Bend-insensitive drop fiber | MDU/customer routing |
| Superior Essex Premises cables | Indoor riser/plenum | Building backbone |

## Selection Appendix

### Fast Selection Guide

| Need | Preferred Choice | Why |
| --- | --- | --- |
| Long OSP access route | OS2 loose tube | Lowest attenuation and standard PON compatibility |
| Tight customer routing | G.657.A2 drop cable | Better bend tolerance |
| High-count backbone | Ribbon OS2 | Faster mass fusion and lower cable diameter |
| Rodent/crush exposure | Armored cable | Better mechanical protection |
| Short enterprise backbone | OM4 or OS2 | Depends on optics roadmap and reach |
| Building entry transition | Indoor/outdoor dual-rated cable | Avoids unnecessary splice or transition hardware |

### Compatibility Notes

| Mixed Condition | Risk | Field Guidance |
| --- | --- | --- |
| OM1 to OM3/OM4 path | Launch mismatch and loss | Escalate before permanent tie-in |
| G.652 to G.657 | Usually acceptable but backscatter can differ | Use correct splice program and verify routing |
| Indoor cable in wet OSP route | Moisture failure | Replace with outdoor-rated cable |
| Non-armored cable in rodent zone | Recurrent damage | Upgrade when restoring permanently |
| Figure-8 hardware on ADSS | Structural mismatch | Use hardware approved for cable design |

### Field Red Flags

- Jacket marking missing or unreadable on a cable about to be cut.
- Indoor-only cable found in a wet or direct-buried route.
- Mixed 62.5 µm and 50 µm multimode components in one path.
- Drop cable routed where messenger or armor was actually required.
- Ribbon count on print does not match actual cable build.
- Cable OD does not fit the closure kit already staged for the job.

### Receiving and Storage Checks

- Verify reel tag part number against the work package before unloading.
- Inspect for crushed flanges, broken lagging, or exposed cable layers.
- Keep cable ends sealed until installation starts.
- Store reels to prevent standing water contact and uncontrolled rolling.
- Record any shipping damage before accepting the reel into field stock.

### Common Verification Questions

- Does the cable OD match the closure or gland kit on site?
- Does the route environment require metallic bonding or dielectric isolation?
- Is the cable flame rating acceptable for the building space entered?
- Is the fiber type consistent with existing patch cords and optics?
- Does the selected repair section preserve count and bend performance?
- Does the route require low-smoke or plenum handling after building entry?

### Legacy Plant Notes

- OM1 and OM2 are still encountered in older campus and building backbones.
- Older loose-tube cable may use gel filling that requires additional cleanup time.
- Legacy aerial spans may mix figure-8 and lashed ADSS segments on the same serving route.
- Spare fiber records in older plant are often less reliable than jacket count and continuity checks.
- Older direct-buried routes may have undocumented repair sections using different armor packages.
