# Vendored, pinned assets for the static public site

| file | source | version | sha256 |
|---|---|---|---|
| globe.gl.min.js | https://unpkg.com/globe.gl@2.46.2/dist/globe.gl.min.js | globe.gl 2.46.2 (MIT) | 2c3e445c04d121215910a89688b96091c8a72071c122a4f830081a39b636c94c |
| earth-night.jpg | https://unpkg.com/three-globe@2.45.6/example/img/earth-night.jpg | three-globe 2.45.6 example (NASA Black Marble imagery) | 355ab23dd1323315b393d7b91dd2d7ee223a1cbaaba2b48dc72ba90d371ced24 |

`scripts/build_live_site.py` refuses to build if these hashes change. The local
dashboard (uvicorn) still loads globe.gl from unpkg; only the public static build uses these.
