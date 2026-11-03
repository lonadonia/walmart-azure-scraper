OWNER AZURE TEST: the recorded walkthrough of release 1.5.2 (627c804), on Hamza's Azure test VM, 2026-11-01T21:19:22Z to
21:22:52Z. Offline: no provider, retailer or Classic request. Not the client's environment.

  WALKTHROUGH_1.5.2.cast  the recording (asciinema, 120 x 36). SHA-256 07bfb30c57c00b7f798428e4b7e6df9eab2643cf205c0e27b48687e0047d2fab
  walkthrough.sh          the script it recorded. Every command shown ran as shown; the lines starting with # are the narration
  render_cast.py          draws the recording frame by frame and encodes it with ffmpeg: WALKTHROUGH_1.5.2.mp4 in the delivery
                          folder, 8 frames a second, 170.1 s, no audio, pauses longer than 2 s shortened to 2 s.
                          SHA-256 92d6b2fd639170b72f297c51ac841e15f9daaf34138618b5b0d9e01d32d7b0d7
  rec.log, render.log     the exit codes of the recording and of the render (0 and 0)

The kill and resume in it ran on a fresh copy of the campaign database (walmart_walk), dropped at the end of the recording.
The Classic probe ZIP hash it shows (20de284c...) is the ZIP tested on the VM. The delivered ZIP was rebuilt on 2026-11-02 to
replace the workstation's name in one recorded file: ../owner_vm/PROBE_ZIP_TESTED_VS_DELIVERED.json.

Earlier takes, not used: the first stopped when its replay was refused (a run already replayed is not replayed again);
the second said "after 6 pages" where the count shown was 7; the third showed "exit 0" for the refused validate-config,
because the script read the exit code after an echo. This take fixes all three. The second and third are kept on the VM.
