# ElevenLabs roof prompts — Levee / Near South

Saved for later dress onto building cube tops (`Row_*_Mass` +Z).
Match façade style: grey studio background, orthographic, 1930s Chicago grit.

## Shared prefix

Paste in front of each landmark prompt:

```
1930s Chicago Near South industrial city, photoreal game building roof asset, orthographic top-down roof plan, centered, isolated on solid neutral grey background, no ground, no people, no cars, weathered gritty PBR detail, soot stains, tar patches, rusty vents, period-accurate, high resolution, flat even studio lighting, no text overlays, no watermarks
```

## Landmark roofs

### Pell’s Garage
```
[PREFIX] flat tar-and-gravel garage roof, low brick parapet with stepped corners, one brick chimney, rusty gooseneck vent pipes, faded painted roof hatch, oil stains near hatch, small water tank silhouette optional, square footprint
```

### Corvo Cafe
```
[PREFIX] two-story shop roof, weathered green copper cornice edge visible from above, flat tar roof behind cornice, two small chimneys, skylight hatch, laundry lines or vent caps, cream brick parapet rim, square footprint
```

### Dock / Freight warehouse
```
[PREFIX] long industrial warehouse roof, rusted corrugated metal sheets, sawtooth monitor sections OR simple gable ridge, three circular vent pipes on ridge, tar seams, water stains, wooden hoist beam end barely visible, rectangular footprint longer than wide
```

### Rope / Pier warehouse
```
[PREFIX] pier warehouse roof, heavily rusted corrugated metal, three round ridge vents, timber gable ends, rope coils and crate shadows optional at edges, weathered wood trim, rectangular footprint
```

### Bar / tavern
```
[PREFIX] single-story tavern flat roof, oxidized green copper parapet with dentil edge, dark tar center, one chimney, rusty vent stack, moss in corners, square footprint
```

### Board / ROOMS boarding house
```
[PREFIX] four-story tenement mansard roof from above, dark grey slate shingles, two dormer roofs, ornate stone cornice rim, chimney pots, weathered green copper accents, rectangular footprint
```

### Street tenement (Facade A–G)
```
[PREFIX] classic Chicago tenement flat roof, heavy green-patina copper cornice ring, black tar roof deck, water tank on steel stilts, chimney cluster, fire-escape top landing hint at one edge, rectangular footprint
```

## Multi-view roof sheet

Best if you want cornice sides + top together:

```
3D game building roof reference sheet on solid grey background, three labeled views: TOP ORTHOGRAPHIC roof plan, FRONT ELEVATION cornice/parapet only, THREE-QUARTER view of roof meeting upper facade. 1930s Chicago brick building, weathered copper cornice, tar roof, vents, chimneys, photoreal, no people, no ground plane beyond the building
```

## Import notes

- Prefer **top-down orthographic** for the plate mapped on the cube +Z face.
- Keep **square or clearly rectangular** footprints to limit UV stretch.
- Same grit language as façades: soot, rust, tar patches, copper patina.
- Generate landmark roofs first (Garage, Cafe, Dock, Board), then reuse the tenement roof across Mid A–G with slight variation.
- Drop finished JPGs next to façade assets; wire via `Scripts/FixBuildingFacades.py` (or a roof dress pass) onto building tops.
