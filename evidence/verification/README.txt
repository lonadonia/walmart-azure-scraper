RELEASE 1.5.2's record (publication c4e665c, 2026-11-03), unchanged below this paragraph. The records of
this delivery are in 1.6.5/ (and 1.6.1/, 1.6.4/ for the earlier last-good checks).

The raw record of the clean-extraction verification of this delivery:
  logs/<step>.log        each step's full output (logs/attempts/: earlier attempts of a step, kept)
  junit/<group>/*.xml    the JUnit XML of every test step (attempts/: earlier ones)
  steps.jsonl            one line per step attempt: command, folder, start and end (UTC), exit code
  DATA_CHECKS.txt        the checks of the data step
  delivery_scripts/      the verifier that ran (verify_walmart_152_delivery.py), the modules it imports and
                         the delivery builder, as they were when this record was collected (SHA-256):
  4b3c93e68802adcda5309ba4b8b550cdc07dd58abc915d45ce25c132680bff64  delivery_scripts/verify_walmart_152_delivery.py
  4a6e6309b674e0cbdc606ded1d8ab08834a97bf2953732b28e490938b9183baf  delivery_scripts/verify_walmart_151_delivery.py
  6f228b4c04c3c1b581df227de18e51e8a35c5b45e26ad863ecd9f463c099c921  delivery_scripts/verify_walmart_141_delivery.py
  12e0478c9ec56dac1804fa9e4d921c2d5c0a080b1f0649a478f5fae58a0b370d  delivery_scripts/verify_walmart_131_delivery.py
  59780e4bd4f622c8c9e3e0a11c1ed9a991419053f342c92af9103da9211a1cff  delivery_scripts/verify_walmart_130_delivery.py
  97031c5a528a7a5d10b0c7da804470e577fce77cf4ca1f42caf08f026339a3b6  delivery_scripts/verify_walmart_delivery.py
  e765a8d3c7b42fd9ba5fb7b8f909eb40c44c2c86b59a9d6e3bc377976d8b52ee  delivery_scripts/verify_headless_delivery.py
  987f9882d505c48bf480c5c78064b546fae344fd92051ed6acbfba5e2d0775d9  delivery_scripts/verify_steps.py
  995c818e999260f5a9467f1d3c4cee164e7014cf240c4ca8619dee49c95221cc  delivery_scripts/build_walmart_152_delivery.py
  e2ed440ef33f1c461ab8469ba60f4114f74d75206efb4fc49709d21ad622d44f  delivery_scripts/build_walmart_151_delivery.py
  04236317bc167069f38d2a75ec24ca925326e874512a9899413a6377f4c0b4d0  delivery_scripts/build_walmart_141_delivery.py
PACKAGE_VERIFICATION.txt, at the top of the delivery, is composed from them; ACCEPTANCE_RUNBOOK.md says
how to run the verifier again.
When collected, the workstation's host name was replaced with <workstation> (JUnit XML: hostname="(workstation)"):
  files changed: {'junit': 44}
