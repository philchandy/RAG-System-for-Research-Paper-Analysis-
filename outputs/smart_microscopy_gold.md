# An Optogenetic Smart Microscopy Platform Reveals Signaling Dynamics-Dependent Control over Collective Cell Migration

## problem
- All-optical experiments that combine biosensor measurement with optogenetic stimulation are usually designed and implemented manually. A predetermined static stimulus pattern is applied and data is processed offline, making adaptive, closed-loop, or scaled multi-cell experiments difficult to implement.
- Existing smart microscopy systems for real-time imaging and stimulation are powerful but require considerable end-user programming, especially when different customized experiments must run in parallel across many fields of view.
- It is unclear how the spatiotemporal dynamics, such as speed, of receptor tyrosine kinase (RTK) signaling waves organize collective epithelial tissue migration, despite RTK activity waves being observed in vivo during processes like zebrafish scale regeneration and mouse wound healing.

## method
- The authors developed PyCLM (Closed-Loop Microscopy in Python), which combines MicroManager for fluorescent image acquisition and hardware/optogenetic control, Cellpose for real-time cell and embryo segmentation, and control of a digital micromirror device for optogenetic stimulation.
- The software architecture uses a master scheduler that coordinates five independently threaded module classes (microscope manager, microscope outbox, segmentation module, pattern module, pattern manager), enabling closed-loop feedback between measurement and stimulation without end-user programming. Experiments are configured using readable TOML files and a position list rather than by writing code.
- PyCLM was applied to three demonstration use cases: (1) bang-bang feedback control of TagRFP-H2B nuclear fluorescence across around 1,000 single MCF10A cells; (2) segmentation-based, scale- and rotation-corrected delivery of anterior-posterior optogenetic patterns to randomly oriented OptoSOS Drosophila embryos; and (3) subcellular ("vortex") versus supracellular (rotating-bar) OptoEGFR stimulation of MDCK epithelial monolayers to compare resulting tissue migration, plus a traveling-wave-speed replication of the migration-direction effect in MCF10A monolayers.
- Tissue and cell movement were quantified using segmentation-based tracking, including coefficient of variation of fluorescence, tangential/mean cell velocities, and velocity/cell-area analyses referenced to the phase of the traveling light wave at each cell's position.

## dataset
- MCF10A human mammary epithelial cells expressing a TagRFP-H2B nuclear marker (n = 1,127 cells) used for the single-cell feedback-control experiments.
- MDCK (Madin-Darby canine kidney) and MCF10A epithelial cell lines engineered to express FusionRed-tagged OptoEGFR, used for the tissue-migration/wave experiments.
- OptoSOS-expressing Drosophila melanogaster embryos, used for the developmental-patterning stimulation experiments.
- Time-lapse fluorescence microscopy image series and segmentation-derived cell tracks collected via PyCLM, including replicate tissue experiments (n = 4 vortex and n = 3 rotating-bar tissue replicates; n = 3 biological replicates each for 15 µm/h and 60 µm/h wave-speed conditions; n = 81 and n = 118 individually tracked cells for the slow- and fast-wave conditions, respectively).

## results
- Local feedback control reduced cell-to-cell fluorescence variability (CV) three-fold within 20 minutes and drove ~1,000 MCF10A cells to a uniform or spatially patterned fluorescence set point, whereas uniform global illumination increased brightness without reducing variability.
- Adaptive, segmentation-guided pattern delivery successfully applied correctly scaled and rotated anterior-posterior light patterns to multiple randomly oriented Drosophila embryos within a single experiment, producing the expected developmental perturbations (local membrane recruitment and gastrulation-associated tissue movement).
- Subcellular ("vortex") optogenetic stimulation of MDCK OptoEGFR tissue produced faster, uniformly counterclockwise rotational flow (~30 µm/h) than supracellular rotating-bar stimulation (~5 µm/h), which produced counterclockwise flow near the pattern center but reversed to clockwise flow beyond ~200 µm from center.
- Traveling light waves of EGFR activity produced tissue migration whose direction depended on wave speed: slow (15 µm/h) waves drove tissue movement that tracked the outgoing wave at a fairly constant rate, while fast (60 µm/h) waves drove faster overall tissue speed (6.06 ± 1.95 vs. 3.40 ± 1.82 µm/h; p = 0.046, paired t test) via brief "ratcheting" bursts of movement toward each incoming wave, with opposing cell-shape (area) dynamics between the two regimes — matching the directional difference observed in vivo between zebrafish scale regeneration (slow FGFR waves, movement away from source) and mouse epidermal wound healing (fast EGFR waves, movement toward source).
- The wave-speed dependence of migration direction was partially reproduced in a second cell line (MCF10A): slow waves again drove directed migration, but fast waves produced oscillatory, non-directional movement rather than a net reversal, indicating the response is cellular-context dependent.

## limitations
- The current PyCLM implementation does not track or store individual single-cell identity/behavior over time, limiting analyses that require per-cell history, such as identifying persistently fast versus slow migrators or implementing integral feedback controllers.
- PyCLM currently supports only a single light source per experiment; more complex multi-input, multi-output optogenetic control has not yet been implemented.
- The mechanistic basis for why fast RTK activity waves reverse tissue migration direction in some cellular contexts (MDCK) but instead produce only symmetric, non-directional oscillatory movement in others (MCF10A) remains unresolved.

## follow_up_questions

Answerable from the paper:
- Q: What software does PyCLM use for real-time cell segmentation?
  A: Cellpose.
- Q: How many independently threaded module classes does PyCLM's master scheduler coordinate?
  A: Five (microscope manager, microscope outbox, segmentation module, pattern module, pattern manager).
- Q: How many MCF10A cells were used in the single-cell feedback control experiment, and what marker did they express?
  A: 1,127 cells expressing a TagRFP-H2B nuclear marker.
- Q: How much faster was tissue migration under fast (60 µm/h) versus slow (15 µm/h) EGFR waves in MDCK cells?
  A: 6.06 ± 1.95 µm/h vs 3.40 ± 1.82 µm/h (p = 0.046, paired t test).
- Q: What file format is used to configure PyCLM experiments?
  A: TOML files, together with a position list.
- Q: Is PyCLM's code publicly available, and where can it be found?
  A: Yes — the code has been deposited at https://github.com/Harrison-Oatman/PyCLM and is publicly available as of the date of publication, with an archived copy referenced via a Zenodo DOI in the Key Resources Table.

Not answered in the paper:
- Q: Has PyCLM been tested on human tumor organoids?
  A: Not mentioned — the demonstrated systems are MCF10A and MDCK cell lines and Drosophila embryos.
- Q: Under what specific software license (e.g., MIT, GPL, BSD) is PyCLM released?
  A: Not specified — the paper states the code is publicly available on GitHub and archived via Zenodo, but never names a specific software license.
- Q: Does PyCLM support multi-photon excitation microscopy?
  A: Not discussed in the paper.
